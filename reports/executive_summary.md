# Executive Summary

**E-Commerce Revenue & Customer Analytics**
*Data as of the most recent synthetic order date: December 31, 2024*

> **Note on the data:** This analysis is built on a **synthetic** dataset
> generated with a fixed random seed for reproducibility (see
> `data/README.md`). It is designed to behave like a realistic e-commerce
> export, but the specific figures below are illustrative, not real
> business results.

---

## Headline KPIs

| Metric | Value |
|---|---|
| Total Revenue (excl. cancelled orders) | Rs 1,337,315,331 |
| Total Profit | Rs 418,207,478 |
| Overall Profit Margin | 31.27% |
| Total Valid Orders | 103,402 |
| Active Customers (>=1 order) | 31,034 |
| Average Order Value | Rs 12,933 |
| Repeat Purchase Rate (active customers) | 59.10% |
| Repeat Purchase Rate (all registered customers) | 36.68% |

---

## What we set out to answer

The business wanted to understand revenue performance, product/category
performance, customer behavior and lifetime value, repeat purchase
patterns, customer segmentation, geographic performance, payment
behavior, review/satisfaction trends, and shipping performance — and to
turn all of that into concrete recommendations rather than a pile of
charts.

## Top findings

**1. Revenue is heavily concentrated in a small share of customers.**
RFM segmentation shows **Champions** (20.8% of active customers) generate
**56.9%** of total revenue. Champions + Loyal Customers together are
**36.0%** of the customer base and **74.4%** of revenue. This is a
textbook Pareto pattern and the single most important lever in this
dataset — protecting and growing this segment matters more than
broad-based, undifferentiated marketing spend.

**2. Two-thirds of active customers have ordered only once.**
Repeat purchase rate is 59.10% among the customers who ordered more than
once out of the active base, but only 36.68% of all *registered*
customers ever place a second order. Converting even a modest share of
one-time buyers into repeat buyers is one of the highest-leverage growth
opportunities available, since acquiring a first-time customer is
typically far more expensive than retaining an existing one.

**3. Category revenue leadership does not always match margin leadership.**
Electronics is the clear revenue leader (Rs 414M) but sits mid-pack on
margin (30.06%). Pet Supplies and Beauty & Personal Care post the
strongest margins (35.70% and 34.99% respectively) despite far smaller
revenue bases. Books has both the lowest revenue and the lowest margin
(25.17%) among all 12 categories — a candidate for catalog or pricing
review.

**4. At Risk and Can't Lose Them segments represent Rs 70.4M in
historically-proven revenue that has gone quiet.** 1,937 customers who
used to order frequently and spend well haven't purchased recently. This
is a defined, addressable win-back list rather than a cold audience.

**5. Estimated customer lifetime value is highly skewed.**
Average CLV (Rs 56,413) sits well above median CLV (Rs 33,472),
confirming a small number of high-value customers pull the average up —
consistent with the RFM concentration finding above.

**6. Geographic revenue is led by Maharashtra, Gujarat, and Kerala**, but
revenue is fairly evenly distributed across the top 10 states (all
within a Rs 60M-145M band), suggesting demand is broad-based rather than
concentrated in one region.

**7. UPI is the leading payment method** by both order count (38,820
orders) and revenue (Rs 504M), consistent with its popularity in the
Indian market this dataset is modeled on.

## How this analysis was built

- **Data**: A synthetic dataset of 50,000 customers, 320 products, and
  110,000 orders, generated with realistic data quality issues and then
  cleaned (see `data/README.md` and `reports/data_dictionary.md`).
- **Pipeline**: Python (pandas/NumPy) for cleaning, feature engineering,
  RFM segmentation, and CLV estimation — fully reproducible via
  `python scripts/run_pipeline.py`.
- **SQL**: 6 files, 50+ business-question queries demonstrating joins,
  CTEs, window functions, and aggregate analysis (`sql/`).
- **Notebooks**: 4 Jupyter notebooks walking through EDA, customer
  analysis, RFM segmentation, and business insight synthesis
  (`notebooks/`).
- **Dashboard**: Power BI-ready CSV extracts and a full build guide with
  DAX measures (`dashboard/`).

See `reports/business_recommendations.md` for the full, prioritized
recommendation list, and `reports/data_dictionary.md` for complete table
and column documentation.
