# Data contracts and metric definitions

## Provenance

Constante, Fabian; Silva, Fernando; Pereira, António (2019), “DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS”, Mendeley Data, V5, https://doi.org/10.17632/8gx2fvg2k6.5 (CC BY 4.0). A publicly downloadable mirror is used: https://zenodo.org/records/11112645. Mirror MD5: `354eb3cd362619ef120ca2201337ae92`; pipeline also records SHA-256. Preserve original attribution despite the Kaggle mirror showing different licensing metadata.

This is a historical benchmark, not a live ERP or an employer's production extract. Source-generated features or customer construction can distort real-world interpretations.

## order_lines

One row per Order Item Id. Only whitelisted fields are ingested. Names, emails, customer passwords, street addresses, zip codes, images and precise coordinates are excluded. Local internal customer/order IDs are retained for aggregation and ignored by Git.

| Analytical field | Source field / interpretation |
|---|---|
| item_id | Order Item Id: primary key |
| order_id | Order Id: shared by lines |
| customer_id | Order Customer Id: observed identifier, not guaranteed lifetime identity |
| ordered_at | order date (DateOrders), parsed month/day/year; timezone unspecified |
| market, region | Order market/region |
| shipping_mode | Shipping Mode |
| actual_days, scheduled_days | Shipping durations, not a live delivery feed |
| late_flag | Supplied Late_delivery_risk binary label |
| net_sales | Order Item Total, after recorded line discount |
| gross_sales | Sales, before recorded line discount |
| recorded_profit | Order Profit Per Order, supplied per row; varies across lines within orders |

The confusingly named profit field varies within orders and equals Benefit per order in the profiled extract. The system treats it as an additive line-level recorded measure, not audited profit. Confirm business semantics before production use. Negative profit is valid; negative sales and invalid IDs fail validation.

## fact_orders

One row per order_id. Sum line sales, quantities and recorded profit. Before committing, assert order-level customer, timestamp, market, region, status, shipping mode, customer segment, shipping durations and late flag agree across lines. Counts are distinct orders, never order lines.

Completed commercial activity = order_status in COMPLETE or CLOSED. PENDING, PROCESSING, payment states, CANCELED, SUSPECTED_FRAUD and ON_HOLD remain in stored history but are excluded from dashboard commercial KPIs. Snapshot statuses do not establish when an order became complete.

## Metrics

- Late rate = late completed orders / completed orders.
- Net sales = sum(net_sales) over completed orders; no tax/refund reconciliation is available.
- Recorded profit = sum(recorded_profit) over completed orders, in unverified units.
- Snapshot recency = cutoff calendar date minus last completed purchase calendar date.
- Frequency = distinct historical completed orders through cutoff.
- Monetary = historical net sales through cutoff.
- Inactivity label = no completed purchase in (cutoff, cutoff + 90 days]. NULL if full follow-up is unavailable.
- Cohort = first observed completed purchase month. Retention Mx = cohort customers purchasing in month x / original cohort size.

The current final observed calendar month is conservatively excluded from cohort maturity. Distinguish observed 0% retention from unobserved/null. The data's max timestamp establishes nominal coverage only; it cannot prove complete capture for every customer.

## Filters

Market and shipping-mode controls apply only to delivery cards, bars, scenario and detail. Monthly sales, customer snapshots and cohort tables remain full-portfolio and are explicitly labeled.
