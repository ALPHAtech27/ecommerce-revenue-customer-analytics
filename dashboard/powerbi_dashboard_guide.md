# Power BI Dashboard Build Guide

**E-Commerce Revenue & Customer Analytics**

This project does not ship a `.pbix` file (Power BI Desktop files are
binary and environment-specific, so they don't reproduce reliably across
machines). Instead, this guide plus the CSV extracts in
`dashboard/dashboard_data/` give you everything needed to build the
dashboard from scratch in Power BI Desktop in under an hour.

---

## 1. Data sources to import

Open Power BI Desktop → **Get Data → Text/CSV** → import each file below
from `dashboard/dashboard_data/`:

| File | Grain | Used on page(s) |
|---|---|---|
| `kpi_summary.csv` | Single row | Executive Overview |
| `monthly_trends.csv` | One row per month | Executive Overview |
| `category_performance.csv` | One row per category/sub-category | Executive Overview, Product Analytics |
| `product_performance.csv` | One row per product | Product Analytics |
| `geographic_performance.csv` | One row per city/state | Geographic Analysis |
| `payment_method_performance.csv` | One row per payment method | Operations |
| `payment_status_breakdown.csv` | One row per method × status | Operations |
| `shipping_performance.csv` | One row per shipping method | Operations |
| `rating_by_category.csv` | One row per category | Operations |
| `rating_vs_delivery_time.csv` | One row per delivery-time bucket | Operations |
| `rfm_customer_segments.csv` | One row per customer | Customer Analytics |
| `rfm_segment_summary.csv` | One row per segment | Customer Analytics |
| `customer_lifetime_value.csv` | One row per customer | Customer Analytics |

Alternatively, import `data/processed/ecommerce.db` directly (SQLite)
using the **ODBC** connector with a SQLite ODBC driver, if you'd rather
work from the raw joinable tables and build these summaries as DAX/Power
Query measures instead of pre-aggregated CSVs.

## 2. Recommended relationships

If you also import `customer_lifetime_value.csv` and
`rfm_customer_segments.csv` alongside a `customers` table, set:

- `rfm_customer_segments[customer_id]` → `customer_lifetime_value[customer_id]` (1:1)
- `product_performance[product_id]` → `category_performance` (many:1 via category, if imported at product grain)

Most tables in this dashboard are pre-aggregated extracts (one row per
report grain), so heavy relationship modeling is optional — the CSVs are
designed to be dropped directly onto visuals.

## 3. Dashboard pages

### Page 1 — Executive Overview

**KPI cards** (from `kpi_summary.csv`): Total Revenue, Total Profit,
Total Orders, Total Customers, Average Order Value, Repeat Purchase
Rate %, Profit Margin %.

**Charts:**
- Line chart: `monthly_trends.csv` → revenue & profit by `year_month`
- Bar chart: `category_performance.csv` → revenue by `category`
- Map or bar chart: `geographic_performance.csv` → revenue by `state`

**Slicers:** year_month (date range), category, state

---

### Page 2 — Customer Analytics

**Charts:**
- Bar/pie chart: `rfm_segment_summary.csv` → customer_count and
  total_revenue by `segment`
- Scatter chart: `rfm_customer_segments.csv` → recency (x) vs. frequency
  (y), sized by monetary, colored by segment
- Table: top 20 customers from `customer_lifetime_value.csv` sorted by
  `clv` descending
- Histogram: `customer_lifetime_value.csv` → distribution of `clv` by
  `clv_tier`

**Slicers:** segment, clv_tier, state

**Drill-through suggestion:** From the segment bar chart, drill through
to a customer-detail page filtered to `rfm_customer_segments[segment]`.

---

### Page 3 — Product Analytics

**Charts:**
- Bar chart: `product_performance.csv` → top 15 products by revenue
- Bar chart: `category_performance.csv` → revenue vs. profit_margin_pct
  by category (dual-axis)
- Table: `category_performance.csv` filtered/sorted to surface
  high-revenue, low-margin categories (see Discount Impact measure below)

**Slicers:** category, brand

---

### Page 4 — Operations

**Charts:**
- Bar chart: `shipping_performance.csv` → avg_delivery_days and
  late_delivery_rate_pct by shipping_method
- Bar chart: `payment_method_performance.csv` → revenue by payment_method
- Stacked bar: `payment_status_breakdown.csv` → count by payment_method
  and payment_status
- Line chart: `rating_vs_delivery_time.csv` → avg_rating by
  delivery_bucket

**Slicers:** shipping_method, payment_method

---

### Page 5 — Geographic Analysis

**Charts:**
- Filled map or bar chart: `geographic_performance.csv` → revenue by
  state
