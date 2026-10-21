# ETL and operational runbook

## Commands

```sh
operations-bi build
operations-bi build --as-of 2017-06-30
operations-bi build --source data/raw/corrected_batch.csv
operations-bi build --source data/raw/corrected_batch.csv --force
```

Run from the repository root. Set DATABASE_URL for PostgreSQL; otherwise SQLite persists at data/processed/operations.db. Default source download is checksum-verified. A custom source file must follow the DataCo field contract; it is validated but cannot use the full-source checksum. `--force` reapplies a known file, not a destructive reset.

## Reliability design

- Streamed download with three attempts for transient connection errors. Temporary downloads do not replace validated cached sources.
- Schema whitelist and explicit validations; invalid input fails closed instead of silently dropping records.
- Order-item primary key, checksum manifest and batch upserts.
- Validate merged order-level consistency within the database transaction; conflicts roll back the batch and manifest.
- Reporting views separate order grain from lines.
- Quality gates run before dashboard publication.
- No deleted records are inferred from a missing item in an incremental batch. Deletions require a separate governed process.
- Single writer only; serialize scheduled runs. Order-line corrections should be supplied consistently for all affected lines when order-level attributes change.

## Scheduling

`scripts/run_daily.ps1` is an executable scheduler entry point with timestamped local logs and failure exit propagation. After activating the environment, test it manually. A Windows Task Scheduler job can run the script with the project working directory and the environment's PATH. A scheduler is not installed on the user's machine by this project.

`automation/replay.yml` is a GitHub Actions template for a manual historical-source replay and downloadable report artifacts. Copy it to `.github/workflows/refresh.yml` to enable. It does not claim new daily business data exists.

## Failures and recovery

On schema/checksum failure, preserve the raw source for inspection. Never publish raw rows. On order conflicts, fix all affected line records upstream and replay the corrected batch. On database failure, ingestion rolls back. Exports and database commits are separate; rerun the complete build after export failure. Manifest status `already_loaded` still regenerates reports.

Local internal CSVs and SQLite data are ignored by Git. The dashboard contains aggregates only. Separate source extraction, reporting read credentials and secret management for a real deployment.

## Tests

`pytest -q` covers invalid source fields, privacy whitelist, order grain, corrected batches, rollback, mature/censored inactivity and zero-versus-unobserved cohort behavior. Set TEST_DATABASE_URL only to a disposable dedicated PostgreSQL database: its integration test resets project test tables.

## Backfills and timestamps

`--as-of` rebuilds a customer snapshot at a chosen date using only earlier purchase features. The dataset contains final order statuses, so it is not a full event-time reconstruction of historical status changes. Default reference cutoff = observed max order date minus 365 days, leaving a full 90-day outcome window and a later validation period. A later cutoff leaves outcomes unlabelled when full follow-up is unavailable. A separate final-90-day customer overlap check flags possible identifier/source discontinuity; it is shown even when an earlier reference snapshot is selected.
