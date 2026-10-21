# FlowMetrics — Supply Chain & Customer Retention BI

An independent operational analytics project with validated Python ETL, incremental batch manifests, SQL reporting marts, customer inactivity/cohort analysis, and an interactive browser dashboard.

**180,519 order lines → 65,752 distinct orders · 28,965 completed orders · 5 reporting checks**

![FlowMetrics dashboard](dashboard/preview.png)

## Business problem

Operations teams need to diagnose late delivery without inflating order counts by the number of line items. Customer teams need a precise definition of inactivity and a view of repeat purchase behavior. Finance needs sales totals that reconcile to source records.

This project provides one reproducible system covering those questions. Read the [project brief](docs/PROJECT_BRIEF.md), [measured executive summary and conclusion](reports/executive_summary.md), and [data contracts](docs/DATA_DICTIONARY.md).

## Working dashboard

Open `dashboard/index.html` directly; its public aggregate data is included. No API key, database or paid BI license is required to view it.

```sh
python -m http.server 8766 --directory dashboard
```

Visit http://localhost:8766. The dashboard includes:

- Market and shipping-mode delivery filters.
- Completed-order count, late-delivery rate, net sales and recorded-profit cards.
- Shipping service comparisons, monthly sales and downloadable segment CSV.
- Editable hypothetical avoidable-cost scenario.
- Historical customer recency groups and mature 90-day inactivity labels.
- Cohort retention heatmap that distinguishes 0% from unobserved outcomes.
- Source fingerprint, ingestion status and reconciliation results.

Monthly/customer/cohort sections are full-portfolio and explicitly labeled independent of delivery filters.

## Architecture

```mermaid
flowchart LR
    A[Checksum-verified DataCo CSV] --> B[Whitelisted schema and validation]
    B --> C[Transactional item-key upsert]
    C --> D[SQLite or PostgreSQL]
    D --> E[Order-grain SQL views]
    D --> F[Checksum ingestion manifest]
    E --> G[Customer snapshots and cohorts]
    E --> H[Reconciliation gates]
    G --> H
    H --> I[Aggregate dashboard]
    H --> J[Local CSV and Power BI handoff]
    H --> K[Executive summary]
```

## Quick start

Python 3.11+; developed with Python 3.12. The first build downloads approximately 96 MB of historical public data. Subsequent builds reuse the verified archive.

```sh
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
operations-bi build
pytest -q
ruff check .
```

Run commands from the repository root. The default database is SQLite, so Docker is unnecessary for a working local project.

```sh
# Historical customer snapshot
operations-bi build --as-of 2017-06-30
# A compatible new/corrected order-line batch
operations-bi build --source data/raw/corrected_batch.csv
```

Outputs: ignored raw source and local database/CSVs; committed aggregate dashboard data and nonpersonal validation/report artifacts. No raw customer records are uploaded to GitHub.

## PostgreSQL option

PowerShell example; Compose uses port 5433 to avoid collision with Project 1:

```powershell
$env:POSTGRES_PASSWORD = 'choose_a_local_demo_password'
docker compose up -d --wait
$env:DATABASE_URL = 'postgresql+psycopg://operations:choose_a_local_demo_password@localhost:5433/operations'
operations-bi build
```

Percent-encode password characters in URLs where needed. Keep credentials in your shell or secret manager; never commit them.

Reporting SQL demonstrates CTEs, market-partitioned `DENSE_RANK`, `LAG`, rolling windows, conditional aggregation and grain-safe counts. See [sql/marts.sql](sql/marts.sql) and [investigation queries](sql/investigation.sql).

## Enterprise engineering evidence

| Concern | Implemented behavior |
|---|---|
| Reproducibility | Source MD5 verification plus SHA-256 lineage |
| Privacy | Field whitelist excludes source personal/contact fields |
| Idempotency | Identical batch checksum skips database mutation |
| Corrections | Upsert by order-item primary key |
| Consistency | Merged order-level attributes validated before commit |
| Failure recovery | Transaction rollback and documented replay |
| Data grain | Line inputs separated from order-grain reporting |
| Time integrity | Historical-only customer features; censored outcomes remain missing |
| Quality | Five real-data reconciliation checks and meaningful automated tests |
| Automation | One-command pipeline, scheduler entry script, replay workflow template |

This is a single-writer portfolio system. It does not claim a live ERP feed, Kubernetes deployment, installed scheduler, production alerts, causal churn uplift or a deployed ML model.

## Measured results and recommendations

- 180,519 source lines reconcile to 65,752 distinct orders.
- 28,965 orders satisfy the explicit COMPLETE/CLOSED population.
- The completed-order late-delivery rate is **57.42%**.
- Completed-order net sales total **14,476,738.58 dataset monetary units**. Source currency is unverified.
- Some First Class market groups show 100% late rates. Treat this as a reason to inspect source definitions and service promise settings, not proof that an intervention will fix them.

Recommended next decisions: investigate both late rates and absolute late-order counts; verify the source profit-field semantics; validate customer-ID continuity before using inactivity as a business churn measure; design a randomized retention experiment before attributing campaign benefit.

## ROI methodology

The dashboard calculates **late orders × assumed preventable share × assumed unit cost**. This is a scenario only. Efficiency ROI requires measured operator minutes before/after automation; script duration is recorded but is not a labor-savings estimate. No realized savings are claimed.

## Tests and CI

Local result: **20 tests passed**, with the dedicated PostgreSQL test skipped locally when TEST_DATABASE_URL is absent. Lint passes. Tests cover invalid inputs, personal-field exclusion, order grain, repeated batches, corrected upserts, rollback, point-in-time features, censored labels, cohort maturity and an end-to-end replay.

GitHub Actions runs the same tests with a PostgreSQL 16 service. Check the Actions tab for the actual remote result. TEST_DATABASE_URL must point to a disposable dedicated database; its integration test resets project tables there.

## Power BI and automation

[Power BI setup](bi/POWER_BI_SETUP.md) and [DAX measures](bi/measures.dax) describe the native report build. No `.pbix` is included. The browser dashboard is complete and runnable.

[Runbook](docs/RUNBOOK.md) explains batch corrections, backfills, logging, scheduling and recovery. `scripts/run_daily.ps1` provides a local scheduler entry point; `automation/replay.yml` is a manual historical ETL replay template. No scheduler is installed automatically.

## Repository structure

```text
src/operations/        source validation, transactional warehouse, retention and CLI
sql/                   reporting views and investigation queries
dashboard/             browser application and aggregate data
bi/                    Power BI setup and DAX
tests/                 unit, warehouse, temporal and end-to-end tests
reports/               measured executive summary and reconciliation
docs/                  business brief, contracts, runbook, interview guide
scripts/               local scheduler entry point
automation/            replay workflow template
.github/workflows/     publication bootstrap and CI
```

## Conclusion

FlowMetrics demonstrates reliable operational reporting and careful customer analysis, with auditable numbers and reproducible code. The primary result is trustworthy analytical infrastructure and clearly scoped recommendations, not an unsupported claim of prevented delays or reduced churn.

## Dataset and licensing

Constante, F.; Silva, F.; Pereira, A. (2019), *DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS*, Mendeley Data V5, [DOI 10.17632/8gx2fvg2k6.5](https://doi.org/10.17632/8gx2fvg2k6.5), CC BY 4.0. Download mirror: [Zenodo record 11112645](https://zenodo.org/records/11112645).

Transformations include sanitization, order-level aggregation, temporal snapshots, derived cohorts and aggregate dashboard exports. Dataset and derived data retain attribution obligations; project code is MIT licensed. No affiliation with DataCo or a target employer is implied.
