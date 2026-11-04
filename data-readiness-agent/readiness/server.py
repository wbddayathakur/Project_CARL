"""Local web UI: python3 -m readiness.server [--port 8765]

Standard library only. Binds to 127.0.0.1. POSTs require application/json (blocks cross-site
form posts) and the Host header must be local (blocks DNS rebinding).
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .agent import SUGGESTED, Agent
from .engine import Engine

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "ui" / "index.html"
MAX_BODY = 64 * 1024


def make_handler(engine: Engine, agent: Agent, port: int):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class H(BaseHTTPRequestHandler):
        server_version = "readiness-ui"

        def log_message(self, fmt, *args):  # quiet
            pass

        # ---- plumbing ----
        def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj, default=str).encode())

        def _host_ok(self) -> bool:
            return self.headers.get("Host", "") in allowed_hosts

        def _body(self) -> dict:
            if "application/json" not in self.headers.get("Content-Type", ""):
                raise ValueError("Content-Type must be application/json")
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("request too large")
            return json.loads(self.rfile.read(n) or b"{}")

        # ---- routes ----
        def do_GET(self):
            if not self._host_ok():
                return self._json({"error": "bad host"}, 403)
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    return self._send(200, UI.read_bytes(), "text/html")
                if u.path == "/api/state":
                    return self._json(engine.state())
                if u.path == "/api/tables":
                    return self._json(engine.tables(q.get("source", ""), q.get("layer", ""), q.get("q", ""), q.get("prod", "")))
                if u.path == "/api/recon":
                    return self._json(engine.recon_rows(q.get("classification", ""), q.get("source", ""), q.get("q", "")))
                if u.path == "/api/suggestions":
                    return self._json({"suggestions": SUGGESTED})
                return self._json({"error": "not found"}, 404)
            except Exception as e:  # surface, never crash the server
                return self._json({"error": str(e)}, 500)

        def do_POST(self):
            if not self._host_ok():
                return self._json({"error": "bad host"}, 403)
            try:
                b = self._body()
                if self.path == "/api/ask":
                    return self._json(agent.ask(str(b.get("question", ""))))
                if self.path == "/api/triage":
                    names = b.get("names", [])
                    if not isinstance(names, list):
                        raise ValueError("names must be a list")
                    return self._json(engine.triage([str(n) for n in names]))
                if self.path == "/api/rubric":
                    d = engine.set_thresholds(int(b["fresh_window_days"]), int(b["recurring_min_commit_days_30d"]))
                    return self._json({"delta": d, "state": engine.state()})
                if self.path == "/api/rubric/save":
                    engine.save_thresholds()
                    return self._json({"saved": True, "state": engine.state()})
                if self.path == "/api/reload":
                    engine.reload()
                    return self._json({"state": engine.state()})
                return self._json({"error": "not found"}, 404)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                return self._json({"error": str(e)}, 400)
            except Exception as e:
                return self._json({"error": str(e)}, 500)

    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    engine = Engine(ROOT)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(engine, Agent(engine), a.port))
    print(f"Data-readiness UI: http://127.0.0.1:{a.port}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
