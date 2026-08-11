-- =============================================================================
-- 05_rfm_analysis.sql
-- E-Commerce Revenue & Customer Analytics
--
-- Two things happen in this file:
--   (a) A from-scratch SQL implementation of RFM scoring using NTILE(),
--       shown for interview purposes (the production pipeline computes RFM
--       in Python -- see scripts/rfm_segmentation.py -- so results are
--       100% reproducible; this SQL version demonstrates the same logic
--       and will produce equivalent quintile-based scores).
--   (b) Queries against the pre-computed `rfm_segments` table (loaded from
--       data/processed/rfm_customer_segments.csv), which is what the
--       Power BI dashboard and notebooks actually use.
-- =============================================================================

-- (a) RFM SCORING FROM SCRATCH IN SQL -----------------------------------------
WITH base AS (
    SELECT
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(*) AS frequency,
        SUM(revenue) AS monetary
    FROM orders
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id
),
with_recency AS (
    SELECT
        customer_id,
        frequency,
        monetary,
        CAST(julianday((SELECT MAX(order_date) FROM orders WHERE order_status != 'Cancelled'))
             - julianday(last_order_date) AS INTEGER) AS recency
    FROM base
),
scored AS (
    SELECT
        customer_id,
        recency,
        frequency,
        monetary,
        -- lower recency (days) = better = higher score, so invert the tile
        (6 - NTILE(5) OVER (ORDER BY recency))   AS r_score,
        NTILE(5) OVER (ORDER BY frequency)        AS f_score,
        NTILE(5) OVER (ORDER BY monetary)         AS m_score
    FROM with_recency
)
SELECT
    customer_id,
    recency,
    frequency,
    ROUND(monetary, 2) AS monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_sum
FROM scored
ORDER BY rfm_sum DESC
LIMIT 20;


-- (b) SEGMENT DISTRIBUTION FROM THE PRE-COMPUTED TABLE -------------------------
SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(SUM(monetary), 2) AS total_revenue,
    ROUND(AVG(monetary), 2) AS avg_revenue,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(recency), 1) AS avg_recency,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_segments), 2) AS pct_of_customers
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;


-- (c) Champions & Loyal Customers -- who they are, where they live -----------
SELECT
    segment,
    state,
    COUNT(*) AS customer_count,
    ROUND(SUM(monetary), 2) AS segment_state_revenue
FROM rfm_segments
WHERE segment IN ('Champions', 'Loyal Customers')
GROUP BY segment, state
ORDER BY segment_state_revenue DESC
LIMIT 15;


-- (d) At-risk / Can't Lose Them -- highest priority win-back targets ----------
SELECT
    customer_id,
    customer_name,
    city,
    state,
    recency,
    frequency,
    ROUND(monetary, 2) AS monetary,
    segment
FROM rfm_segments
WHERE segment IN ('At Risk', "Can't Lose Them")
ORDER BY monetary DESC
LIMIT 20;


-- (e) Revenue concentration: what % of revenue comes from the top 2 segments? -
WITH segment_revenue AS (
    SELECT segment, SUM(monetary) AS revenue
    FROM rfm_segments
    GROUP BY segment
)
SELECT
    ROUND(SUM(CASE WHEN segment IN ('Champions', 'Loyal Customers') THEN revenue ELSE 0 END)
          * 100.0 / SUM(revenue), 2) AS pct_revenue_from_top_2_segments
FROM segment_revenue;
