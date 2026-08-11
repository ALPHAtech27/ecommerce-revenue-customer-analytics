-- =============================================================================
-- 01_data_quality.sql
-- E-Commerce Revenue & Customer Analytics
--
-- Purpose: Data quality / sanity checks on the CLEANED tables. In a real
-- warehouse these would run as part of a dbt test suite or a CI job before
-- data is promoted to the reporting layer.
--
-- Compatible with: SQLite (as shipped in this repo) and PostgreSQL.
-- Table names match the ones loaded by scripts/run_pipeline.py into
-- data/processed/ecommerce.db (see README "How to run" section).
-- =============================================================================

-- 1. Row counts per table -----------------------------------------------------
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'shipping', COUNT(*) FROM shipping
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews;


-- 2. Duplicate primary keys (should return 0 rows if cleaning worked) --------
SELECT customer_id, COUNT(*) AS occurrences
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT order_id, COUNT(*) AS occurrences
FROM orders
GROUP BY order_id
HAVING COUNT(*) > 1;


-- 3. Orphaned records: order_items pointing to a non-existent order ----------
SELECT oi.order_id
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 4. Orphaned records: orders pointing to a non-existent customer ------------
SELECT o.order_id, o.customer_id
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- 5. Negative or zero revenue / quantity (should return 0 rows) --------------
SELECT order_item_id, quantity, unit_price, discount, revenue
FROM order_items
WHERE revenue < 0 OR quantity <= 0;


-- 6. Delivery date earlier than order date (logical impossibility) -----------
SELECT order_id, order_date, delivery_date
FROM orders
WHERE delivery_date IS NOT NULL
  AND delivery_date < order_date;


-- 7. Null checks on key business columns --------------------------------------
SELECT
    SUM(CASE WHEN customer_name IS NULL THEN 1 ELSE 0 END) AS null_customer_name,
    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END)         AS null_email,
    SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END)          AS null_city
FROM customers;


-- 8. Rating values outside the valid 1-5 scale (should return 0 rows) --------
SELECT review_id, rating
FROM reviews
WHERE rating NOT BETWEEN 1 AND 5;


-- 9. Products with selling_price <= cost_price (would imply a loss on every sale)
SELECT product_id, product_name, cost_price, selling_price
FROM products
WHERE selling_price <= cost_price;


-- 10. Distinct value inventory for key categorical columns (spot-check for
--     inconsistent casing / stray categories after cleaning) ----------------
SELECT DISTINCT order_status FROM orders ORDER BY 1;
SELECT DISTINCT payment_method FROM payments ORDER BY 1;
SELECT DISTINCT shipping_method FROM shipping ORDER BY 1;
SELECT DISTINCT category FROM products ORDER BY 1;
