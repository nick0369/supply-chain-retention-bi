import pandas as pd
import pytest

from operations.retention import cohort_retention, snapshot


@pytest.fixture
def orders():
    return pd.DataFrame([
        {'order_id': 1, 'customer_id': 10, 'ordered_at': '2017-01-01', 'net_sales': 100, 'completed': 1},
        {'order_id': 2, 'customer_id': 20, 'ordered_at': '2017-01-10', 'net_sales': 50, 'completed': 1},
        {'order_id': 3, 'customer_id': 10, 'ordered_at': '2017-02-01', 'net_sales': 300, 'completed': 1},
        {'order_id': 4, 'customer_id': 30, 'ordered_at': '2017-03-01', 'net_sales': 900, 'completed': 1},
        {'order_id': 5, 'customer_id': 20, 'ordered_at': '2017-02-10', 'net_sales': 800, 'completed': 0},
    ])


def test_point_in_time_features_exclude_future(orders):
    customers, window = snapshot(orders, '2017-01-31', '2017-05-01')
    assert set(customers.customer_id) == {10, 20}
    assert customers.monetary.sum() == 150
    assert customers.frequency.sum() == 2
    assert window['label_mature']
    labels = dict(zip(customers.customer_id, customers.inactive_next_90d))
    assert labels == {10: 0, 20: 1}


def test_censored_labels_remain_missing(orders):
    customers, window = snapshot(orders, '2017-02-01', '2017-03-01')
    assert not window['label_mature']
    assert customers.inactive_next_90d.isna().all()


def test_snapshot_after_end_rejected(orders):
    with pytest.raises(ValueError):
        snapshot(orders, '2018-01-01', '2017-03-01')


def test_cohort_zero_distinguished_from_unobserved(orders):
    cells = cohort_retention(orders, '2017-03-31')
    january = {r['period']: r for r in cells if r['cohort'] == '2017-01'}
    assert january[0]['retention'] == 1
    assert january[1]['retention'] == 0.5
    assert january[2]['retention'] is None


def test_zero_activity_in_fully_observed_month_is_zero(orders):
    cells = cohort_retention(orders, '2017-05-01')
    assert next(r for r in cells if r['cohort']=='2017-01' and r['period']==3)['retention'] == 0
