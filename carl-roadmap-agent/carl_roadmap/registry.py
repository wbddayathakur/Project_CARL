"""The human-owned half of the roadmap.

Jira knows an epic's status, assignee and points. It does not know which of the
five CARL programs the epic belongs to, which sub-project, what the committed
target date is, or why a slip happened. That judgement lives here and survives
every weekly refresh.

The split matters: a refresh that regenerated the whole page from Jira would
wipe the program structure every Monday, which is exactly the failure mode that
makes people stop trusting an automated page.

`bootstrap` seeds this file from the existing hand-built HTML so none of that
curation has to be retyped.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

# Fields the agent refreshes from Jira every run. Anything not in this set is
# owned by a human and is only ever read from the registry.
JIRA_OWNED = {"n", "st", "o", "tk", "sp", "ws"}

# Fields a human owns. Listed explicitly so a typo in the YAML is caught rather
# than silently ignored.
HUMAN_OWNED = {"p", "sub", "s", "t", "fc", "a", "pri", "note", "rm", "n_override"}


class Registry:
    def __init__(self, path: Path):
        self.path = path
        self.epics: dict[str, dict] = {}
        self.meta: dict[str, Any] = {}
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                doc = yaml.safe_load(fh) or {}
            self.meta = doc.get("meta") or {}
            self.epics = {str(k): (v or {}) for k, v in (doc.get("epics") or {}).items()}

    # ------------------------------------------------------------------ query

    def entry(self, num: str) -> dict:
        return self.epics.get(str(num), {})

    def program_of(self, num: str) -> Optional[str]:
        return self.entry(num).get("p")

    def known(self, num: str) -> bool:
        return str(num) in self.epics

    def roadmap_only(self) -> dict[str, dict]:
        """Items on the roadmap that have no Jira epic behind them.

        Kept in the page deliberately — dropping them would make the roadmap
        look complete when seven committed items have nothing tracking them.
        """
        return {k: v for k, v in self.epics.items() if v.get("rm")}

    # ------------------------------------------------------------------- edit

    def upsert(self, num: str, **fields) -> None:
        bad = set(fields) - HUMAN_OWNED
        if bad:
            raise ValueError(f"not human-owned fields: {sorted(bad)}")
        self.epics.setdefault(str(num), {}).update(
            {k: v for k, v in fields.items() if v is not None}
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "meta": {
                **self.meta,
                "note": (
                    "Human-owned roadmap fields. The weekly agent reads this and "
                    "never writes over it. Jira owns name/status/owner/tickets/points."
                ),
                "fields": {
                    "p": "program code: DF | DP | MM | GA | XP",
                    "sub": "sub-project within the program",
                    "s": "committed start (YYYY-MM-DD)",
                    "t": "committed target (YYYY-MM-DD)",
                    "fc": "revised forecast, when the target has slipped",
                    "a": "actual completion",
                    "pri": "P0 | P1 | P2",
                    "note": "why — shown on hover in the page",
                    "rm": "true for a roadmap commitment with no Jira epic",
                    "n_override": "display name, when the Jira summary is wrong for exec reading",
                },
            },
            "epics": {k: self.epics[k] for k in sorted(self.epics, key=_sort_key)},
        }
        with self.path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=100)
        log.info("wrote %s entries to %s", len(self.epics), self.path)


def bootstrap_from_html(html_path: Path, out_path: Path) -> Registry:
    """Seed the registry from the DATA blob of the hand-built v3 page.

    This runs once. After it, the HTML is a render target rather than a source,
    and the curation lives somewhere a diff can show.
    """
    data = extract_data_blob(html_path)
    reg = Registry(out_path)
    for item in data.get("items", []):
        num = str(item.get("k"))
        fields = {k: item.get(k) for k in HUMAN_OWNED if item.get(k) not in (None, "")}
        # `rm` is meaningful when false, so carry it explicitly.
        fields["rm"] = bool(item.get("rm"))
        # A non-numeric key (CDC, IDS, SF2) is a roadmap placeholder by
        # definition — it can never match a Jira epic.
        if not num.isdigit():
            fields["rm"] = True
            fields["n_override"] = item.get("n")
        reg.epics[num] = {k: v for k, v in fields.items() if v is not None}
    reg.meta["bootstrapped_from"] = str(html_path)
    return reg


def extract_data_blob(html_path: Path) -> dict:
    """Pull `const DATA={...};` out of the page.

    Brace-matched rather than regex-greedy, because the blob contains braces
    inside string values and a lazy match truncates it mid-object.
    """
    text = html_path.read_text(encoding="utf-8")
    marker = "const DATA="
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"no `const DATA=` in {html_path}")
    i = text.index("{", start)
    depth, j, in_str, esc = 0, i, False, False
    while j < len(text):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[i : j + 1])
        j += 1
    raise ValueError(f"unterminated DATA object in {html_path}")


def _sort_key(k: str):
    return (0, int(k)) if str(k).isdigit() else (1, str(k))
