"""Orchestration: collect, classify, analyse, render, publish.

One weekly run is a straight line through these five steps. The only branching
is at collection, where a live Glue run that cannot reach an account falls back
to the last published markdown rather than failing — a stale page with a
visible "generated from snapshot" banner is more useful on a Monday morning
than no page at all.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import adoption, classify, registry
from .config import Config
from .model import Catalog
from .render import confluence as render_confluence
from .render import markdown as render_markdown
from .render import tabular as render_tabular
from .sources import snapshot as snapshot_source

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    catalog: Catalog
    report: adoption.AdoptionReport
    outputs: dict
    published_url: Optional[str] = None


def run(
    config: Config,
    *,
    source: str = "auto",
    snapshot_path: Optional[Path] = None,
    publish: bool = False,
    dry_run: bool = False,
    tabular_out: Optional[Path] = None,
) -> RunResult:
    catalog = _collect(config, source=source, snapshot_path=snapshot_path)

    catalog.products = (
        registry.load_products(config.products_path) if config.products_path else []
    )
    if config.cube_model_path:
        catalog.cube_views, catalog.measures = registry.load_cube_views(
            config.cube_model_path
        )

    # Tiering reads the registry's *declared* table list, so it can run before
    # binding. Binding then resolves those declarations against what was
    # actually collected.
    classify.classify(
        catalog,
        domain_map=config.domains,
        sandbox_patterns=config.sandbox_patterns,
    )
    registry.bind(catalog)

    report = adoption.analyse(
        catalog,
        intake_log=_load_intake(config.intake_log_path),
        targets=config.targets,
    )

    outputs = _write(config, catalog, report)

    if tabular_out:
        # Writing over the input is the normal case here, so keep one backup of
        # whatever was there before rather than trusting that a copy exists.
        if tabular_out.exists():
            backup = tabular_out.with_suffix(tabular_out.suffix + ".bak")
            backup.write_text(tabular_out.read_text(encoding="utf-8"), encoding="utf-8")
            outputs["backup"] = backup
        tabular_out.write_text(
            outputs["tabular"].read_text(encoding="utf-8"), encoding="utf-8"
        )
        outputs["tabular_out"] = tabular_out

    published_url = None
    if publish:
        published_url = _publish(config, catalog, report, dry_run=dry_run)

    return RunResult(catalog=catalog, report=report, outputs=outputs, published_url=published_url)


def _collect(
    config: Config, *, source: str, snapshot_path: Optional[Path]
) -> Catalog:
    if source == "snapshot":
        if not snapshot_path:
            raise SystemExit("--source snapshot needs --snapshot <path to markdown>")
        return snapshot_source.parse_markdown(snapshot_path, window_days=config.window_days)

    from .sources import glue as glue_source

    try:
        return glue_source.collect(
            config.environments,
            window_days=config.window_days,
            iceberg_only=config.iceberg_only,
            exclude_databases=config.exclude_databases,
        )
    except glue_source.GlueUnavailable as exc:
        if source == "glue":
            raise SystemExit(f"Glue collection failed: {exc}")
        log.warning("Glue unavailable (%s); falling back", exc)
        catalog = _fallback(config, snapshot_path, exc)
        catalog.notes.insert(
            0,
            "Live collection was unavailable this run, so these figures come from the "
            f"last recorded state ({catalog.generated_at:%Y-%m-%d}), not from a fresh "
            "read of the catalog.",
        )
        return catalog


def _fallback(config: Config, snapshot_path: Optional[Path], exc: Exception) -> Catalog:
    """Prefer the previous run's JSON over a markdown snapshot.

    The JSON is complete; the published markdown has stale and sandbox tables
    stripped out of it, so parsing that back would shrink every denominator in
    the adoption report and make the estate look better than it is.
    """
    previous_json = config.output_dir / "iceberg-catalog.json"
    if previous_json.exists():
        from .sources import previous

        log.info("restoring from %s", previous_json)
        return previous.load_json(previous_json)

    if snapshot_path:
        return snapshot_source.parse_markdown(
            snapshot_path, window_days=config.window_days
        )

    raise SystemExit(
        f"Glue collection failed and there is nothing to fall back to.\n"
        f"  {exc}\n"
        f"  Re-run with --snapshot <path to a markdown snapshot>, or once a "
        f"successful run has written {previous_json} it will be used automatically."
    )


def _write(config: Config, catalog: Catalog, report: adoption.AdoptionReport) -> dict:
    out_dir = config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    intake_url = config.intake_form_url if config.intake_configured else ""

    markdown = render_markdown.render(
        catalog, report, intake_url=intake_url, timezone_label=config.timezone
    )
    storage = render_confluence.render(
        catalog, report, intake_url=intake_url, timezone_label=config.timezone
    )

    payload = catalog.to_dict()
    payload["adoption"] = report.to_dict()
    payload["intake_form_url"] = intake_url or None

    tabular = render_tabular.render(catalog, timezone_label=config.timezone)

    paths = {
        "markdown": out_dir / "iceberg-catalog.md",
        "tabular": out_dir / "iceberg-catalog-tabular.md",
        "csv": out_dir / "iceberg-catalog-inventory.csv",
        "confluence": out_dir / "iceberg-catalog.confluence.xhtml",
        "json": out_dir / "iceberg-catalog.json",
    }
    paths["markdown"].write_text(markdown, encoding="utf-8")
    paths["tabular"].write_text(tabular, encoding="utf-8")
    paths["confluence"].write_text(storage, encoding="utf-8")
    paths["json"].write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    with paths["csv"].open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(render_tabular.csv_rows(catalog))

    # A dated copy, so week-on-week movement in the adoption metrics can be
    # reconstructed later without standing up a time-series store.
    history = out_dir / "history"
    history.mkdir(exist_ok=True)
    stamp = catalog.generated_at.strftime("%Y-%m-%d")
    (history / f"adoption-{stamp}.json").write_text(
        json.dumps(report.to_dict(), indent=2, default=str), encoding="utf-8"
    )

    return paths


def _publish(
    config: Config,
    catalog: Catalog,
    report: adoption.AdoptionReport,
    *,
    dry_run: bool,
) -> Optional[str]:
    from .publish import confluence as publisher

    problems = config.confluence.problems()
    if problems:
        raise SystemExit(
            "Cannot publish to Confluence:\n"
            + "\n".join(f"  - {p}" for p in problems)
        )

    body = render_confluence.render(
        catalog,
        report,
        intake_url=config.intake_form_url if config.intake_configured else "",
        timezone_label=config.timezone,
    )

    result = publisher.publish(
        base_url=config.confluence.base_url,
        page_id=config.confluence.page_id,
        title=config.confluence.page_title,
        body_storage=body,
        user=config.confluence.user,
        token=config.confluence.token,
        dry_run=dry_run,
    )
    return result.url if result else None


def _load_intake(path: Optional[Path]) -> Optional[list]:
    """Read the intake log, if one is configured.

    Accepts CSV or JSON. Returns None — not an empty list — when there is no
    log, so the reuse metric is reported as unknown rather than as zero.
    """
    if not path or not path.exists():
        return None

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("responses", [])

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
