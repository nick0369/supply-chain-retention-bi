DROP VIEW IF EXISTS monthly_operations;
DROP VIEW IF EXISTS delivery_by_mode;
DROP VIEW IF EXISTS fact_orders;

CREATE VIEW fact_orders AS
SELECT order_id, MIN(customer_id) AS customer_id, MIN(ordered_at) AS ordered_at,
       MIN(market) AS market, MIN(region) AS region, MIN(shipping_mode) AS shipping_mode,
       MIN(customer_segment) AS customer_segment, MIN(order_status) AS order_status,
       MIN(delivery_status) AS delivery_status, MAX(late_flag) AS late_flag,
       MAX(actual_days) AS actual_days, MAX(scheduled_days) AS scheduled_days,
       COUNT(*) AS line_count, SUM(quantity) AS quantity,
       SUM(gross_sales) AS gross_sales, SUM(net_sales) AS net_sales,
       SUM(recorded_profit) AS recorded_profit,
       CASE WHEN MIN(order_status) IN ('COMPLETE','CLOSED') THEN 1 ELSE 0 END AS completed
FROM order_lines GROUP BY order_id;

CREATE VIEW delivery_by_mode AS
SELECT market, shipping_mode, COUNT(*) AS completed_orders, SUM(late_flag) AS late_orders,
       1.0*SUM(late_flag)/NULLIF(COUNT(*),0) AS late_rate,
       SUM(net_sales) AS net_sales, SUM(recorded_profit) AS recorded_profit,
       DENSE_RANK() OVER (PARTITION BY market ORDER BY 1.0*SUM(late_flag)/NULLIF(COUNT(*),0) DESC) AS delay_rank
FROM fact_orders WHERE completed=1 GROUP BY market, shipping_mode;

CREATE VIEW monthly_operations AS
WITH monthly AS (
 SELECT SUBSTR(ordered_at,1,7) AS month, COUNT(*) AS completed_orders,
        SUM(net_sales) AS net_sales, SUM(recorded_profit) AS recorded_profit,
        SUM(late_flag) AS late_orders
 FROM fact_orders WHERE completed=1 GROUP BY SUBSTR(ordered_at,1,7)
)
SELECT *, net_sales-LAG(net_sales) OVER (ORDER BY month) AS monthly_sales_change,
       AVG(net_sales) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_three_month_sales
FROM monthly;
