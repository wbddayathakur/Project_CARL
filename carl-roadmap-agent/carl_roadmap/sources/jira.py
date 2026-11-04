"""Pull CARL epics and their children from Jira.

Uses the REST API with an API token rather than the interactive MCP connector,
because this has to run on a schedule with nobody logged in.

Two requests per run regardless of project size: one paged search for epics,
one paged search for every child of those epics. Fetching children per-epic
would be ~90 round trips and would rate-limit on a slow morning.
"""

from __future__ import annotations

import base64
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterator, Optional

from ..model import Buckets, Epic, Story

log = logging.getLogger(__name__)

_TIMEOUT = 60
_PAGE = 100
_MAX_RETRIES = 4


class JiraError(RuntimeError):
    pass


class Jira:
    def __init__(self, base_url: str, user: str, token: str):
        if not user or not token:
            raise JiraError(
                "Jira credentials missing. Set JIRA_USER and JIRA_TOKEN "
                "(see .env.example)."
            )
        self.base = base_url.rstrip("/")
        self._auth = "Basic " + base64.b64encode(
            f"{user}:{token}".encode()
        ).decode()

    # ---------------------------------------------------------------- request

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", self._auth)
        req.add_header("Accept", "application/json")

        for attempt in range(_MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")[:400]
                # 429 and 5xx are worth another go; 400 and 401 never are.
                if e.code in (429, 500, 502, 503, 504) and attempt < _MAX_RETRIES - 1:
                    wait = int(e.headers.get("Retry-After") or 2 ** (attempt + 1))
                    log.warning("jira %s on %s — retrying in %ss", e.code, path, wait)
                    time.sleep(wait)
                    continue
                if e.code == 401:
                    raise JiraError(
                        "Jira rejected the credentials (401). The API token may "
                        "have expired — regenerate it at id.atlassian.com."
                    ) from e
                raise JiraError(f"jira {e.code} on {path}: {body}") from e
            except urllib.error.URLError as e:
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise JiraError(f"cannot reach {self.base}: {e.reason}") from e
        raise JiraError(f"gave up on {path}")

    def _search(self, jql: str, fields: list[str]) -> Iterator[dict]:
        """Page through /search/jql.

        Uses the token-paged endpoint rather than startAt, which Atlassian has
        deprecated and which silently caps out at 5000 results on this tenant.
        """
        token: Optional[str] = None
        seen = 0
        while True:
            params = {
                "jql": jql,
                "maxResults": _PAGE,
                "fields": ",".join(fields),
            }
            if token:
                params["nextPageToken"] = token
            page = self._get("/rest/api/3/search/jql", params)
            issues = page.get("issues") or []
            for issue in issues:
                yield issue
            seen += len(issues)
            token = page.get("nextPageToken")
            if page.get("isLast") or not token or not issues:
                break
        log.info("jql returned %s issues: %s", seen, jql)

    # ------------------------------------------------------------------ fetch

    def epics(self, project: str, issue_types: list[str], points_field: str) -> list[Epic]:
        types = ", ".join(f'"{t}"' for t in issue_types)
        jql = f"project = {project} AND issuetype IN ({types}) ORDER BY key ASC"
        fields = [
            "summary", "status", "assignee", "issuetype", "labels",
            "duedate", "created", "updated", "parent", points_field,
        ]
        out = []
        for issue in self._search(jql, fields):
            f = issue.get("fields") or {}
            parent = f.get("parent") or {}
            key = issue["key"]
            out.append(
                Epic(
                    key=key,
                    num=key.split("-", 1)[1],
                    summary=(f.get("summary") or "").strip(),
                    status=_name(f.get("status")),
                    assignee=_display(f.get("assignee")),
                    issue_type=_name(f.get("issuetype")),
                    labels=list(f.get("labels") or []),
                    due=f.get("duedate"),
                    created=_day(f.get("created")),
                    updated=_day(f.get("updated")),
                    parent_key=parent.get("key"),
                    parent_summary=((parent.get("fields") or {}).get("summary") or "").strip()
                    or None,
                )
            )
        return out

    def children_of(
        self,
        epic_keys: list[str],
        points_field: str,
        buckets: Buckets,
    ) -> dict[str, list[Story]]:
        """Every child of the given epics, grouped by parent key.

        `parent IN (...)` is chunked because Jira rejects JQL over ~8kB, which
        this project passes at roughly 300 keys.
        """
        by_parent: dict[str, list[Story]] = {k: [] for k in epic_keys}
        fields = ["summary", "status", "assignee", "issuetype", "parent", "updated", points_field]

        for chunk in _chunks(epic_keys, 120):
            keys = ", ".join(chunk)
            jql = f"parent IN ({keys}) ORDER BY key ASC"
            for issue in self._search(jql, fields):
                f = issue.get("fields") or {}
                parent_key = (f.get("parent") or {}).get("key")
                if parent_key not in by_parent:
                    continue
                status = _name(f.get("status"))
                by_parent[parent_key].append(
                    Story(
                        key=issue["key"],
                        summary=(f.get("summary") or "").strip(),
                        status=status,
                        bucket=buckets.of(status),
                        points=_points(f.get(points_field)),
                        assignee=_display(f.get("assignee")),
                        issue_type=_name(f.get("issuetype")),
                        updated=_day(f.get("updated")),
                    )
                )
        return by_parent


# -------------------------------------------------------------------- helpers


def _chunks(items: list[str], n: int) -> Iterator[list[str]]:
    for i in range(0, len(items), n):
        yield items[i : i + n]


def _name(obj) -> str:
    return ((obj or {}).get("name") or "").strip()


def _display(obj) -> str:
    return ((obj or {}).get("displayName") or "").strip()


def _day(ts) -> Optional[str]:
    return str(ts)[:10] if ts else None


def _points(value) -> float:
    """Story points, defaulting to zero.

    An unestimated story is zero points, not missing data — the whole reason
    the exec view flags "unsized" epics is that zero is the honest number.
    """
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
