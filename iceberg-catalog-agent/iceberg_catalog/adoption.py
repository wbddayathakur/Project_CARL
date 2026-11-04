"""Turn a catalog into the handful of numbers that move Iceberg/Cube adoption.

A catalog listing is a reference document; nobody reads one voluntarily. What
gets a platform adopted is a weekly number that somebody is accountable for, so
the agent computes six and republishes them next to the listing.

The metrics are chosen so that each one has an obvious owner and an obvious
next action. "1,128 tables exist" is trivia. "30 of 1,128 tables have a
catalogued consumer" is a statement that either the lineage inventory is
incomplete or three quarters of the lakehouse is being built for nobody, and
somebody has to go find out which.

`reuse_rate` is the only metric that cannot be derived from the catalog. It
needs the intake log, because it measures the thing the intake form exists to
change: what share of incoming demand was answered with something that already
existed instead of a new build. Without the log it is reported as unknown
rather than guessed.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Sequence

from .classify import (
    TIER_CERTIFIED,
    TIER_PRODUCTION,
    TIER_SANDBOX,
    TIER_STALE,
    TIER_UNDOCUMENTED,
)
from .model import Catalog


@dataclass
class Metric:
    """One published number, with the arithmetic left visible.

    `numerator`/`denominator` are kept rather than just the ratio because the
    first question anyone asks about a governance metric is "out of what", and
    a percentage on its own invites argument.
    """

    key: str
    label: str
    numerator: int
    denominator: int
    question: str
    owner: Optional[str] = None
    target_pct: Optional[float] = None

    @property
    def pct(self) -> float:
        return 0.0 if not self.denominator else 100.0 * self.numerator / self.denominator

    @property
    def meets_target(self) -> Optional[bool]:
        if self.target_pct is None:
            return None
        return self.pct >= self.target_pct

    def to_dict(self) -> dict:
        data = asdict(self)
        data["pct"] = round(self.pct, 1)
        data["meets_target"] = self.meets_target
        return data


@dataclass
class AdoptionReport:
    generated_at: dt.datetime
    metrics: list = field(default_factory=list)
    tier_counts: dict = field(default_factory=dict)
    layer_counts: dict = field(default_factory=dict)
    domain_counts: dict = field(default_factory=dict)
    env_counts: dict = field(default_factory=dict)
    headlines: list = field(default_factory=list)
    reuse: Optional[dict] = None

    def metric(self, key: str) -> Optional[Metric]:
        return next((m for m in self.metrics if m.key == key), None)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
            "tier_counts": self.tier_counts,
            "layer_counts": self.layer_counts,
            "domain_counts": self.domain_counts,
            "env_counts": self.env_counts,
            "headlines": self.headlines,
            "reuse": self.reuse,
        }


def analyse(
    catalog: Catalog,
    *,
    intake_log: Optional[Sequence[dict]] = None,
    targets: Optional[dict] = None,
) -> AdoptionReport:
    targets = targets or {}
    report = AdoptionReport(generated_at=catalog.generated_at)

    tables = catalog.tables
    report.tier_counts = _count(t.tier for t in tables)
    report.layer_counts = _count(t.layer for t in tables)
    report.domain_counts = _count(t.domain for t in tables)
    report.env_counts = {
        account.environment: {
            "account": account.account_id,
            "in_catalog": account.tables_in_catalog,
            "refreshed": account.tables_refreshed,
            "databases": account.databases_with_tables,
        }
        for account in catalog.accounts
    }

    # The denominator for most metrics is "tables a consumer could plausibly
    # use" — prod, not scratch. Counting dev sprawl in the denominator would
    # make every metric look worse each time an engineer runs an experiment.
    addressable = [t for t in tables if t.in_prod and t.tier != TIER_SANDBOX]
    gold_prod = [t for t in addressable if t.layer == "gold"]
    cube_backed = {v.source_table for v in catalog.cube_views if v.source_table}

    report.metrics = [
        Metric(
            key="product_coverage",
            label="Prod tables published as a data product",
            numerator=sum(1 for t in addressable if t.tier == TIER_CERTIFIED),
            denominator=len(addressable),
            question="If someone asks what's available, how much of prod can we actually describe?",
            owner="Data Product Management",
            target_pct=targets.get("product_coverage"),
        ),
        Metric(
            key="semantic_coverage",
            label="Prod Gold tables exposed through a Cube view",
            numerator=sum(1 for t in gold_prod if t.fqn in cube_backed),
            denominator=len(gold_prod),
            question="Can a business user reach this without writing Athena SQL?",
            owner="Semantic Layer",
            target_pct=targets.get("semantic_coverage"),
        ),
        Metric(
            key="consumer_visibility",
            label="Tables with a known downstream consumer",
            numerator=sum(1 for t in tables if t.consumers),
            denominator=len(tables),
            question="Are we building things anyone reads, or can we simply not see the reads?",
            owner="Data Engineering",
            target_pct=targets.get("consumer_visibility"),
        ),
        Metric(
            key="producer_visibility",
            label="Tables with a catalogued producer job",
            numerator=sum(1 for t in tables if t.producers),
            denominator=len(tables),
            question="Do we know what writes this, and can we page someone when it stops?",
            owner="Data Engineering",
            target_pct=targets.get("producer_visibility"),
        ),
        Metric(
            key="prod_freshness",
            label="Prod tables refreshed inside the window",
            numerator=sum(1 for t in addressable if t.tier != TIER_STALE),
            denominator=len(addressable),
            question="Is what we published still true this week?",
            owner="Data Engineering",
            target_pct=targets.get("prod_freshness"),
        ),
        Metric(
            key="promotion_rate",
            label="Distinct tables that reached prod",
            numerator=sum(1 for t in tables if t.in_prod),
            denominator=len(tables),
            question="How much of what we build is still sitting in lower environments?",
            owner="Platform",
            target_pct=targets.get("promotion_rate"),
        ),
    ]

    if intake_log is not None:
        report.reuse = _reuse(intake_log)
        report.metrics.append(
            Metric(
                key="reuse_rate",
                label="Intake requests answered by something that already existed",
                numerator=report.reuse["reused"],
                denominator=report.reuse["total"],
                question="Is the catalog deflecting new builds, which is the only reason it exists?",
                owner="Data Product Management",
                target_pct=targets.get("reuse_rate"),
            )
        )

    report.headlines = _headlines(catalog, report, addressable)
    return report


def _reuse(intake_log: Sequence[dict]) -> dict:
    """Summarise the intake log.

    Expects rows with a `resolution` field. Anything starting with "reuse" or
    equal to "existing" counts as deflected demand.
    """
    total = len(intake_log)
    reused = sum(
        1
        for row in intake_log
        if str(row.get("resolution", "")).lower().startswith(("reuse", "existing"))
    )
    new_build = sum(
        1 for row in intake_log if str(row.get("resolution", "")).lower().startswith("new")
    )
    return {
        "total": total,
        "reused": reused,
        "new_build": new_build,
        "unresolved": total - reused - new_build,
    }


def _headlines(catalog: Catalog, report: AdoptionReport, addressable: list) -> list:
    """Three sentences a reader should leave with, stated as findings."""
    lines = []

    consumer = report.metric("consumer_visibility")
    if consumer and consumer.denominator:
        lines.append(
            f"{consumer.numerator} of {consumer.denominator} tables have a catalogued "
            f"consumer ({consumer.pct:.0f}%). Either the lineage inventory only sees part "
            f"of the estate, or most of what is being refreshed has no named reader."
        )

    dev = report.env_counts.get("dev", {}).get("in_catalog", 0)
    prod = report.env_counts.get("prod", {}).get("in_catalog", 0)
    if dev and prod:
        lines.append(
            f"Dev holds {dev} tables against {prod} in prod, a {dev / prod:.1f}x spread. "
            f"That gap is where duplicate builds hide, and it is the first thing an "
            f"intake reviewer should search before approving new work."
        )

    undocumented = report.tier_counts.get(TIER_UNDOCUMENTED, 0)
    if undocumented:
        lines.append(
            f"{undocumented} tables are refreshing on a schedule that no catalogued job "
            f"claims to own. They are running, but nobody can be paged when they stop."
        )

    return lines


def _count(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
