"""Tests. Section A checks rules on tiny hand-written cases (labelled fixtures, not data we
report). Section B checks invariants of the real run against the real inputs."""
import unittest
from datetime import date
from pathlib import Path

from readiness.inputs import Table, in_scope, load, source_for
from readiness.match import candidates, expected_layer, _classify, _name_matches
from readiness.match import reconcile
from readiness.score import score

ROOT = Path(__file__).resolve().parent.parent


def T(**kw):
    base = dict(db="d", name="t", layer="bronze", in_dev=True, in_prod=False, dev_updated=None, prod_updated=None)
    base.update(kw)
    return Table(**base)


class RuleTests(unittest.TestCase):  # Section A
    def test_candidate_parsing(self):
        self.assertEqual(candidates("Ingest Freewheel D_BREAK to Bronze"), ["d_break"])
        self.assertEqual(candidates("Ingest DEALBLDR.DCI_RATECLASS -  (Production)"), ["dealbldr_dci_rateclass", "dci_rateclass"])
        self.assertEqual(candidates("Bronze Ingestion — video_ad_api_agency"), ["video_ad_api_agency"])
        self.assertEqual(candidates("Get DCI_ORDER_HEADER table available in bronze"), ["dci_order_header"])
        self.assertEqual(candidates("Design Finance Forecast Ingest Feed (Digital+Linear)"), [])

    def test_layer_detection(self):
        self.assertEqual(expected_layer("SILVER.DIM_X transformation"), "silver")
        self.assertIsNone(expected_layer("Ingest DEALBLDR.X"))
        self.assertIsNone(expected_layer("Bronze to Silver pipeline"))

    def test_name_match_is_suffix_on_underscore_boundary(self):
        self.assertTrue(_name_matches("ideal_dci_acct", "dci_acct"))
        self.assertFalse(_name_matches("ideal_xdci_acct", "dci_acct"))

    def test_classification(self):
        d = date(2026, 10, 7)
        self.assertEqual(_classify("done", "Done", [T(in_prod=True)], None, d), "done_and_in_prod")
        self.assertEqual(_classify("done", "Done", [T()], None, d), "done_but_dev_only")
        self.assertEqual(_classify("done", "Done", [], date(2026, 10, 10), d), "done_after_snapshot")
        self.assertEqual(_classify("done", "Done", [], date(2026, 9, 1), d), "done_no_table_found")
        self.assertEqual(_classify("indeterminate", "Blocked", [T(in_prod=True)], None, d), "live_but_open")
        self.assertEqual(_classify("indeterminate", "In Testing", [], None, d), "testing_no_table")
        self.assertEqual(_classify("new", "To Do", [], None, d), "open_no_table")

    def test_scope_rules(self):
        self.assertTrue(in_scope(T()))
        self.assertFalse(in_scope(T(noise=True)))
        self.assertFalse(in_scope(T(sandbox_db=True)))
        self.assertFalse(in_scope(T(layer="unknown")))

    def test_source_fallback_strips_layer_suffixes(self):
        cfg = {"sources": []}
        self.assertEqual(source_for("adsales_iceberg_silver_dev", "x", cfg), "adsales_iceberg")


class RealDataTests(unittest.TestCase):  # Section B
    @classmethod
    def setUpClass(cls):
        cls.inp = load(ROOT / "data", ROOT / "config" / "rubric.json")
        cls.recon = reconcile(cls.inp)
        cls.sc = score(cls.inp, cls.recon)

    def test_every_catalog_table_is_scored_or_excluded(self):
        scored = sum(r["counts"]["tables"] for r in self.sc["rows"])
        self.assertEqual(scored + sum(self.sc["excluded"].values()), len(self.inp.tables))

    def test_counts_are_consistent(self):
        for r in self.sc["rows"]:
            c = r["counts"]
            self.assertLessEqual(c["in_dev"], c["tables"])
            self.assertLessEqual(c["in_prod"], c["tables"])
            self.assertLessEqual(c["fresh_in_prod"], c["in_prod"])
            self.assertLessEqual(c["prod_recurring"], c["prod_with_history"])

    def test_unverifiable_criteria_are_never_pass_or_fail(self):
        for r in self.sc["rows"]:
            for c in r["criteria"]:
                if c["evidence"] == "none":
                    self.assertEqual(c["status"], "unverified")

    def test_all_jira_stories_accounted_for(self):
        m = self.recon
        self.assertEqual(m["reconciled"] + len(m["unparsed"]) + len(m["no_layer"]), m["stories_total"])

    def test_no_cross_source_match_counted(self):
        for r in self.recon["recons"]:
            if r.confidence != "none" and r.source != "unmapped":
                self.assertTrue(r.tables)

    def test_load_history_fully_joined_to_inventory(self):
        self.assertEqual(self.inp.history_unmatched, 0)


if __name__ == "__main__":
    unittest.main()
