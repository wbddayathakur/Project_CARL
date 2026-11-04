"""Checks that run every week and land on the Data Notes tab.

These are the recurring mismatches between the roadmap and Jira. Each one was
found by hand at least once; running them every Monday means nobody has to find
them by hand again, and means the page says what it does not know rather than
quietly presenting a wrong total.

Every finding carries the evidence that produced it, so it can be settled
without reopening both files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

from .model import Epic
from .registry import Registry


@dataclass
class Finding:
    code: str
    severity: str           # "blocker" | "check" | "note"
    subject: str            # epic key or roadmap id
    detail: str
    evidence: str = ""

    def as_row(self) -> list[str]:
        return [self.code, self.severity, self.subject, self.detail, self.evidence]


def run_all(epics: list[Epic], registry: Registry, *, asof: str) -> list[Finding]:
    out: list[Finding] = []
    out += orphan_roadmap_items(epics, registry)
    out += unmapped_epics(epics, registry)
    out += name_drift(epics, registry)
    out += label_vs_name(epics)
    out += unsized_but_active(epics)
    out += stale_in_progress(epics, asof=asof)
    out += duplicate_display_names(epics)
    out += overdue_without_forecast(epics, registry, asof=asof)
    return out


# --------------------------------------------------------------------- checks


def orphan_roadmap_items(epics: list[Epic], registry: Registry) -> list[Finding]:
    """Roadmap commitments with no Jira epic behind them.

    These are the "roadmap-only" rows. They stay on the page on purpose: a
    commitment nobody is tracking is the most useful thing on a status report,
    and hiding it would make the roadmap look complete.
    """
    live = {e.num for e in epics}
    out = []
    for num, entry in registry.roadmap_only().items():
        if num in live:
            out.append(
                Finding(
                    code="RM-RESOLVED",
                    severity="note",
                    subject=_key(num),
                    detail=(
                        "Tagged roadmap-only but a Jira epic now exists. "
                        "Clear `rm: true` in registry/epic-map.yaml."
                    ),
                )
            )
            continue
        name = entry.get("n_override") or entry.get("note") or "(unnamed)"
        out.append(
            Finding(
                code="RM-ONLY",
                severity="check",
                subject=_key(num),
                detail="Roadmap commitment with no epic in the Jira export.",
                evidence=f"{name} \u00b7 program {entry.get('p', '?')}"
                f" \u00b7 target {entry.get('t') or 'none set'}",
            )
        )
    return out


def unmapped_epics(epics: list[Epic], registry: Registry) -> list[Finding]:
    """Epics Jira knows about that the roadmap has never placed.

    New epics appear weekly. Until someone assigns a programme they are
    invisible on every tab except the tracker, so this is the one finding that
    needs action before the next refresh.
    """
    out = []
    for e in epics:
        if registry.known(e.num) and registry.program_of(e.num):
            continue
        out.append(
            Finding(
                code="NO-PROGRAM",
                severity="blocker",
                subject=e.key,
                detail=(
                    "New epic with no programme assigned — it is missing from "
                    "every programme rollup until one is set."
                ),
                evidence=f"{e.summary} \u00b7 {e.status} \u00b7 "
                f"{e.ticket_count} tickets \u00b7 {e.points_total:g} SP"
                + (f" \u00b7 under {e.parent_summary}" if e.parent_summary else ""),
            )
        )
    return out


def name_drift(epics: list[Epic], registry: Registry) -> list[Finding]:
    """The Jira summary has moved away from the name shown on the page.

    Renames in Jira are routine and usually fine. They matter when the page is
    being read alongside Jira in a review and the two no longer agree.
    """
    out = []
    for e in epics:
        override = registry.entry(e.num).get("n_override")
        if not override:
            continue
        if _slug(override) != _slug(e.summary):
            out.append(
                Finding(
                    code="NAME-DRIFT",
                    severity="note",
                    subject=e.key,
                    detail="Page name and Jira summary differ.",
                    evidence=f"page: {override!r} \u00b7 jira: {e.summary!r}",
                )
            )
    return out


def label_vs_name(epics: list[Epic]) -> list[Finding]:
    """Catches the AID/AIP class of mismatch.

    CARL-3958 is filed under project "AID" while its summary says AIP. One of
    the two is wrong and the rollup follows whichever the grouping uses.
    """
    pairs = [("AID", "AIP"), ("AIP", "AID")]
    out = []
    for e in epics:
        blob = " ".join(e.labels).upper()
        name = e.summary.upper()
        for a, b in pairs:
            if a in blob.split() and b in re.findall(r"[A-Z]{3,}", name):
                out.append(
                    Finding(
                        code="LABEL-MISMATCH",
                        severity="check",
                        subject=e.key,
                        detail=f"Labelled {a} but the summary says {b}.",
                        evidence=f"labels={e.labels} \u00b7 summary={e.summary!r}",
                    )
                )
    return out


def unsized_but_active(epics: list[Epic]) -> list[Finding]:
    """Epics carrying tickets but zero points.

    These are the ones that make a programme look smaller than it is. An
    unsized epic contributes nothing to the denominator, so percent-complete
    rises every time one is opened.
    """
    out = []
    for e in epics:
        if e.ticket_count and not e.sized:
            out.append(
                Finding(
                    code="UNSIZED",
                    severity="check",
                    subject=e.key,
                    detail=(
                        f"{e.ticket_count} tickets, no story points — excluded "
                        f"from every percentage on the page."
                    ),
                    evidence=f"{e.summary} \u00b7 {e.status}",
                )
            )
    return out


def stale_in_progress(epics: list[Epic], *, asof: str, days: int = 45) -> list[Finding]:
    """In Progress but untouched for a month and a half."""
    out = []
    for e in epics:
        if e.status.strip().casefold() != "in progress" or not e.updated:
            continue
        age = _days_between(e.updated, asof)
        if age is not None and age > days:
            out.append(
                Finding(
                    code="STALE",
                    severity="note",
                    subject=e.key,
                    detail=f"In Progress but not updated for {age} days.",
                    evidence=f"{e.summary} \u00b7 last update {e.updated}",
                )
            )
    return out


def duplicate_display_names(epics: list[Epic]) -> list[Finding]:
    """Two epics with effectively the same name.

    The reported CARL-3932 duplication is this shape: the same work tracked
    twice means its points are counted twice in the programme total.
    """
    seen: dict[str, list[str]] = {}
    for e in epics:
        seen.setdefault(_slug(e.summary), []).append(e.key)
    out = []
    for slug, keys in seen.items():
        if len(keys) > 1:
            out.append(
                Finding(
                    code="DUPLICATE",
                    severity="check",
                    subject=", ".join(sorted(keys)),
                    detail="Several epics share a summary — points may be double-counted.",
                    evidence=slug,
                )
            )
    return out


def overdue_without_forecast(
    epics: list[Epic], registry: Registry, *, asof: str
) -> list[Finding]:
    """Past its target with no revised date.

    An overdue item with a forecast is a managed slip. One without is an
    unanswered question, and those are what the Monday review is for.
    """
    out = []
    for e in epics:
        entry = registry.entry(e.num)
        target = entry.get("t") or e.due
        if not target or entry.get("a") or entry.get("fc"):
            continue
        if str(target) < asof and e.pct_done < 100:
            out.append(
                Finding(
                    code="OVERDUE",
                    severity="check",
                    subject=e.key,
                    detail=f"Target {target} passed with {e.pct_done:.0f}% done and no revised date.",
                    evidence=f"{e.summary} \u00b7 {e.status}",
                )
            )
    return out


# -------------------------------------------------------------------- helpers


def as_rows(findings: Iterable[Finding]) -> list[list[str]]:
    order = {"blocker": 0, "check": 1, "note": 2}
    return [
        f.as_row()
        for f in sorted(findings, key=lambda x: (order.get(x.severity, 9), x.code, x.subject))
    ]


def summarise(findings: list[Finding]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        out[f.severity] = out.get(f.severity, 0) + 1
    return out


def _key(num: str) -> str:
    return f"CARL-{num}" if str(num).isdigit() else str(num)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").casefold()).strip()


def _days_between(a: str, b: str) -> Optional[int]:
    from datetime import date

    try:
        d1 = date.fromisoformat(str(a)[:10])
        d2 = date.fromisoformat(str(b)[:10])
    except ValueError:
        return None
    return (d2 - d1).days
