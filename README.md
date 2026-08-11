# E-Commerce Revenue & Customer Analytics

An end-to-end analytics project for a synthetic e-commerce business:
data generation → cleaning → feature engineering → RFM segmentation →
SQL analysis → EDA notebooks → Power BI-ready dashboard datasets →
business recommendations.

Built to demonstrate a realistic, complete analytics workflow — the kind
of project a Data Analyst would actually ship, not a toy tutorial.

---

## ⚠️ About the data

This project uses a **synthetic** dataset (50,000 customers, 320
products, 110,000 orders) generated with a fixed random seed for full
reproducibility. It is designed to look and behave like a real
e-commerce export, including realistic data quality issues that the
cleaning pipeline detects and fixes. **No real customer or transaction
data is used anywhere in this repository.** See `data/README.md` for
details.

---

## Business problem

An e-commerce company wants to understand revenue performance,
product/category performance, customer behavior and lifetime value,
repeat-purchase patterns, customer segmentation, geographic performance,
payment behavior, review/satisfaction trends, and shipping performance —
and turn all of it into concrete, prioritized recommendations rather
than a pile of disconnected charts.

## Objectives

1. Build a reproducible data pipeline from raw synthetic data to
   analysis-ready tables
2. Quantify revenue, profit, and growth trends
3. Segment customers using RFM analysis and estimate Customer Lifetime
   Value (CLV)
4. Identify where high revenue does **not** translate to high profit
5. Surface geographic, payment, and shipping performance patterns
6. Translate all of the above into prioritized business recommendations
7. Package the analysis as SQL queries, Jupyter notebooks, and a Power
   BI-ready dashboard

## Key results (from the synthetic dataset)

| Metric | Value |
|---|---|
| Total Revenue (valid orders) | Rs 1,337,315,331 |
| Total Profit | Rs 418,207,478 |
| Profit Margin | 31.27% |
| Active Customers | 31,034 |
| Repeat Purchase Rate (active customers) | 59.10% |
| Champions' share of revenue | 56.9% (from 20.8% of customers) |

Full findings: [`reports/executive_summary.md`](reports/executive_summary.md) ·
Recommendations: [`reports/business_recommendations.md`](reports/business_recommendations.md)

---

## Architecture

```
Synthetic data generation (Python/NumPy/pandas)
            │
            ▼
   Data cleaning & validation
            │
            ▼
     Feature engineering
    (revenue, profit, dates,
     repeat-customer flags)
            │
            ▼
     RFM segmentation
     & CLV estimation
            │
     ┌──────┴──────┐
     ▼             ▼
 SQLite DB     Dashboard CSVs
 (sql/ queries) (Power BI)
     │             │
     ▼             ▼
 Notebooks      Dashboard
 (EDA, insights) (5-page guide)
```

## Tech stack

- **Python**: pandas, NumPy, Matplotlib, Seaborn, scikit-learn (KMeans
  cross-validation of RFM segments)
