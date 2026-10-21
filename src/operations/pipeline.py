"""Orchestrate reproducible ingestion, marts, quality checks, exports and business insights."""
from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from operations.retention import cohort_retention, snapshot
from operations.source import SOURCE_URL, download, fingerprint, read, validate
from operations.warehouse import connect, load, query

LOG = logging.getLogger(__name__)


def records(frame: pd.DataFrame):
    return json.loads(frame.to_json(orient="records", date_format="iso", double_precision=10))


def run(root: Path, source_path: Path | None = None, database_url: str | None = None,
        as_of: str | None = None, force: bool = False) -> dict:
    started = time.perf_counter()
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    source_path = source_path or download(root)
    digest = fingerprint(source_path)
    frame = validate(read(source_path))
    engine = connect(database_url or "sqlite:///" + (processed / "operations.db").as_posix())
    try:
        ingestion = load(frame, digest, engine, root, force)
        orders = query(engine, "SELECT * FROM fact_orders")
        counts = query(engine, "SELECT COUNT(*) AS n, SUM(net_sales) AS net_sales FROM order_lines").iloc[0]
        observed = pd.to_datetime(orders.ordered_at).max().normalize()
        # A fixed one-year lookback leaves a full 90-day label window and a later validation period.
        as_of = as_of or (observed-pd.Timedelta(days=365)).strftime("%Y-%m-%d")
        customers, window = snapshot(orders, as_of, observed.strftime("%Y-%m-%d"))
        checks = [
            {"name": "order_primary_key", "passed": bool(orders.order_id.is_unique)},
            {"name": "line_count_reconciled", "passed": int(orders.line_count.sum()) == int(counts.n)},
            {"name": "net_sales_reconciled", "passed": abs(float(orders.net_sales.sum())-float(counts.net_sales))<0.01},
            {"name": "customer_snapshot_unique", "passed": bool(customers.customer_id.is_unique)},
            {"name": "nonnegative_recency", "passed": bool(customers.recency_days.ge(0).all())},
        ]
        if not all(check["passed"] for check in checks):
            raise ValueError(f"Reconciliation failure: {checks}")
        orders.to_csv(processed / "orders.csv", index=False)
        customers.to_csv(processed / "customer_snapshot.csv", index=False)
        operations = query(engine, "SELECT * FROM delivery_by_mode ORDER BY market, late_rate DESC")
        monthly = query(engine, "SELECT * FROM monthly_operations ORDER BY month")
        grouped = customers.groupby("segment").agg(customers=("customer_id", "count"),
            historical_sales=("monetary", "sum"), avg_recency=("recency_days", "mean"))
        retention = []
        for name, row in grouped.iterrows():
            subset = customers.loc[customers.segment.eq(name)]
            retention.append({"segment": name, **row.to_dict(), "future_inactive_rate":
                              float(subset.inactive_next_90d.mean()) if window["label_mature"] else None})
        complete = orders.loc[orders.completed.eq(1)]
        prior_cutoff = observed-pd.Timedelta(days=90)
        dated = complete.assign(date=pd.to_datetime(complete.ordered_at).dt.normalize())
        prior_customers = set(dated.loc[dated.date <= prior_cutoff, "customer_id"])
        recent_customers = set(dated.loc[dated.date > prior_cutoff, "customer_id"])
        overlap = len(prior_customers & recent_customers)
        warnings = []
        if prior_customers and recent_customers and overlap == 0:
            warnings.append("No completed-purchase customer IDs overlap the final 90 days and earlier history. Verify identifier continuity and source coverage before treating recent inactivity as business churn.")
        report = {"built_at_utc": datetime.now(UTC).isoformat(), "source_url": SOURCE_URL,
            "source_sha256": digest, "ingestion": ingestion, "line_count": int(counts.n),
            "orders": len(orders), "completed_orders": len(complete),
            "eligible_statuses": ["COMPLETE", "CLOSED"], "observation_end": observed.strftime("%Y-%m-%d"),
            "checks": checks, "duration_seconds": round(time.perf_counter()-started, 3),
            "database_dialect": engine.dialect.name, "window": window,
            "quality_warnings": warnings, "final_90d_repeat_customer_overlap": overlap}
        payload = {"report": report, "delivery": records(operations), "monthly": records(monthly),
            "retention": retention, "cohorts": cohort_retention(orders, observed.strftime("%Y-%m-%d")),
            "summary": {"net_sales": float(complete.net_sales.sum()),
                "recorded_profit": float(complete.recorded_profit.sum()),
                "late_rate": float(complete.late_flag.mean()), "customers": int(complete.customer_id.nunique())}}
        # Data is published only after all reporting checks pass. No PII or customer IDs in dashboard.
        reports = root / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (root / "dashboard/data.js").write_text("window.OPERATIONS = " + json.dumps(payload, allow_nan=False) + ";", encoding="utf-8")
        (reports / "executive_summary.md").write_text(executive_summary(payload), encoding="utf-8")
        with engine.begin() as connection:
            # Audit read is deliberately explicit: manifest row count is not a business KPI.
            batches = connection.execute(text("SELECT COUNT(*) FROM ingestion_batches")).scalar()
        LOG.info(json.dumps({"event": "pipeline_complete", "batches": batches, **report}))
        return report
    finally:
        engine.dispose()


def executive_summary(data: dict) -> str:
    report, summary = data["report"], data["summary"]
    worst = sorted(data["delivery"], key=lambda row: row["late_rate"], reverse=True)[:3]
    details = "\n".join(f"- {r['market']} / {r['shipping_mode']}: {r['late_rate']:.2%} late across {r['completed_orders']:,} completed orders." for r in worst)
    return f"""# Executive summary — measured historical results

## Problem
Operations needs a single reconciled view of order-level delivery performance and a documented customer inactivity definition.

## Summary
Processed {report['line_count']:,} order lines into {report['orders']:,} distinct orders. COMPLETE/CLOSED orders: {report['completed_orders']:,}. Completed-order late rate: {summary['late_rate']:.2%}. Net sales: {summary['net_sales']:,.2f} dataset monetary units. Currency is unverified; do not label INR/USD.

## Delivery findings
{details}

## Customer analysis
Snapshot: {report['window']['as_of']}; observed through: {report['observation_end']}. Inactivity means no completed purchase in the following 90 days; label maturity: {report['window']['label_mature']}. This is descriptive, not a prediction model.

Data coverage warning: {' '.join(report['quality_warnings']) or 'No zero-overlap warning triggered.'}

## Recommendations
Investigate shipping-mode promise settings and fulfillment bottlenecks in the listed groups; compare absolute late counts, order sizes and service costs before changing a promise. Use RFM/inactivity groups to design a controlled retention experiment. Validate customer-ID continuity and observation completeness first.

## Conclusion
The system produces auditable order metrics and repeatable customer cohorts. No causal churn reduction, delivery improvement or realized ROI has been demonstrated. Apparent retention patterns may reflect dataset construction or incomplete capture rather than business behavior.
"""
