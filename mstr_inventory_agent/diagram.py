"""Visual schema output: Mermaid ER diagrams and a dimension bus-matrix image."""

import os
import re
from typing import List, Optional

import pandas as pd


def write_mermaid(path: str, edges: pd.DataFrame, star: pd.DataFrame) -> Optional[str]:
    """Write one Mermaid ER diagram per fact table, plus an overview of conformed dimensions.

    Mermaid renders directly in Cursor, GitHub and most markdown viewers, and stays diffable in
    version control, which a binary image does not.
    """
    if edges.empty:
        return None
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    dim_use = edges.groupby("Dimension Table")["Fact Table"].nunique()
    conformed = sorted(dim_use[dim_use > 1].index)

    lines: List[str] = [
        "# US Ad Sales — Logical Star Schema",
        "",
        "Inferred from MicroStrategy table naming and the validated fact/dimension analysis.",
        "The exports contain no columns, keys or join expressions, so these diagrams show table",
        "relationships only — not a physical schema.",
        "",
        "## Conformed dimensions",
        "",
        f"{len(conformed)} dimensions are shared by more than one fact and form the reusable core "
        "of the model:",
        "",
    ]
    for d in conformed:
        lines.append(f"- `{d}` — used by {int(dim_use[d])} facts")

    lines += ["", "## Star schema by fact table", ""]

    for rec in star.to_dict("records"):
        fact = rec["Fact Table"]
        dims = [d.strip() for d in str(rec["Dimension Tables"]).split(",") if d.strip()]
        lines += [
            f"### {fact}",
            "",
            f"*{rec['Business Area']}* — {rec['Dimensions']} dimensions "
            f"({rec['Conformed Dimensions']} conformed, {rec['Private Dimensions']} private). "
            f"Confidence: {rec['Confidence']}.",
            "",
        ]
        if rec.get("Key Grain / Notes"):
            lines += [f"Grain: {rec['Key Grain / Notes']}", ""]
        lines += ["```mermaid", "erDiagram"]
        for d in dims:
            tag = "conformed" if d in conformed else "private"
            lines.append(f"    {_safe(fact)} }}o--|| {_safe(d)} : \"{tag}\"")
        lines += ["```", ""]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_bus_matrix_image(path: str, edges: pd.DataFrame) -> Optional[str]:
    """Render the classic data-warehouse bus matrix (facts x conformed dimensions)."""
    if edges.empty:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        return None

    grid = pd.crosstab(edges["Dimension Table"], edges["Fact Table"])
    grid = grid.reindex(
        grid.sum(axis=1).sort_values(ascending=False).index
    )[grid.sum(axis=0).sort_values(ascending=False).index]

    shared = grid.sum(axis=1)
    values = grid.copy()
    for dim in values.index:
        values.loc[dim] = grid.loc[dim] * (2 if shared[dim] > 1 else 1)

    height = max(6.0, 0.22 * len(grid.index) + 2.0)
    width = max(8.0, 0.9 * len(grid.columns) + 5.0)
    fig, ax = plt.subplots(figsize=(width, height))

    cmap = matplotlib.colors.ListedColormap(["#F5F5F5", "#9DB8D8", "#1F3864"])
    ax.imshow(values.values, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels(grid.columns, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(grid.index)))
    ax.set_yticklabels(grid.index, fontsize=7)
    ax.set_xticks([x - 0.5 for x in range(1, len(grid.columns))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(grid.index))], minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8)
    ax.tick_params(which="minor", length=0)

    ax.set_title(
        "US Ad Sales warehouse — dimension bus matrix\n"
        f"{len(grid.index)} dimensions x {len(grid.columns)} facts, "
        f"{int(grid.values.sum())} mapped joins",
        fontsize=13, pad=16,
    )
    ax.legend(
        handles=[Patch(facecolor="#1F3864", label="Conformed dimension (used by >1 fact)"),
                 Patch(facecolor="#9DB8D8", label="Private dimension (single fact)")],
        loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=9,
    )

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(name))
