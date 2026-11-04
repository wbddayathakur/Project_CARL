"""Tests for the UI backend: engine, triage, question routing, gate and HTTP guards.
They run against the real data in data/, so they check behaviour, not invented numbers."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from readiness.agent import Agent
from readiness.engine import Engine, gate
from readiness.server import make_handler

ROOT = Path(__file__).resolve().parent.parent


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = Engine(ROOT)
        cls.a = Agent(cls.e)

    # ---- gate ----
    def test_gate_never_clears_with_unverified_criteria(self):
        for r in self.e.state()["rows"]:
            if any(c["status"] == "unverified" for c in r["criteria"]):
                self.assertNotEqual(r["gate"]["verdict"], "CLEARED")

    def test_gate_blocks_anything_not_in_prod(self):
        for r in self.e.state()["rows"]:
            if r["stage"] in ("dev only", "not present"):
                self.assertEqual(r["gate"]["verdict"], "BLOCK")

    def test_gate_can_clear_only_when_all_pass(self):
        row = {"stage": "in prod", "counts": {"in_prod": 1, "tables": 1},
               "criteria": [{"id": "B1", "status": "pass"}, {"id": "B2", "status": "pass"}]}
        self.assertEqual(gate(row)["verdict"], "CLEARED")  # logic fixture only

    # ---- triage ----
    def test_triage_known_table_in_prod(self):
        r = self.e.triage_one("DCI_RATECARD_HEADER")
        self.assertEqual(r["code"], "in_prod")

    def test_triage_schema_dot_table(self):
        self.assertEqual(self.e.triage_one("DEALBLDR.DCI_RATECLASS")["code"], "in_prod")

    def test_triage_requested_but_missing(self):
        self.assertEqual(self.e.triage_one("D_BREAK")["code"], "requested_no_table")

    def test_triage_unknown_is_new_request(self):
        self.assertEqual(self.e.triage_one("zzz_nothing_like_this_xyz")["code"], "new_request")

    def test_triage_invalid(self):
        self.assertEqual(self.e.triage_one("   ")["code"], "invalid")
        self.assertEqual(self.e.triage_one("x" * 300)["code"], "invalid")

    def test_triage_limits_batch(self):
        self.assertEqual(len(self.e.triage(["a_b"] * 500)["results"]), 100)

    # ---- thresholds ----
    def test_threshold_validation_and_effect(self):
        with self.assertRaises(ValueError):
            self.e.set_thresholds(0, 2)
        base = self.e.totals()["stale_in_prod"]
        try:
            d = self.e.set_thresholds(365, 2)
            self.assertLessEqual(d["after"]["stale_in_prod"], base)
        finally:
            self.e.set_thresholds(*self.e.baseline)
        self.assertEqual(self.e.totals()["stale_in_prod"], base)

    # ---- question routing ----
    def tools(self, q):
        return [t["tool"] for t in self.a.ask(q)["tools"]]

    def test_routing(self):
        self.assertEqual(self.tools("Give me an overview"), ["get_state"])
        self.assertEqual(self.tools("Which sources are safe for an agent to use?"), ["gate_by_source_layer"])
        self.assertIn("list_blocked", self.tools("What is blocked?"))
        self.assertIn("readiness_by_source", self.tools("Is FreeWheel ready?"))
        self.assertIn("evidence_gaps", self.tools("What can't you measure?"))
        self.assertIn("input_freshness", self.tools("How fresh is the data?"))
        self.assertIn("triage_table", self.tools("Look up DCI_RATECARD_HEADER"))
        self.assertIn("dev_only_groups", self.tools("Which tables are dev only?"))

    def test_agent_does_not_match_age_inside_agent(self):
        self.assertNotIn("input_freshness", self.tools("safe for an agent"))

    def test_unknown_question_falls_back_and_says_so(self):
        a = self.a.ask("blah blah")
        self.assertIn("not sure", a["headline"])

    def test_every_answer_cites_its_tools(self):
        for q in ["overview", "what is blocked", "is ideal ready", "jira mismatches", "gaps", "fresh", "recurring", "dev only"]:
            self.assertTrue(self.a.ask(q)["tools"], q)

    # ---- drill-down ----
    def test_tables_filters(self):
        j = self.e.tables(source="FreeWheel", layer="bronze")
        self.assertTrue(all(r["layer"] == "bronze" and r["source"] == "FreeWheel" for r in j["rows"]))
        self.assertEqual(self.e.tables(source="FreeWheel", layer="bronze", prod="yes")["total"], 0)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        e = Engine(ROOT)
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(e, Agent(e), 0))
        cls.port = cls.srv.server_address[1]
        # allowed hosts are keyed on the port given to make_handler, so rebuild with the real one
        cls.srv.RequestHandlerClass = make_handler(e, Agent(e), cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, path, body=None, headers=None):
        h = {"Content-Type": "application/json", **(headers or {})}
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=None if body is None else json.dumps(body).encode(), headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, err.read()

    def test_index_and_state(self):
        code, body = self.req("/")
        self.assertEqual(code, 200)
        self.assertIn(b"CARL data readiness", body)
        code, body = self.req("/api/state")
        self.assertEqual(code, 200)
        self.assertIn("totals", json.loads(body))

    def test_ask_roundtrip(self):
        code, body = self.req("/api/ask", {"question": "What is blocked?"})
        self.assertEqual(code, 200)
        self.assertIn("headline", json.loads(body))

    def test_bad_host_rejected(self):
        code, _ = self.req("/api/state", headers={"Host": "evil.example"})
        self.assertEqual(code, 403)

    def test_post_requires_json_content_type(self):
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/ask", data=b"question=x", headers={"Content-Type": "text/plain"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(r)
        self.assertEqual(cm.exception.code, 400)

    def test_bad_threshold_is_400_not_500(self):
        code, _ = self.req("/api/rubric", {"fresh_window_days": 0, "recurring_min_commit_days_30d": 2})
        self.assertEqual(code, 400)

    def test_unknown_route_404(self):
        self.assertEqual(self.req("/api/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
