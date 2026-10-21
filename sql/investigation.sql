-- Avoid diagnosing from rates alone: include volume and gross/net sales.
SELECT market, shipping_mode, completed_orders, late_orders, late_rate, net_sales,
       late_orders * 0.10 * 20 AS illustrative_avoidable_cost_units
FROM delivery_by_mode ORDER BY late_orders DESC;

-- Previous-month comparisons and rolling statistics are already exposed by the reporting view.
SELECT * FROM monthly_operations ORDER BY month;

-- RFM-style account history at an explicit cutoff; no purchases after cutoff enter features.
SELECT customer_id, MIN(ordered_at) AS first_observed_purchase,
       MAX(ordered_at) AS last_observed_purchase, COUNT(*) AS frequency,
       SUM(net_sales) AS monetary
FROM fact_orders WHERE completed=1 AND ordered_at < '2017-11-03'
GROUP BY customer_id ORDER BY monetary DESC;

-- Never sum an order table after joining it to the line table without re-aggregating.
-- Test the grain instead:
SELECT order_id, COUNT(*) AS duplicates FROM fact_orders GROUP BY order_id HAVING COUNT(*)>1;
