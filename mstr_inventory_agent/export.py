"""Write the consolidated inventory workbook."""

import os
from typing import Dict, List

import pandas as pd

MAX_COL_WIDTH = 70
MIN_COL_WIDTH = 9


def write_workbook(path: str, sheets: Dict[str, pd.DataFrame], notes: List[str]) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    with pd.ExcelWriter(path, engine="xlsxwriter",
                        engine_kwargs={"options": {"strings_to_urls": False}}) as writer:
        book = writer.book
        header_fmt = book.add_format(
            {"bold": True, "bg_color": "#1F3864", "font_color": "white", "border": 1,
             "text_wrap": True, "valign": "vcenter"}
        )
        wrap_fmt = book.add_format({"text_wrap": True, "valign": "top"})
        mono_fmt = book.add_format({"font_name": "Menlo", "valign": "top"})
        title_fmt = book.add_format({"bold": True, "font_size": 14})
        note_fmt = book.add_format({"text_wrap": True, "valign": "top"})

        _write_read_me(book, title_fmt, note_fmt, notes)

        for sheet_name, df in sheets.items():
            if df is None:
                continue
            safe = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe, index=False, startrow=0)
            ws = writer.sheets[safe]

            if df.empty:
                ws.write(0, 0, f"No rows for {sheet_name}", note_fmt)
                continue

            for c, col in enumerate(df.columns):
                ws.write(0, c, str(col), header_fmt)

            widths = _column_widths(df)
            for c, (col, width) in enumerate(zip(df.columns, widths)):
                fmt = mono_fmt if col in {"Surrogate GUID", "MSTR GUID", "Object ID"} else (
                    wrap_fmt if width >= MAX_COL_WIDTH else None
                )
                ws.set_column(c, c, width, fmt)

            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), len(df.columns) - 1)
            ws.set_row(0, 30)

    return path


def _write_read_me(book, title_fmt, note_fmt, notes: List[str]):
    ws = book.add_worksheet("Read Me")
    ws.set_column(0, 0, 118)
    ws.write(0, 0, "CARL — US Ad Sales MicroStrategy Master Inventory", title_fmt)
    row = 2
    for line in notes:
        ws.write(row, 0, line, note_fmt)
        row += 2 if line.endswith(":") else 1


def _column_widths(df: pd.DataFrame) -> List[int]:
    widths = []
    for col in df.columns:
        sample = df[col].astype("string").dropna().head(400)
        longest = int(sample.str.len().max()) if len(sample) else 0
        width = max(len(str(col)) + 3, min(longest + 2, MAX_COL_WIDTH), MIN_COL_WIDTH)
        widths.append(width)
    return widths