- Table: `geographic_performance.csv` sorted by revenue, with orders,
  profit, customers, and average_order_value columns visible

**Slicers:** state, city

---

## 4. DAX measures

Create these as new measures in Power BI (**Modeling → New Measure**).
Adjust table/column names if you imported the raw tables from
`ecommerce.db` instead of the pre-aggregated CSVs — the formulas below
assume you're working from `monthly_trends`, `kpi_summary`, and
`rfm_customer_segments`.

```dax
Total Revenue = SUM(kpi_summary[total_revenue])

Total Profit = SUM(kpi_summary[total_profit])

Total Orders = SUM(kpi_summary[total_orders])

Total Customers = SUM(kpi_summary[total_customers])

Average Order Value = DIVIDE([Total Revenue], [Total Orders])

Profit Margin % = DIVIDE([Total Profit], [Total Revenue])

Repeat Customer Rate =
    DIVIDE(
        COUNTROWS(FILTER(rfm_customer_segments, rfm_customer_segments[frequency] > 1)),
        COUNTROWS(rfm_customer_segments)
    )

Revenue MoM % =
    VAR CurrentMonthRevenue = SUM(monthly_trends[revenue])
    VAR PriorMonthRevenue =
        CALCULATE(
            SUM(monthly_trends[revenue]),
            DATEADD(monthly_trends[year_month], -1, MONTH)
        )
    RETURN DIVIDE(CurrentMonthRevenue - PriorMonthRevenue, PriorMonthRevenue)

Revenue YoY % =
    VAR CurrentRevenue = SUM(monthly_trends[revenue])
    VAR PriorYearRevenue =
        CALCULATE(
            SUM(monthly_trends[revenue]),
            DATEADD(monthly_trends[year_month], -1, YEAR)
        )
    RETURN DIVIDE(CurrentRevenue - PriorYearRevenue, PriorYearRevenue)

Average Delivery Days = AVERAGE(shipping_performance[avg_delivery_days])

Champions Revenue Share =
    VAR ChampionsRevenue =
        CALCULATE(
            SUM(rfm_segment_summary[total_revenue]),
            rfm_segment_summary[segment] = "Champions"
        )
    RETURN DIVIDE(ChampionsRevenue, SUM(rfm_segment_summary[total_revenue]))

High Revenue Low Margin Flag =
    IF(
        [Total Revenue] > CALCULATE([Total Revenue], ALL(category_performance)) * 0.05
            && category_performance[profit_margin_pct] < 30,
        "Review Pricing",
        "OK"
    )
```

**Notes:**
- `monthly_trends[year_month]` is a text column (e.g. `"2023-07"`). For
  `DATEADD`-based time intelligence to work, add a proper Date column
  (Power Query: `Date.FromText(year_month & "-01")`) and mark it as a
  Date table in the model, or replace the DATEADD measures with
  `LOOKUPVALUE`-based prior-period lookups against the text key.
- `Champions Revenue Share` and `High Revenue Low Margin Flag` are
  illustrative starting points — adjust thresholds to match actual
  stakeholder-agreed definitions.

## 5. Calculated columns (Power Query / DAX)

- **Delivery Bucket** (if working from raw `orders`/`shipping` tables
  instead of the pre-bucketed CSV):
  ```dax
  Delivery Bucket =
      SWITCH(
          TRUE(),
          shipping[avg_delivery_days] <= 3, "0-3 days",
          shipping[avg_delivery_days] <= 5, "4-5 days",
          shipping[avg_delivery_days] <= 7, "6-7 days",
          shipping[avg_delivery_days] <= 10, "8-10 days",
          "10+ days"
      )
  ```
- **Revenue Bucket** (customer segmentation column, if building from raw
  `customer_lifetime_value`):
  ```dax
  Revenue Bucket =
      SWITCH(
          TRUE(),
          customer_lifetime_value[total_revenue] < 5000, "Under 5K",
          customer_lifetime_value[total_revenue] < 20000, "5K-20K",
          customer_lifetime_value[total_revenue] < 50000, "20K-50K",
          customer_lifetime_value[total_revenue] < 150000, "50K-150K",
          "150K+"
      )
  ```

## 6. Suggested slicers & filters (global, applied via the Filters pane on every page)

- Date range (`monthly_trends[year_month]` or a proper Date table)
- `category`
- `state`
- `segment` (RFM)

## 7. Layout notes

- Use a consistent color per RFM segment across every page (set once via
  a color-by-field on `rfm_customer_segments[segment]` and Power BI will
  remember it across visuals in the same report).
- KPI cards belong at the top of Page 1, above the fold, in a single row.
- Keep the Executive Overview page to 5-6 visuals maximum — it's meant
  to be read in under 30 seconds by a stakeholder.
