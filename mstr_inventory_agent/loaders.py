"""Read the raw MicroStrategy exports into normalised frames."""

import os
from typing import Dict, List, Tuple

import pandas as pd

from .config import SOURCES, DRAFT_FILENAME, DRAFT_CARRY_FORWARD_SHEETS, SourceSpec


class SourceError(RuntimeError):
    pass


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace("\u00a0", " ", regex=False)
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            )
    df = df.dropna(how="all")
    return df


def load_source(source_dir: str, spec: SourceSpec) -> pd.DataFrame:
    path = os.path.join(source_dir, spec.filename)
    if not os.path.exists(path):
        if spec.required:
            raise SourceError(f"Required export not found: {path}")
        return pd.DataFrame()

    df = _clean(pd.read_excel(path))

    missing = [c for c in [spec.name_col] + ([spec.path_col] if spec.path_col else [])
               if c not in df.columns]
    if missing:
        raise SourceError(
            f"{spec.filename}: expected column(s) {missing} but found {list(df.columns)}"
        )

    df = df[df[spec.name_col].notna()]
    df["__source_file"] = spec.filename
    df["__source_key"] = spec.key
    return df.reset_index(drop=True)


def load_all(source_dir: str) -> Tuple[Dict[str, pd.DataFrame], List[dict]]:
    """Return {source_key: frame} plus a provenance log describing what was read."""
    frames: Dict[str, pd.DataFrame] = {}
    provenance: List[dict] = []

    for key, spec in SOURCES.items():
        df = load_source(source_dir, spec)
        frames[key] = df
        full = os.path.join(source_dir, spec.filename)
        provenance.append(
            {
                "Source File": spec.filename,
                "Object Type": spec.object_type,
                "Rows Read": len(df),
                "Columns In Export": ", ".join(c for c in df.columns
                                               if not c.startswith("__")),
                "Last Modified": _mtime(full),
                "Size (KB)": round(os.path.getsize(full) / 1024, 1)
                if os.path.exists(full) else None,
            }
        )

    return frames, provenance


def load_draft_sheets(source_dir: str) -> Dict[str, pd.DataFrame]:
    """Carry forward hand-built analysis sheets that the raw exports do not contain."""
    path = os.path.join(source_dir, DRAFT_FILENAME)
    if not os.path.exists(path):
        return {}
    out: Dict[str, pd.DataFrame] = {}
    try:
        book = pd.ExcelFile(path)
    except Exception:
        return {}
    for sheet in DRAFT_CARRY_FORWARD_SHEETS:
        if sheet in book.sheet_names:
            out[sheet] = book.parse(sheet)
    return out


def _mtime(path: str):
    if not os.path.exists(path):
        return None
    return pd.Timestamp(os.path.getmtime(path), unit="s", tz="UTC").tz_convert(
        "Asia/Kolkata"
    ).strftime("%Y-%m-%d %H:%M")
