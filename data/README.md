# Data Folder

## ⚠️ This is synthetic data

Every file in `raw/` and `processed/` is **generated programmatically**
by `scripts/generate_data.py` using a fixed random seed (`42`). No real
customer, order, or transaction data is used anywhere in this project.
The dataset is designed to *look and behave* like a realistic e-commerce
export (including realistic data quality issues), purely for portfolio
and learning purposes.

## Folder structure

```
data/
├── raw/           - Output of generate_data.py (includes intentional
│                    data quality issues: missing values, duplicates,
│                    inconsistent casing, a few invalid dates/values)
├── processed/     - Output of clean_data.py, feature_engineering.py,
│                    and rfm_segmentation.py (cleaned + enriched tables,
│                    plus a SQLite database for the sql/ queries)
└── README.md      - This file
```

## Regenerating the data

Neither `raw/` nor `processed/` needs to be committed to version control
for the project to work — everything is reproducible from scratch:

```bash
python scripts/run_pipeline.py
```

This regenerates `raw/`, `processed/`, and `dashboard/dashboard_data/`
in one command, in under a minute. See the main `README.md` for full
setup instructions.

## Why these files ARE included in this repo

Even though the data is reproducible, the processed CSVs are committed
so that:
1. The notebooks can be opened and read (with cached outputs) without
   first running the pipeline.
2. The Power BI dashboard can be built immediately from
   `dashboard/dashboard_data/` without a Python environment.
3. Reviewers (e.g. in a technical interview) can inspect real output
   files directly on GitHub.

If you fork this project and want a smaller repository, add `data/raw/`
and `data/processed/` to `.gitignore` and instruct users to run
`python scripts/run_pipeline.py` after cloning.

## A note on file size

`data/processed/ecommerce.db` (~84 MB) is the largest file in this
repository — it's under GitHub's 100 MB hard limit but above the 50 MB
warning threshold. If you outgrow it (e.g. by increasing `N_ORDERS` in
`generate_data.py`), either delete `data/raw/`, `data/processed/`, and
`dashboard/dashboard_data/` from version control (they regenerate with
`python scripts/run_pipeline.py`) or switch to
[Git LFS](https://git-lfs.com/) for the `.db` and large `.csv` files.
