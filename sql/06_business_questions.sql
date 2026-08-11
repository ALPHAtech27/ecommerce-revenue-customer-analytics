-- =============================================================================
-- 06_business_questions.sql
-- E-Commerce Revenue & Customer Analytics
--
-- A grab-bag of additional interview-style business questions covering
-- geography, payments, shipping, and reviews -- the sections not already
-- covered in files 02-05.
-- =============================================================================

-- 1. Revenue by state (geographic performance) ---------------------------------
SELECT
    c.state,
    COUNT(DISTINCT o.customer_id) AS customers,
    COUNT(*) AS orders,
    ROUND(SUM(o.revenue), 2) AS revenue,
    ROUND(SUM(o.revenue) / COUNT(*), 2) AS avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status != 'Cancelled'
GROUP BY c.state
ORDER BY revenue DESC;


-- 2. Payment method distribution and revenue share -----------------------------
WITH by_method AS (
    SELECT payment_method, COUNT(*) AS txn_count, SUM(payment_amount) AS revenue
    FROM payments
    WHERE payment_status = 'Success'
    GROUP BY payment_method
)
SELECT
    payment_method,
    txn_count,
    ROUND(revenue, 2) AS revenue,
    ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS pct_of_revenue
FROM by_method
ORDER BY revenue DESC;


-- 3. Failed payment rate by payment method --------------------------------------
SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 2) AS failed_rate_pct
FROM payments
GROUP BY payment_method
ORDER BY failed_rate_pct DESC;


-- 4. Average delivery time by shipping method -----------------------------------
SELECT
    s.shipping_method,
    COUNT(*) AS shipments,
    ROUND(AVG(julianday(s.delivery_date) - julianday(s.shipping_date)), 2) AS avg_delivery_days,
    ROUND(AVG(s.shipping_cost), 2) AS avg_shipping_cost
FROM shipping s
WHERE s.delivery_date IS NOT NULL
GROUP BY s.shipping_method
ORDER BY avg_delivery_days;


-- 5. Late delivery rate (defined here as > 7 days from ship to delivery) -------
SELECT
    shipping_method,
    COUNT(*) AS shipments,
    SUM(CASE WHEN julianday(delivery_date) - julianday(shipping_date) > 7 THEN 1 ELSE 0 END) AS late_shipments,
    ROUND(SUM(CASE WHEN julianday(delivery_date) - julianday(shipping_date) > 7 THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 2) AS late_delivery_rate_pct
FROM shipping
WHERE delivery_date IS NOT NULL
GROUP BY shipping_method
ORDER BY late_delivery_rate_pct DESC;


-- 6. Average rating by category --------------------------------------------------
SELECT
    p.category,
    COUNT(*) AS review_count,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM reviews r
JOIN products p ON r.product_id = p.product_id
GROUP BY p.category
ORDER BY avg_rating DESC;


-- 7. Relationship between delivery time and customer rating ---------------------
WITH review_delivery AS (
    SELECT
        r.rating,
        CAST(julianday(o.delivery_date) - julianday(o.order_date) AS INTEGER) AS delivery_days
    FROM reviews r
    JOIN orders o ON r.order_id = o.order_id
    WHERE o.delivery_date IS NOT NULL
)
SELECT
    CASE
        WHEN delivery_days <= 3 THEN '0-3 days'
        WHEN delivery_days <= 5 THEN '4-5 days'
        WHEN delivery_days <= 7 THEN '6-7 days'
        WHEN delivery_days <= 10 THEN '8-10 days'
        ELSE '10+ days'
    END AS delivery_bucket,
    COUNT(*) AS reviews,
    ROUND(AVG(rating), 2) AS avg_rating
FROM review_delivery
GROUP BY delivery_bucket
ORDER BY MIN(delivery_days);


-- 8. Monthly order growth (order count MoM %, distinct from revenue growth) ----
WITH monthly_orders AS (
    SELECT year_month, COUNT(*) AS order_count
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY year_month
)
SELECT
    year_month,
    order_count,
    LAG(order_count) OVER (ORDER BY year_month) AS prior_month_orders,
    ROUND(
        (order_count - LAG(order_count) OVER (ORDER BY year_month)) * 100.0
        / NULLIF(LAG(order_count) OVER (ORDER BY year_month), 0), 2
    ) AS order_growth_pct
FROM monthly_orders
ORDER BY year_month;


-- 9. Cancellation rate by category (operational / demand-quality signal) -------
SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0
          / COUNT(DISTINCT o.order_id), 2) AS cancellation_rate_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY cancellation_rate_pct DESC;


-- 10. Day-of-week order pattern (operations / staffing planning) ---------------
SELECT
    day_of_week,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM orders
WHERE order_status != 'Cancelled'
GROUP BY day_of_week
ORDER BY orders DESC;
