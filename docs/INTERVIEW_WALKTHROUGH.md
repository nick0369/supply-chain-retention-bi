# Interview and portfolio guide

## 60-second summary

I built a supply-chain and customer-retention BI system on the public DataCo dataset. The pipeline validates and sanitizes order-line records, then loads them transactionally into SQLite or PostgreSQL with checksum tracking and corrected-record upserts. I separate line and order grains to avoid inflated delivery counts. SQL views provide market/service metrics and rolling trends. Customer snapshots use historical-only features and explicit 90-day inactivity labels, while cohorts distinguish observed zero activity from incomplete follow-up. The dashboard presents measured findings and editable hypothetical savings assumptions.

## Demonstrate

1. Show source fingerprint and ignored raw-data directory.
2. Explain 180,519 lines versus 65,752 orders.
3. Rerun ingestion and show `already_loaded` with unchanged business totals.
4. Show a unit test for corrected-line upsert and another for transaction rollback.
5. Explain why COMPLETE/CLOSED is an explicit KPI population rather than an implicit filter.
6. Show a customer snapshot before follow-up completes; labels remain missing.
7. Explain why a 100% late rate in one service may be a dataset/promise-definition artifact.
8. Distinguish customer inactivity, churn prediction and causal campaign uplift.

## Honest résumé bullets

- Built a reproducible operational analytics pipeline covering 180,519 order lines and 65,752 distinct orders using modular Python, SQL reporting views and transactional batch manifests.
- Prevented duplicate reporting and supported corrected records by implementing order-item upserts, source checksum tracking and tests for rollback and order-grain consistency.
- Developed an interactive delivery and customer-inactivity dashboard with explicit 90-day observation windows, cohort maturity rules and auditable executive recommendations.

Only add PostgreSQL execution or CI success after the relevant run succeeds. No delivered revenue increase, avoided cost, client employment or native Power BI file is implied.
