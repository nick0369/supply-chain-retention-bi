"""Descriptive 90-day inactivity labels with explicit historical observation windows."""
from __future__ import annotations

import pandas as pd


def snapshot(orders: pd.DataFrame, as_of: str, observed_through: str, horizon: int = 90):
    cutoff = pd.Timestamp(as_of).normalize()
    observed = pd.Timestamp(observed_through).normalize()
    if horizon <= 0 or cutoff > observed:
        raise ValueError("Invalid horizon or snapshot after observation end")
    data = orders.loc[orders.completed.eq(1)].copy()
    data["date"] = pd.to_datetime(data.ordered_at).dt.normalize()
    history = data.loc[data.date <= cutoff]
    if history.empty:
        raise ValueError("Snapshot has no completed purchase history")
    customers = history.groupby("customer_id").agg(
        first_purchase=("date", "min"), last_purchase=("date", "max"),
        frequency=("order_id", "nunique"), monetary=("net_sales", "sum"),
    ).reset_index()
    customers["recency_days"] = (cutoff - customers.last_purchase).dt.days
    customers["segment"] = customers.recency_days.map(
        lambda days: "Active (0–30 days)" if days <= 30 else "Cooling (31–90 days)" if days <= 90 else "Inactive (91+ days)"
    )
    # All customers in this snapshot share the same observation window.
    mature = cutoff + pd.Timedelta(days=horizon) <= observed
    future = data.loc[(data.date > cutoff) & (data.date <= cutoff + pd.Timedelta(days=horizon))]
    future_customers = set(future.customer_id)
    customers["inactive_next_90d"] = customers.customer_id.map(lambda c: int(c not in future_customers)) if mature else pd.NA
    customers["cohort"] = customers.first_purchase.dt.strftime("%Y-%m")
    return customers, {"as_of": cutoff.strftime("%Y-%m-%d"), "observed_through": observed.strftime("%Y-%m-%d"),
                       "horizon_days": horizon, "label_mature": mature}


def cohort_retention(orders: pd.DataFrame, observed_through: str) -> list[dict]:
    frame = orders.loc[orders.completed.eq(1)].copy()
    frame["month"] = pd.to_datetime(frame.ordered_at).dt.to_period("M")
    first = frame.groupby("customer_id").month.min()
    frame["cohort"] = frame.customer_id.map(first)
    sizes = first.value_counts()
    frame["period"] = (frame.month.dt.year-frame.cohort.dt.year)*12 + frame.month.dt.month-frame.cohort.dt.month
    counts = frame.groupby(["cohort", "period"]).customer_id.nunique()
    # Exclude current partial month from retention denominators.
    complete_month_end = pd.Timestamp(observed_through).to_period("M") - 1
    result = []
    for cohort, size in sizes.sort_index().items():
        for offset in range(7):
            mature = cohort + offset <= complete_month_end
            count = int(counts.get((cohort, offset), 0)) if mature else None
            result.append({"cohort": str(cohort), "period": offset, "size": int(size),
                           "active": count, "retention": count/int(size) if mature else None})
    return result
