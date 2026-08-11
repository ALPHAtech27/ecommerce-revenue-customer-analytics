-- =============================================================================
-- 04_product_analysis.sql
-- E-Commerce Revenue & Customer Analytics
--
-- Business questions answered:
--   1. Top products by revenue, profit, and quantity sold
--   2. Worst-performing products (revenue but negative/near-zero margin)
--   3. Category and sub-category contribution to total revenue
--   4. Discount level vs. revenue and profit
--   5. Products where high revenue does NOT mean high profit
--   6. Top product per category (window function, ROW_NUMBER + PARTITION BY)
-- =============================================================================

-- 1. Top 10 products by quantity sold ------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.revenue), 2) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold DESC
LIMIT 10;


-- 2. Worst-performing products: sold reasonably well but poor margin ---------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.revenue), 2) AS total_revenue,
    ROUND(SUM(oi.profit), 2) AS total_profit,
    ROUND(SUM(oi.profit) * 100.0 / NULLIF(SUM(oi.revenue), 0), 2) AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY p.product_id, p.product_name, p.category
HAVING SUM(oi.quantity) >= 10
ORDER BY profit_margin_pct ASC
LIMIT 10;


-- 3. Category contribution to total revenue (% of grand total) ---------------
WITH category_revenue AS (
    SELECT p.category, SUM(oi.revenue) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY p.category
)
SELECT
    category,
    ROUND(revenue, 2) AS category_revenue,
    ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS pct_of_total_revenue
FROM category_revenue
ORDER BY category_revenue DESC;


-- 4. Sub-category performance ---------------------------------------------------
SELECT
    p.category,
    p.sub_category,
    ROUND(SUM(oi.revenue), 2) AS revenue,
    ROUND(SUM(oi.profit), 2) AS profit,
    SUM(oi.quantity) AS units_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY p.category, p.sub_category
ORDER BY revenue DESC
LIMIT 15;


-- 5. Discount level vs. revenue and profit -------------------------------------
SELECT
    CASE
        WHEN discount = 0 THEN '0% (no discount)'
        WHEN discount <= 0.10 THEN '1-10%'
        WHEN discount <= 0.20 THEN '11-20%'
        WHEN discount <= 0.30 THEN '21-30%'
        ELSE '30%+'
    END AS discount_band,
    COUNT(*) AS line_items,
    ROUND(SUM(oi.revenue), 2) AS revenue,
    ROUND(SUM(oi.profit), 2) AS profit,
    ROUND(SUM(oi.profit) * 100.0 / NULLIF(SUM(oi.revenue), 0), 2) AS profit_margin_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'Cancelled'
GROUP BY discount_band
ORDER BY discount_band;


-- 6. Products where high revenue does NOT translate to high profit -----------
-- (top-20-by-revenue products whose profit margin falls below the overall
--  average margin -- these are prime candidates for pricing/discount review)
WITH product_perf AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(oi.revenue) AS revenue,
        SUM(oi.profit) AS profit,
        SUM(oi.profit) * 100.0 / NULLIF(SUM(oi.revenue), 0) AS margin_pct
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY p.product_id, p.product_name, p.category
),
overall_avg AS (
    SELECT AVG(margin_pct) AS avg_margin FROM product_perf
),
top20_by_revenue AS (
    SELECT * FROM product_perf ORDER BY revenue DESC LIMIT 20
)
SELECT
    t.product_id,
    t.product_name,
    t.category,
    ROUND(t.revenue, 2) AS revenue,
    ROUND(t.margin_pct, 2) AS margin_pct,
    ROUND(o.avg_margin, 2) AS overall_avg_margin_pct
FROM top20_by_revenue t
CROSS JOIN overall_avg o
WHERE t.margin_pct < o.avg_margin
ORDER BY t.revenue DESC;


-- 7. Top-selling product per category (ROW_NUMBER + PARTITION BY) ------------
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_id,
        p.product_name,
        SUM(oi.revenue) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY p.category, p.product_id, p.product_name
),
ranked AS (
    SELECT
        category,
        product_id,
        product_name,
        ROUND(revenue, 2) AS revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) AS rn
    FROM product_revenue
)
SELECT category, product_id, product_name, revenue
FROM ranked
WHERE rn = 1
ORDER BY revenue DESC;
