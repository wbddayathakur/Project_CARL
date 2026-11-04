"""CLI.

  python -m carl_roadmap bootstrap     seed the registry from the existing page
  python -m carl_roadmap check         connectivity and field sanity, no writes
  python -m carl_roadmap run           the weekly refresh
  python -m carl_roadmap run --dry-run everything except touching the page
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .registry import Registry, bootstrap_from_html

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="carl_roadmap")
    ap.add_argument("command", choices=["bootstrap", "check", "run"])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--dry-run", action="store_true",
                    help="compute everything, write out/, leave the page alone")
    ap.add_argument("--skip-confluence", action="store_true")
    ap.add_argument("--asof", help="override the as-of date (YYYY-MM-DD)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    log = logging.getLogger("carl_roadmap")
    cfg = Config.load(args.config)

    if args.command == "bootstrap":
        return _bootstrap(cfg, log)
    if args.command == "check":
        return _check(cfg, log)
    return _run(cfg, args, log)


def _bootstrap(cfg: Config, log) -> int:
    html = cfg.path("output", "html_path")
    out = cfg.path("registry", "epics", default="registry/epic-map.yaml")
    if out.exists():
        log.error(
            "%s already exists. Bootstrap is a one-time seed and will not "
            "overwrite hand edits — delete it first if that is really what you want.",
            out,
        )
        return 1
    reg = bootstrap_from_html(html, out)
    reg.save()
    mapped = sum(1 for v in reg.epics.values() if v.get("p"))
    print(f"seeded {len(reg.epics)} entries ({mapped} with a programme) into {out}")
    return 0


def _check(cfg: Config, log) -> int:
    """Prove the credentials and the story-point field before trusting a run."""
    from .model import Buckets
    from .sources.jira import Jira, JiraError

    ok = True
    user, token = cfg.credentials("jira")
    masked = (user[:3] + "***") if user else "(unset)"
    print(f"jira user:  {masked}")
    print(f"jira token: {'set' if token else '(unset)'}")

    try:
        jira = Jira(cfg.get("jira", "base_url"), user, token)
        field = cfg.get("jira", "story_points_field")
        epics = jira.epics(
            cfg.get("jira", "project", default="CARL"),
            cfg.get("jira", "epic_issue_types", default=["Epic"]),
            field,
        )
        print(f"epics:      {len(epics)}")

        buckets = Buckets(cfg.get("buckets", default={}) or {})
        sample = [e.key for e in epics[:25]]
        kids = jira.children_of(sample, field, buckets)
        pts = sum(s.points for v in kids.values() for s in v)
        n = sum(len(v) for v in kids.values())
        print(f"sample:     {n} children of {len(sample)} epics, {pts:g} SP via {field}")
        if n and pts == 0:
            print(f"  ! {field} returned no points on any of them — wrong field?")
            ok = False
        if buckets.unmapped:
            print(f"  ! statuses not in config buckets: {sorted(buckets.unmapped)}")
    except JiraError as e:
        print(f"jira:       FAILED — {e}")
        ok = False

    reg_path = cfg.path("registry", "epics", default="registry/epic-map.yaml")
    reg = Registry(reg_path)
    print(f"registry:   {len(reg.epics)} entries at {reg_path}")
    if not reg.epics:
        print("  ! empty — run `bootstrap` first")
        ok = False

    html = cfg.path("output", "html_path")
    print(f"page:       {'found' if html and html.exists() else 'MISSING'} {html}")
    if not (html and html.exists()):
        ok = False

    print("outlook:    not connected — see README, 'Outlook'")
    return 0 if ok else 1


def _run(cfg: Config, args, log) -> int:
    from .agent import run
    from .sources.jira import JiraError

    try:
        report = run(
            cfg,
            dry_run=args.dry_run,
            skip_confluence=args.skip_confluence,
            asof=args.asof,
        )
    except JiraError as e:
        log.error("%s", e)
        return 2

    f = report["findings"]
    print(
        f"{report['epics']} epics \u00b7 {report['tickets']} tickets \u00b7 "
        f"{report['points']:g} SP as of {report['asof']}"
    )
    for code in ("blocker", "check", "note"):
        if f.get(code):
            print(f"  {f[code]} {code}{'s' if f[code] != 1 else ''}")
    html = report.get("html") or {}
    if html.get("dry_run"):
        print("page not written (--dry-run)")
    elif html.get("changed"):
        print(f"page updated: {html.get('path')}")
    else:
        print("page already current")
    # A blocker means a new epic is missing from every rollup. Exit non-zero so
    # a scheduled run surfaces it instead of looking like a clean week.
    return 1 if f.get("blocker") else 0


if __name__ == "__main__":
    raise SystemExit(main())
