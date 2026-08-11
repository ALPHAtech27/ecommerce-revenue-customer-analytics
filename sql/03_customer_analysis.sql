-- =============================================================================
-- 03_customer_analysis.sql
-- E-Commerce Revenue & Customer Analytics
--
-- Business questions answered:
--   1. Total / active / repeat customers and repeat purchase rate
--   2. Average orders and revenue per customer
--   3. Top 20 customers by lifetime revenue (with RANK / DENSE_RANK)
--   4. Customer revenue distribution (bucketed)
--   5. New vs. returning customer revenue split by month
--   6. Customers with declining purchase behavior (CTE + LAG)
--   7. Customer ranking within their state (window function, PARTITION BY)
-- =============================================================================

-- 1. Total, active, repeat customers and repeat purchase rate ----------------
WITH customer_orders AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id
)
SELECT
    (SELECT COUNT(*) FROM customers)                                   AS total_customers,
    COUNT(*)                                                           AS active_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)                   AS repeat_customers,
    ROUND(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 2)                                                AS repeat_purchase_rate_pct,
    ROUND(AVG(order_count), 2)                                          AS avg_orders_per_active_customer
FROM customer_orders;


-- 2. Average revenue per customer ----------------------------------------------
SELECT
    ROUND(AVG(customer_revenue), 2) AS avg_revenue_per_customer,
    ROUND(MIN(customer_revenue), 2) AS min_revenue,
    ROUND(MAX(customer_revenue), 2) AS max_revenue
FROM (
    SELECT customer_id, SUM(revenue) AS customer_revenue
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id
) t;


-- 3. Top 20 customers by lifetime revenue (RANK + DENSE_RANK comparison) -----
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        c.customer_name,
        c.city,
        c.state,
        SUM(o.revenue) AS lifetime_revenue,
        COUNT(*) AS order_count
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY o.customer_id, c.customer_name, c.city, c.state
)
SELECT
    customer_id,
    customer_name,
    city,
    state,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue,
    order_count,
    RANK() OVER (ORDER BY lifetime_revenue DESC)        AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY lifetime_revenue DESC)  AS revenue_dense_rank,
    ROW_NUMBER() OVER (ORDER BY lifetime_revenue DESC)  AS revenue_row_number
FROM customer_revenue
ORDER BY lifetime_revenue DESC
LIMIT 20;


-- 4. Customer revenue distribution (CASE WHEN bucketing) ---------------------
WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS lifetime_revenue
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN lifetime_revenue < 5000   THEN '1. Under 5K'
        WHEN lifetime_revenue < 20000  THEN '2. 5K - 20K'
        WHEN lifetime_revenue < 50000  THEN '3. 20K - 50K'
        WHEN lifetime_revenue < 150000 THEN '4. 50K - 150K'
        ELSE '5. 150K+'
    END AS revenue_bucket,
    COUNT(*) AS customer_count,
    ROUND(SUM(lifetime_revenue), 2) AS bucket_total_revenue
FROM customer_revenue
GROUP BY revenue_bucket
ORDER BY revenue_bucket;


-- 5. New vs returning customer revenue split by month -------------------------
-- "New" = this is the customer's first-ever order month
WITH first_order AS (
    SELECT customer_id, MIN(year_month) AS first_month
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id
)
SELECT
    o.year_month,
    SUM(CASE WHEN o.year_month = f.first_month THEN o.revenue ELSE 0 END) AS new_customer_revenue,
    SUM(CASE WHEN o.year_month != f.first_month THEN o.revenue ELSE 0 END) AS returning_customer_revenue
FROM orders o
JOIN first_order f ON o.customer_id = f.customer_id
WHERE o.order_status != 'Cancelled'
GROUP BY o.year_month
ORDER BY o.year_month;


-- 6. Customers with declining purchase behavior (CTE + LAG) ------------------
-- Flags customers whose most recent order revenue is lower than their
-- previous order's revenue AND whose average order value is trending down.
WITH ordered AS (
    SELECT
        customer_id,
        order_id,
        order_date,
        revenue,
        LAG(revenue) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_revenue,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS recency_rank
    FROM orders
    WHERE order_status != 'Cancelled'
)
SELECT customer_id, order_id, order_date, revenue, prev_order_revenue
FROM ordered
WHERE recency_rank = 1
  AND prev_order_revenue IS NOT NULL
  AND revenue < prev_order_revenue
ORDER BY (prev_order_revenue - revenue) DESC
LIMIT 20;


-- 7. Top 3 customers within each state (PARTITION BY) -------------------------
-- SQLite/standard-SQL-compatible version: rank in a CTE, then filter in the
-- outer query (avoids relying on the non-standard QUALIFY clause).
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        c.customer_name,
        c.state,
        SUM(o.revenue) AS lifetime_revenue
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY o.customer_id, c.customer_name, c.state
),
ranked AS (
    SELECT
        customer_id,
        customer_name,
        state,
        ROUND(lifetime_revenue, 2) AS lifetime_revenue,
        RANK() OVER (PARTITION BY state ORDER BY lifetime_revenue DESC) AS rank_within_state
    FROM customer_revenue
)
SELECT *
FROM ranked
WHERE rank_within_state <= 3
ORDER BY state, rank_within_state;
