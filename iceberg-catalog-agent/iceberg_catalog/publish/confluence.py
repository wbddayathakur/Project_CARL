"""Publish the rendered page to Confluence.

Updates one existing page in place rather than creating a new one each week.
That is deliberate: the page URL is the link that sits inside the intake form,
so it has to survive every republish. Create the page once by hand, put its ID
in config.yaml, and the agent owns the body from then on.

Uses stdlib urllib rather than `requests` so the only runtime dependencies are
PyYAML and boto3. Confluence's REST API is one PUT; it does not justify a third.
"""

from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

_TIMEOUT = 60


class ConfluenceError(RuntimeError):
    pass


@dataclass
class PublishResult:
    page_id: str
    version: int
    url: str
    title: str


def publish(
    *,
    base_url: str,
    page_id: str,
    title: str,
    body_storage: str,
    user: str,
    token: str,
    dry_run: bool = False,
) -> Optional[PublishResult]:
    """Replace the body of an existing Confluence page.

    Confluence requires the new version number to be exactly current + 1, so the
    current version is fetched first. Two runs racing each other will make the
    second fail with a 409 rather than silently clobber the first.
    """
    base_url = base_url.rstrip("/")
    auth = _auth_header(user, token)

    current = _get(f"{base_url}/rest/api/content/{page_id}?expand=version", auth)
    version = int(current["version"]["number"])
    resolved_title = title or current.get("title", "")

    if dry_run:
        log.info("dry run: would update page %s to version %s", page_id, version + 1)
        return None

    payload = {
        "id": page_id,
        "type": "page",
        "title": resolved_title,
        "version": {
            "number": version + 1,
            "message": "Automated weekly refresh — iceberg-catalog-agent",
            "minorEdit": True,
        },
        "body": {"storage": {"value": body_storage, "representation": "storage"}},
    }

    updated = _put(f"{base_url}/rest/api/content/{page_id}", auth, payload)

    webui = (updated.get("_links") or {}).get("webui", "")
    return PublishResult(
        page_id=page_id,
        version=int(updated["version"]["number"]),
        url=f"{base_url}{webui}" if webui else f"{base_url}/pages/{page_id}",
        title=updated.get("title", resolved_title),
    )


def _auth_header(user: str, token: str) -> str:
    raw = f"{user}:{token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _get(url: str, auth: str) -> dict:
    return _request("GET", url, auth, None)


def _put(url: str, auth: str, payload: dict) -> dict:
    return _request("PUT", url, auth, payload)


def _request(method: str, url: str, auth: str, payload: Optional[dict]) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", auth)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise ConfluenceError(
            f"{method} {url} failed with {exc.code}. {_explain(exc.code)} {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ConfluenceError(f"could not reach Confluence at {url}: {exc.reason}") from exc


def _explain(code: int) -> str:
    return {
        401: "Check CONFLUENCE_USER is your account email and CONFLUENCE_TOKEN is an "
             "API token from id.atlassian.com, not your password.",
        403: "The account can see the page but cannot edit it. Check space permissions.",
        404: "No page with that ID in this tenant. Check confluence.page_id.",
        409: "Version conflict — someone edited the page between read and write. "
             "Re-run.",
    }.get(code, "")
