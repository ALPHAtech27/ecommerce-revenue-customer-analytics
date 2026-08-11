-- =============================================================================
-- 02_revenue_analysis.sql
-- E-Commerce Revenue & Customer Analytics
--
-- Business questions answered:
--   1. Total revenue, profit, and average order value
--   2. Monthly revenue and profit trend
--   3. Month-over-month revenue growth rate
--   4. Highest revenue / profit month
--   5. Revenue and profit by category
--   6. Top 10 products by revenue
--   7. Highest-margin products
--   8. Running (cumulative) revenue over time
-- =============================================================================

-- 1. Headline KPIs -------------------------------------------------------------
SELECT
    ROUND(SUM(revenue), 2)                    AS total_revenue,
    ROUND(SUM(profit), 2)                     AS total_profit,
    COUNT(*)                                  AS total_orders,
    ROUND(SUM(revenue) * 1.0 / COUNT(*), 2)   AS average_order_value,
    ROUND(SUM(profit) * 100.0 / SUM(revenue), 2) AS profit_margin_pct
FROM orders
WHERE order_status != 'Cancelled';


-- 2. Monthly revenue and profit trend -----------------------------------------
SELECT
    year_month,
    ROUND(SUM(revenue), 2) AS monthly_revenue,
    ROUND(SUM(profit), 2)  AS monthly_profit,
    COUNT(*)               AS monthly_orders
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY year_month
ORDER BY year_month;


-- 3. Month-over-month revenue growth rate (window function: LAG) -------------
WITH monthly AS (
    SELECT
        year_month,
        SUM(revenue) AS monthly_revenue
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(LAG(monthly_revenue) OVER (ORDER BY year_month), 2) AS prior_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month)) * 100.0
        / NULLIF(LAG(monthly_revenue) OVER (ORDER BY year_month), 0),
        2
    ) AS mom_growth_pct
FROM monthly
ORDER BY year_month;


-- 4. Highest revenue month and highest profit month ---------------------------
SELECT year_month, ROUND(SUM(revenue), 2) AS monthly_revenue
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY year_month
ORDER BY monthly_revenue DESC
LIMIT 1;

SELECT year_month, ROUND(SUM(profit), 2) AS monthly_profit
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY year_month
ORDER BY monthly_profit DESC
LIMIT 1;


-- 5. Revenue and profit by category (JOIN + GROUP BY + HAVING) ---------------
SELECT
    p.category,
    ROUND(SUM(oi.revenue), 2) AS category_revenue,
    ROUND(SUM(oi.profit), 2)  AS category_profit,
    ROUND(SUM(oi.profit) * 100.0 / SUM(oi.revenue), 2) AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY p.category
HAVING SUM(oi.revenue) > 0
ORDER BY category_revenue DESC;


-- 6. Top 10 products by revenue (RANK window function) -----------------------
WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(oi.revenue) AS total_revenue,
        SUM(oi.profit)  AS total_profit
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT
    product_id,
    product_name,
    category,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(total_profit, 2)  AS total_profit,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM product_revenue
ORDER BY revenue_rank
LIMIT 10;


-- 7. Highest-margin products (min. 20 units sold, to avoid tiny-sample noise) -
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity)                                      AS units_sold,
    ROUND(SUM(oi.revenue), 2)                              AS total_revenue,
    ROUND(SUM(oi.profit), 2)                               AS total_profit,
    ROUND(SUM(oi.profit) * 100.0 / SUM(oi.revenue), 2)      AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY p.product_id, p.product_name, p.category
HAVING SUM(oi.quantity) >= 20
ORDER BY profit_margin_pct DESC
LIMIT 10;


-- 8. Running (cumulative) monthly revenue -- SUM() OVER() rolling window -----
WITH monthly AS (
    SELECT year_month, SUM(revenue) AS monthly_revenue
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(SUM(monthly_revenue) OVER (ORDER BY year_month
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue,
    ROUND(AVG(monthly_revenue) OVER (ORDER BY year_month
          ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3mo_avg_revenue
FROM monthly
ORDER BY year_month;
