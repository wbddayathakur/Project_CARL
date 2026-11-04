"""Read-only Confluence lookups.

The agent reads Confluence; it never writes to it. The deliverable is the HTML
file, and having one owner per artefact is what stops two versions of the
numbers circulating.

Two things are pulled:

  * the last-updated date and version of the pages the roadmap cites, so the
    page can show when its narrative sources were last touched rather than
    implying they are current;
  * any Jira epic key mentioned on an intake or PRD page, which is the only
    automatic way to connect a request to an epic until the intake form starts
    capturing the link itself.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

_TIMEOUT = 45
EPIC_RE = re.compile(r"\bCARL-(\d{1,5})\b")


class ConfluenceError(RuntimeError):
    pass


@dataclass
class Page:
    page_id: str
    title: str
    url: str
    version: int
    updated: str
    epic_keys: list[str] = field(default_factory=list)


class Confluence:
    def __init__(self, base_url: str, user: str, token: str):
        if not user or not token:
            raise ConfluenceError(
                "Confluence credentials missing. Set JIRA_USER and JIRA_TOKEN."
            )
        self.base = base_url.rstrip("/")
        self._auth = "Basic " + base64.b64encode(f"{user}:{token}".encode()).decode()

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", self._auth)
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise ConfluenceError(
                f"confluence {e.code} on {path}: {e.read().decode(errors='replace')[:300]}"
            ) from e
        except urllib.error.URLError as e:
            raise ConfluenceError(f"cannot reach {self.base}: {e.reason}") from e

    def page(self, page_id: str, *, scan_for_epics: bool = True) -> Page:
        expand = "version,body.storage" if scan_for_epics else "version"
        doc = self._get(f"/rest/api/content/{page_id}", {"expand": expand})
        version = doc.get("version") or {}
        body = (((doc.get("body") or {}).get("storage") or {}).get("value")) or ""
        keys = sorted(
            {f"CARL-{m}" for m in EPIC_RE.findall(body)},
            key=lambda k: int(k.split("-")[1]),
        )
        webui = (doc.get("_links") or {}).get("webui", "")
        return Page(
            page_id=str(page_id),
            title=doc.get("title", ""),
            url=f"{self.base}{webui}" if webui else f"{self.base}/pages/{page_id}",
            version=int(version.get("number") or 0),
            updated=str(version.get("when") or "")[:10],
            epic_keys=keys if scan_for_epics else [],
        )

    def pages(self, page_ids: dict[str, str]) -> dict[str, Page]:
        """Fetch several pages by {name: id}.

        A page that cannot be read is skipped with a warning rather than
        failing the run: a Confluence permission change should not stop the
        Jira numbers from refreshing.
        """
        out: dict[str, Page] = {}
        for name, pid in (page_ids or {}).items():
            try:
                out[name] = self.page(str(pid))
            except ConfluenceError as e:
                log.warning("skipping confluence page %s (%s): %s", name, pid, e)
        return out


def prd_index(pages: dict[str, Page]) -> dict[str, list[str]]:
    """Reverse the page->epics mapping into epic->pages.

    This is what fills the traceability tab's PRD column. Where an epic appears
    on no page the column stays "To link" — inventing a plausible PRD URL would
    be worse than an honest gap, because someone would click it.
    """
    index: dict[str, list[str]] = {}
    for name, page in pages.items():
        for key in page.epic_keys:
            index.setdefault(key, []).append(name)
    return index
