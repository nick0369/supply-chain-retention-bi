import os
from pathlib import Path

import pytest
from sqlalchemy import text

from operations.source import validate
from operations.warehouse import connect, load, query, tables

ROOT = Path(__file__).resolve().parents[1]


def test_order_grain_and_checksum_skip(lines):
    engine = connect('sqlite:///:memory:')
    assert load(validate(lines), 'first', engine, ROOT)['status'] == 'loaded'
    assert load(validate(lines), 'first', engine, ROOT)['status'] == 'already_loaded'
    orders = query(engine, 'SELECT * FROM fact_orders')
    assert len(orders) == 3
    assert orders.line_count.sum() == 4
    assert orders.net_sales.sum() == 360
    assert query(engine, 'SELECT SUM(completed_orders) AS n FROM delivery_by_mode').iloc[0].n == 3
    assert len(query(engine, 'SELECT * FROM ingestion_batches')) == 1
    engine.dispose()


def test_corrected_batch_upserts_instead_of_duplicating(lines):
    engine = connect('sqlite:///:memory:')
    load(validate(lines), 'first', engine, ROOT)
    corrected = lines.iloc[:1].copy()
    corrected['net_sales'] = 75.0
    load(validate(corrected), 'correction', engine, ROOT)
    assert len(query(engine, 'SELECT * FROM order_lines')) == 4
    assert query(engine, 'SELECT SUM(net_sales) AS n FROM fact_orders').iloc[0].n == 345
    engine.dispose()


def test_conflicting_order_update_rolls_back(lines):
    engine = connect('sqlite:///:memory:')
    load(validate(lines), 'first', engine, ROOT)
    bad = lines.iloc[:1].copy()
    bad['shipping_mode'] = 'Same Day'
    with pytest.raises(ValueError, match='Conflicting'):
        load(validate(bad), 'bad', engine, ROOT)
    assert query(engine, 'SELECT shipping_mode FROM order_lines WHERE item_id=1').iloc[0, 0] == 'Standard Class'
    assert len(query(engine, 'SELECT * FROM ingestion_batches')) == 1
    engine.dispose()


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Dedicated PostgreSQL test URL not configured')
def test_postgres_incremental_refresh(lines):
    engine = connect(os.environ['TEST_DATABASE_URL'])
    metadata, _, _ = tables()
    # Explicitly dedicated CI database; do not use your reporting database here.
    with engine.begin() as c:
        for view in ['monthly_operations', 'delivery_by_mode', 'fact_orders']:
            c.execute(text(f'DROP VIEW IF EXISTS {view}'))
    metadata.drop_all(engine)
    assert load(validate(lines), 'first', engine, ROOT)['status'] == 'loaded'
    assert load(validate(lines), 'first', engine, ROOT)['status'] == 'already_loaded'
    changed = lines.iloc[:1].copy()
    changed['net_sales'] = 70.0
    load(validate(changed), 'changed', engine, ROOT)
    assert query(engine, 'SELECT SUM(net_sales) AS n FROM fact_orders').iloc[0].n == 340
    assert len(query(engine, 'SELECT * FROM monthly_operations')) == 2
    engine.dispose()