- **SQL**: SQLite (via Python's built-in `sqlite3`), PostgreSQL-compatible
  syntax
- **Jupyter Notebook** for EDA and analysis narrative
- **Power BI**: dashboard-ready CSV extracts + DAX measure guide
- **pytest** for pipeline testing

## Project structure

```
ecommerce-revenue-customer-analytics/
├── data/
│   ├── raw/                        # Synthetic source data (generate_data.py output)
│   ├── processed/                  # Cleaned & feature-engineered data + SQLite DB
│   └── README.md
│
├── notebooks/
│   ├── 01_data_quality_and_eda.ipynb
│   ├── 02_customer_analysis.ipynb
│   ├── 03_rfm_segmentation.ipynb
│   └── 04_business_insights.ipynb
│
├── sql/
│   ├── 01_data_quality.sql
│   ├── 02_revenue_analysis.sql
│   ├── 03_customer_analysis.sql
│   ├── 04_product_analysis.sql
│   ├── 05_rfm_analysis.sql
│   └── 06_business_questions.sql
│
├── scripts/
│   ├── generate_data.py            # Synthetic dataset generator (seed=42)
│   ├── clean_data.py                # Cleaning & validation pipeline
│   ├── feature_engineering.py       # Revenue/profit/date features
│   ├── rfm_segmentation.py          # RFM scoring & segmentation
│   ├── generate_dashboard_data.py   # Power BI CSVs + CLV + SQLite DB
│   └── run_pipeline.py              # Orchestrates all of the above
│
├── dashboard/
│   ├── dashboard_data/              # Power BI-ready CSV extracts
│   ├── screenshots/
│   └── powerbi_dashboard_guide.md   # Build guide + DAX measures
│
├── reports/
│   ├── executive_summary.md
│   ├── business_recommendations.md
│   └── data_dictionary.md
│
├── tests/
│   └── test_pipeline.py             # pytest suite
│
├── images/
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

## Data pipeline

1. **Generate** (`scripts/generate_data.py`): builds 7 related tables
   (customers, products, orders, order_items, payments, shipping,
   reviews) with realistic distributions and intentionally injects
   missing values, duplicates, inconsistent text casing, and a few
   invalid dates/values.
2. **Clean** (`scripts/clean_data.py`): deduplicates, standardizes text,
   parses dates, imputes missing values (category/product medians),
   corrects invalid records, and enforces referential integrity across
   all 7 tables.
3. **Feature engineer** (`scripts/feature_engineering.py`): computes
   revenue, cost, profit, profit margin, discount amount, date parts,
   delivery days, repeat-customer flags, and customer-level aggregates.
4. **RFM segment** (`scripts/rfm_segmentation.py`): scores every active
   customer on Recency/Frequency/Monetary (quintiles) and assigns one of
   8 business segments.
5. **Dashboard data** (`scripts/generate_dashboard_data.py`): builds
   Customer Lifetime Value, all Power BI CSV extracts, and a SQLite
   database (`data/processed/ecommerce.db`) for the `sql/` queries.

## RFM segmentation

Segments: **Champions, Loyal Customers, Potential Loyalists, New
Customers, At Risk, Can't Lose Them, Hibernating, Lost.** Full scoring
logic and segment definitions in `scripts/rfm_segmentation.py` and
`reports/data_dictionary.md`.

## Customer Lifetime Value (CLV)

A practical, assumption-based CLV estimate:

```
CLV = Average Order Value × (Orders per Month of Tenure)
      × (Estimated Lifespan in Months, capped at 36)
```

Full formula, assumptions, and caveats documented in
`scripts/generate_dashboard_data.py::compute_clv()`.

## SQL analysis

6 files, 50+ business-question queries covering `SELECT`/`WHERE`/
`GROUP BY`/`HAVING`/`CASE WHEN`, joins, CTEs, subqueries, and window
functions (`RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`, `SUM() OVER()`,
rolling averages). Every statement has been executed against the real
generated dataset. See `sql/`.

## Power BI dashboard

5-page dashboard (Executive Overview, Customer Analytics, Product
Analytics, Operations, Geographic Analysis) with recommended
relationships, DAX measures, calculated columns, slicers, and
drill-through suggestions. See `dashboard/powerbi_dashboard_guide.md`.

## Key business insights

See `reports/executive_summary.md` for the full write-up. Highlights:

- Champions (20.8% of customers) generate 56.9% of revenue — a classic
  Pareto concentration
- Only 36.68% of registered customers ever place a second order
- Discount depth beyond 20% erodes margin faster than it grows volume
- At Risk / Can't Lose Them segments represent Rs 70.4M in dormant,
  historically-proven revenue

## Recommendations

10 prioritized, evidence-linked recommendations in
`reports/business_recommendations.md` — from retention program design
to discount policy review to payment-failure diagnosis.

---

## How to run

### Prerequisites

- Python 3.10+ installed and on your PATH
- Windows, macOS, or Linux (all commands below use relative paths and
  work identically across platforms)

### 1. Clone and set up a virtual environment

```bash
git clone https://github.com/<your-username>/ecommerce-revenue-customer-analytics.git
cd ecommerce-revenue-customer-analytics

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
python scripts/run_pipeline.py
```

Expected output (abbreviated):

```
==================================================
E-COMMERCE ANALYTICS PIPELINE
==================================================

[1/5] Generating data...
Customers generated: 50,200
...
[2/5] Cleaning data...
...
[3/5] Feature engineering...
...
[4/5] RFM segmentation...
...
[5/5] Dashboard outputs...
...

==================================================
Pipeline completed successfully in ~35 seconds.
==================================================
```

This populates `data/raw/`, `data/processed/` (including
`ecommerce.db`), and `dashboard/dashboard_data/`.

### 3. Run individual pipeline steps (optional)

```bash
python scripts/generate_data.py
python scripts/clean_data.py
python scripts/feature_engineering.py
python scripts/rfm_segmentation.py
python scripts/generate_dashboard_data.py
```

### 4. Run the test suite

```bash
pytest tests/test_pipeline.py -v
```

### 5. Explore the notebooks

```bash
jupyter notebook notebooks/
```

Open each notebook in order (01 → 04). All notebooks use relative paths
(`../data/processed/...`) and will run top-to-bottom without edits, as
long as `run_pipeline.py` has been run at least once first.

### 6. Run the SQL queries

Using the `sqlite3` CLI:

```bash
sqlite3 data/processed/ecommerce.db < sql/02_revenue_analysis.sql
```

Or open `data/processed/ecommerce.db` in a GUI tool like
[DB Browser for SQLite](https://sqlitebrowser.org/) and paste queries
from any file in `sql/`.

### 7. Build the Power BI dashboard

Follow `dashboard/powerbi_dashboard_guide.md`, importing CSVs from
`dashboard/dashboard_data/`.

---

## Results

- Fully reproducible pipeline: raw data → cleaned data → features →
  segments → dashboard, in under a minute
- 52 tested SQL statements across 6 files with zero execution errors
- 4 notebooks, all executing top-to-bottom without errors
- pytest suite covering schema, primary keys, referential integrity,
  value ranges, and calculated-field correctness
- 10 evidence-linked business recommendations

## Limitations

- **Synthetic data**: patterns are realistic but generated, not
  observed. Some relationships that would typically show a strong signal
  in real data (e.g. delivery time vs. review rating) are weak in this
  particular sample because they weren't deliberately correlated during
  generation — see the note at the end of
  `reports/business_recommendations.md`.
- **CLV formula** is a practical, assumption-based estimate (documented
  in `scripts/generate_dashboard_data.py`), not a churn-model-based
  prediction.
- **RFM quintile thresholds** are relative to this dataset's
  distribution and would need to be re-validated against a real customer
  base before being used operationally.

## Future improvements

- Add a churn-prediction model (e.g. gradient boosting on recency/
  frequency/tenure features) to complement the RFM segmentation
- Incorporate marketing-spend/channel data to compute actual CAC and
  validate the CLV-based acquisition-spend recommendations
- Add cohort retention curves (month-1, month-3, month-6 repeat rates by
  signup cohort)
- Automate the pipeline as a scheduled job (e.g. Airflow/Prefect) against
  a live warehouse instead of a static synthetic snapshot
- Publish the `.pbix` file once a stable Power BI Desktop environment is
  available (currently omitted — see `dashboard/powerbi_dashboard_guide.md`)

## Author

Built as a self-directed portfolio project to demonstrate an end-to-end
Data Analyst workflow: data engineering, SQL, Python/pandas analysis,
statistical customer segmentation, and business communication.
