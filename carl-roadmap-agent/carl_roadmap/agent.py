"""The weekly run.

Pull Jira, merge with the human-owned registry, reconcile, render into the
published HTML, and keep a dated snapshot so week-on-week movement can be
reconstructed later.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from . import reconcile
from .config import Config
from .model import Buckets, Epic, Rollup, rag_for
from .registry import Registry
from .render import write as write_html
from .sources.cached import load as cached_load
from .sources.confluence import Confluence, ConfluenceError, prd_index
from .sources.jira import Jira, JiraError

log = logging.getLogger(__name__)


def run(
    cfg: Config,
    *,
    dry_run: bool = False,
    skip_confluence: bool = False,
    asof: Optional[str] = None,
) -> dict:
    asof = asof or date.today().isoformat()
    buckets = Buckets(cfg.get("buckets", default={}) or {})
    rag_rules = cfg.get("rag", default={}) or {}

    registry = Registry(cfg.path("registry", "epics", default="registry/epic-map.yaml"))
    if not registry.epics:
        raise SystemExit(
            "registry/epic-map.yaml is empty. Run `python -m carl_roadmap bootstrap` "
            "first — it seeds the programme structure from the existing page so "
            "none of that mapping has to be retyped."
        )

    # Read the previous snapshot before this run writes its own, so a re-run on
    # the same day still compares against last week rather than against itself.
    previous = _load_previous(cfg, exclude_asof=asof)

    epics = _load_jira(cfg, buckets)
    _apply_committed_dates(epics, registry)
    pages, prd = _load_confluence(cfg, skip=skip_confluence)

    rag_of = lambda e: rag_for(e, rag_rules, date.fromisoformat(asof))  # noqa: E731

    items = _build_items(epics, registry, rag_of, asof)
    items += _roadmap_only_items(epics, registry)

    rels, deps, dangling = _prune_dangling(
        _carry_over(cfg, "rels"), _carry_over(cfg, "deps"), items
    )

    data = {
        "items": items,
        "rels": rels,
        "deps": deps,
        "notes": [f.as_row() for f in _findings(epics, registry, asof)],
        "prd": prd,
        "pages": {n: {"t": p.title, "u": p.url, "v": p.version, "d": p.updated}
                  for n, p in pages.items()},
        "asof": asof,
        "delta": _delta(items, previous),
    }

    report = {
        "asof": asof,
        "epics": len(epics),
        "tickets": sum(e.ticket_count for e in epics),
        "points": sum(e.points_total for e in epics),
        "programs": _program_summary(items),
        "findings": reconcile.summarise(_findings(epics, registry, asof)),
        "unmapped_statuses": sorted(buckets.unmapped),
        "pruned_links": dangling,
    }

    if buckets.unmapped:
        log.warning(
            "statuses not in config.yaml buckets, counted as requirements: %s",
            ", ".join(sorted(buckets.unmapped)),
        )

    _write_json(cfg, data, report)
    _write_snapshot(cfg, items, asof)

    if dry_run:
        log.info("dry run — the page was not touched")
        report["html"] = {"changed": False, "dry_run": True}
        return report

    html_path = cfg.path("output", "html_path")
    history = cfg.path("output", "snapshot_dir", default="out/history")
    report["html"] = write_html(
        html_path,
        data=data,
        asof=asof,
        history_dir=history,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        status_colours=_status_colours(epics, buckets),
    )
    return report


# The page's own palette, by bucket. Deliberately the same greens and ambers
# the progress bars use, so a bar and a swimlane agree about what "in build"
# looks like.
_BUCKET_COLOUR = {
    "done": "#86efac",
    "build": "#fde68a",
    "requirements": "#e2e8f0",
    "excluded": "#e5e7eb",
}


def _status_colours(epics, buckets: Buckets) -> dict:
    """A colour for every status this run actually saw.

    Jira workflows gain steps without telling anyone. The page indexes its
    colour map by raw status name, so an unknown status renders as no colour
    at all — see `_patch_status_colours`. Supplying the live set means the
    worst case is a grey bar rather than an unstyled one.
    """
    return {
        e.status: _BUCKET_COLOUR.get(buckets.of(e.status), "#e2e8f0")
        for e in epics if e.status
    }


# ------------------------------------------------------------------- loading


def _load_jira(cfg: Config, buckets: Buckets) -> list[Epic]:
    cache = cfg.path("jira", "cache_path", default=None)
    if cache and cache.exists():
        log.info("using the Jira cache at %s; no REST call this run", cache)
        return cached_load(cache, buckets)

    user, token = cfg.credentials("jira")
    jira = Jira(cfg.get("jira", "base_url"), user, token)
    points_field = cfg.get("jira", "story_points_field")
    project = cfg.get("jira", "project", default="CARL")

    epics = jira.epics(
        project,
        cfg.get("jira", "epic_issue_types", default=["Epic"]),
        points_field,
    )
    log.info("pulled %s epics from %s", len(epics), project)

    children = jira.children_of([e.key for e in epics], points_field, buckets)
    for e in epics:
        e.stories = children.get(e.key, [])
        e.roll_up(buckets)
    log.info("pulled %s child issues", sum(len(v) for v in children.values()))
    return epics


def _load_confluence(cfg: Config, *, skip: bool):
    if skip:
        return {}, {}
    try:
        user, token = cfg.credentials("confluence")
        conf = Confluence(cfg.get("confluence", "base_url"), user, token)
        pages = conf.pages(cfg.get("confluence", "pages", default={}) or {})
        return pages, prd_index(pages)
    except ConfluenceError as e:
        # Never fail the run on Confluence. The Jira numbers are the point.
        log.warning("confluence unavailable, continuing without it: %s", e)
        return {}, {}


# -------------------------------------------------------------------- shaping


def _apply_committed_dates(epics, registry: Registry) -> None:
    """Let the RAG see the dates the page shows.

    `rag_for` reads `epic.due`, which comes from Jira's own due-date field. This
    project does not populate it; the committed dates live in the registry. So
    an epic could sit a month past its committed target and still be scored
    green, with the page showing both facts side by side. A revised forecast
    wins over the original target, matching what the page displays.
    """
    for e in epics:
        entry = registry.entry(e.num)
        committed = entry.get("fc") or entry.get("t")
        if committed:
            e.due = committed


def _build_items(epics, registry: Registry, rag_of, asof: str) -> list[dict]:
    """One row per Jira epic, Jira fields fresh and human fields preserved."""
    out = []
    for e in epics:
        entry = registry.entry(e.num)
        if not entry.get("p"):
            # Unmapped epics still appear, in a holding programme, so that new
            # work is visible on the tracker the week it is created rather than
            # the week someone remembers to map it.
            program, sub = "XP", "Unmapped \u2014 needs a programme"
        else:
            program, sub = entry["p"], entry.get("sub") or "\u2014"

        out.append(
            {
                "k": e.num,
                "n": entry.get("n_override") or e.summary,
                "p": program,
                "sub": sub,
                "ws": e.parent_summary or "\u2014",
                "st": e.status,
                "o": e.assignee or "\u2014",
                "tk": e.ticket_count,
                "sp": e.sp_array(),
                "s": entry.get("s", ""),
                "t": entry.get("t", "") or (e.due or ""),
                "fc": entry.get("fc"),
                "a": entry.get("a"),
                "pri": entry.get("pri", "\u2014"),
                "rag": rag_of(e),
                "note": entry.get("note", ""),
                "rm": False,
                "upd": e.updated,
                "bl": _round(e.blocked_points),
            }
        )
    return out


def _roadmap_only_items(epics, registry: Registry) -> list[dict]:
    """Commitments with no epic. Carried through untouched."""
    live = {e.num for e in epics}
    out = []
    for num, entry in registry.roadmap_only().items():
        if num in live:
            continue
        out.append(
            {
                "k": num,
                "n": entry.get("n_override") or f"({num})",
                "p": entry.get("p", "XP"),
                "sub": entry.get("sub", "\u2014"),
                "ws": "\u2014",
                "st": entry.get("st", "Pending Scope"),
                "o": entry.get("o", "\u2014"),
                "tk": None,
                "sp": None,
                "s": entry.get("s", ""),
                "t": entry.get("t", ""),
                "fc": entry.get("fc"),
                "a": entry.get("a"),
                "pri": entry.get("pri", "\u2014"),
                "rag": entry.get("rag", "A"),
                "note": entry.get("note", ""),
                "rm": True,
            }
        )
    return out


def _findings(epics, registry: Registry, asof: str):
    return reconcile.run_all(epics, registry, asof=asof)


def _program_summary(items: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for i in items:
        if i.get("rm") or not i.get("sp"):
            continue
        p = i["p"]
        s = out.setdefault(p, {"epics": 0, "sp": 0.0, "done": 0.0, "build": 0.0, "req": 0.0})
        s["epics"] += 1
        s["sp"] += i["sp"][0]
        s["done"] += i["sp"][1]
        s["build"] += i["sp"][2]
        s["req"] += i["sp"][3]
    for s in out.values():
        s["pct"] = round(s["done"] / s["sp"] * 100, 1) if s["sp"] else 0.0
    return out


# ------------------------------------------------------------------ carry-over


def _carry_over(cfg: Config, key: str):
    """Keep the hand-maintained `rels` and `deps` from the current page.

    Dependencies between programmes and on outside teams are judgement, not
    data — Jira issue links do not carry "this vendor owes us an API scope".
    Rather than regenerate them, the agent reads them back out of the page it
    is about to rewrite and puts them straight back.
    """
    from .registry import extract_data_blob

    html_path = cfg.path("output", "html_path")
    try:
        blob = extract_data_blob(html_path)
    except (FileNotFoundError, ValueError) as e:
        log.warning("could not read existing %s from the page: %s", key, e)
        return []
    return blob.get(key, [])


def _prune_dangling(rels: list, deps: list, items: list[dict]):
    """Drop carried-over links that point at items this run no longer has.

    `rels` and `deps` are hand-maintained and are carried across from the
    previous page, but the item set is rebuilt from Jira every week. An epic
    that gets deleted, or a registry key that gets corrected, leaves a link
    pointing at nothing. The page indexes items by key with no guard, so a
    single dangling reference throws and *every tab renders blank* — the whole
    document is lost, not just the link. Prune here and report it.
    """
    live = {i["k"] for i in items}
    dropped: list[str] = []

    kept_rels = []
    for r in rels:
        missing = [z for z in r if z not in live]
        if missing:
            dropped.append("rel %s (no item %s)" % ("\u2192".join(r), ", ".join(missing)))
        else:
            kept_rels.append(r)

    kept_deps = []
    for d in deps:
        blocked = d.get("b") or []
        missing = [z for z in blocked if z not in live]
        if missing:
            dropped.append(
                "dep %s no longer blocks %s" % (d.get("id", "?"), ", ".join(missing))
            )
            d = dict(d, b=[z for z in blocked if z in live])
        # A gate that blocks nothing is still a real external ask; keep it.
        kept_deps.append(d)

    if dropped:
        log.warning("pruned %s dangling carry-over link(s): %s",
                    len(dropped), "; ".join(dropped))
    return kept_rels, kept_deps, dropped


# --------------------------------------------------------------- week-on-week


def _snapshot_path(cfg: Config, asof: str) -> Path:
    d = cfg.path("output", "snapshot_dir", default="out/history")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"roadmap-{asof}.json"


def _write_snapshot(cfg: Config, items: list[dict], asof: str) -> None:
    slim = {
        i["k"]: {"sp": i.get("sp"), "st": i.get("st"), "tk": i.get("tk")}
        for i in items
        if not i.get("rm")
    }
    _snapshot_path(cfg, asof).write_text(
        json.dumps({"asof": asof, "items": slim}, indent=1), encoding="utf-8"
    )


def _load_previous(cfg: Config, *, exclude_asof: str | None = None) -> dict:
    d = cfg.path("output", "snapshot_dir", default="out/history")
    if not d or not d.exists():
        return {}
    snaps = sorted(d.glob("roadmap-*.json"))
    if exclude_asof:
        snaps = [s for s in snaps if s.stem != f"roadmap-{exclude_asof}"]
    if not snaps:
        return {}
    try:
        return json.loads(snaps[-1].read_text(encoding="utf-8")).get("items", {})
    except (OSError, json.JSONDecodeError):
        return {}


def _delta(items: list[dict], previous: dict) -> dict:
    """Points completed since the last snapshot, per epic and in total.

    This is the number the Monday review actually wants: not "43% done" but
    "we moved 38 points last week".
    """
    if not previous:
        return {}
    moved, by_epic = 0.0, {}
    for i in items:
        if i.get("rm") or not i.get("sp"):
            continue
        before = (previous.get(i["k"]) or {}).get("sp")
        if not before:
            continue
        d = i["sp"][1] - before[1]
        if d:
            by_epic[i["k"]] = _round(d)
            moved += d
    return {"done_delta": _round(moved), "by_epic": by_epic}


def _write_json(cfg: Config, data: dict, report: dict) -> None:
    p = cfg.path("output", "json_path", default="out/carl-roadmap.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"report": report, "data": data}, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )


def _round(x: float) -> float:
    return int(x) if float(x).is_integer() else round(x, 1)
