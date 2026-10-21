import pandas as pd
import pytest


@pytest.fixture
def lines():
    return pd.DataFrame([
        {"item_id": i, "order_id": order, "customer_id": customer, "ordered_at": date,
         "shipping_mode": "Standard Class", "market": "Europe", "region": "Western Europe",
         "category": "Sports", "customer_segment": "Consumer", "actual_days": 5,
         "scheduled_days": 4, "late_flag": 1, "delivery_status": "Late delivery", "order_status": "COMPLETE",
         "gross_sales": 100.0, "net_sales": 90.0, "quantity": 1, "recorded_profit": -5.0}
        for i, order, customer, date in [(1, 10, 1, "2017-01-01 12:00:00"),
                                         (2, 10, 1, "2017-01-01 12:00:00"),
                                         (3, 20, 2, "2017-01-20 12:00:00"),
                                         (4, 30, 1, "2017-02-15 12:00:00")]
    ])
