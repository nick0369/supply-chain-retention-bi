"""Transactional incremental ingestion with audit manifests for SQLite and PostgreSQL."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from operations.source import MAPPING, NUMERIC


def connect(url: str):
    return create_engine(url)


def tables():
    metadata = MetaData()
    integer_fields = {"item_id", "order_id", "customer_id", "quantity", "actual_days", "scheduled_days", "late_flag"}
    lines = Table("order_lines", metadata, *[
        Column(field, Integer if field in integer_fields else Float if field in NUMERIC else String,
               primary_key=field == "item_id", nullable=False) for field in MAPPING.values()
    ])
    batches = Table("ingestion_batches", metadata,
                    Column("sha256", String, primary_key=True), Column("source_rows", Integer, nullable=False),
                    Column("loaded_at_utc", String, nullable=False))
    return metadata, lines, batches


def load(frame: pd.DataFrame, digest: str, engine, root: Path, force: bool = False) -> dict:
    metadata, lines, batches = tables()
    metadata.create_all(engine)
    started = datetime.now(UTC).isoformat()
    with engine.begin() as connection:
        seen = connection.execute(text("SELECT COUNT(*) FROM ingestion_batches WHERE sha256=:sha"),
                                  {"sha": digest}).scalar()
        if seen and not force:
            # SQL definitions may have changed even when the source has not.
            for statement in (root / "sql/marts.sql").read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    connection.execute(text(statement))
            return {"status": "already_loaded", "source_rows": len(frame), "source_sha256": digest}
        existing = connection.execute(text("SELECT COUNT(*) FROM order_lines")).scalar()
        if not existing:
            frame.to_sql("order_lines", connection, if_exists="append", index=False, chunksize=1000)
        else:
            insert = pg_insert if engine.dialect.name == "postgresql" else sqlite_insert
            records = json.loads(frame.to_json(orient="records", double_precision=15))
            for offset in range(0, len(records), 500):
                statement = insert(lines).values(records[offset:offset+500])
                connection.execute(statement.on_conflict_do_update(
                    index_elements=["item_id"],
                    set_={field: statement.excluded[field] for field in MAPPING.values() if field != "item_id"},
                ))
        # Validate order-level dimensions after merging the batch, not only within the incoming file.
        inconsistent = connection.execute(text("""
            SELECT order_id FROM order_lines GROUP BY order_id HAVING
              COUNT(DISTINCT customer_id)>1 OR COUNT(DISTINCT ordered_at)>1
              OR COUNT(DISTINCT market)>1 OR COUNT(DISTINCT shipping_mode)>1
              OR COUNT(DISTINCT order_status)>1 OR COUNT(DISTINCT delivery_status)>1
              OR COUNT(DISTINCT actual_days)>1 OR COUNT(DISTINCT scheduled_days)>1
              OR COUNT(DISTINCT late_flag)>1 OR COUNT(DISTINCT region)>1
              OR COUNT(DISTINCT customer_segment)>1
            LIMIT 1
        """)).first()
        if inconsistent:
            raise ValueError(f"Conflicting order-level attributes for order {inconsistent[0]}")
        for statement in (root / "sql/marts.sql").read_text(encoding="utf-8").split(";"):
            if statement.strip():
                connection.execute(text(statement))
        if not seen:
            connection.execute(batches.insert().values(sha256=digest, source_rows=len(frame), loaded_at_utc=started))
    return {"status": "loaded", "source_rows": len(frame), "source_sha256": digest}


def query(engine, sql: str, params=None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql_query(text(sql), connection, params=params)
