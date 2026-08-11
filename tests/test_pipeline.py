"""
test_pipeline.py
-----------------
Lightweight test suite (pytest) that validates the outputs of the
analytics pipeline: file existence, expected columns, primary-key
uniqueness, referential integrity, valid value ranges, and that
calculated revenue matches a manual recomputation.

Run (from the project root, after running scripts/run_pipeline.py):
    pytest tests/test_pipeline.py -v
"""

import os
import sys
import subprocess
import numpy as np
import pandas as pd
import pytest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DASH_DIR = os.path.join(PROJECT_ROOT, "dashboard", "dashboard_data")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def customers():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "customers_clean.csv"))


@pytest.fixture(scope="module")
def products():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"))


@pytest.fixture(scope="module")
def orders():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "orders_clean.csv"), parse_dates=["order_date"])


@pytest.fixture(scope="module")
def orders_enriched():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "orders_enriched.csv"), parse_dates=["order_date"])


@pytest.fixture(scope="module")
def order_items():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "order_items_clean.csv"))


@pytest.fixture(scope="module")
def order_items_enriched():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "order_items_enriched.csv"))


@pytest.fixture(scope="module")
def rfm():
    return pd.read_csv(os.path.join(PROCESSED_DIR, "rfm_customer_segments.csv"))


# ---------------------------------------------------------------------------
# 1. File existence
# ---------------------------------------------------------------------------
class TestFileExistence:
    EXPECTED_RAW = [
        "customers.csv", "products.csv", "orders.csv", "order_items.csv",
        "payments.csv", "shipping.csv", "reviews.csv",
    ]
    EXPECTED_PROCESSED = [
        "customers_clean.csv", "products_clean.csv", "orders_clean.csv",
        "order_items_clean.csv", "payments_clean.csv", "shipping_clean.csv",
        "reviews_clean.csv", "orders_enriched.csv", "order_items_enriched.csv",
        "customer_features.csv", "rfm_customer_segments.csv",
        "rfm_segment_summary.csv", "customer_lifetime_value.csv",
    ]
    EXPECTED_DASHBOARD = [
        "kpi_summary.csv", "monthly_trends.csv", "category_performance.csv",
        "product_performance.csv", "geographic_performance.csv",
        "payment_method_performance.csv", "shipping_performance.csv",
        "rating_by_category.csv", "rfm_customer_segments.csv",
        "customer_lifetime_value.csv",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_RAW)
    def test_raw_file_exists(self, filename):
        assert os.path.exists(os.path.join(RAW_DIR, filename)), f"Missing raw file: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_PROCESSED)
    def test_processed_file_exists(self, filename):
        assert os.path.exists(os.path.join(PROCESSED_DIR, filename)), f"Missing processed file: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARD)
    def test_dashboard_file_exists(self, filename):
        assert os.path.exists(os.path.join(DASH_DIR, filename)), f"Missing dashboard file: {filename}"


# ---------------------------------------------------------------------------
# 2. Expected columns
# ---------------------------------------------------------------------------
class TestSchema:
    def test_customers_columns(self, customers):
        expected = {"customer_id", "customer_name", "email", "gender", "age", "city", "state", "signup_date"}
        assert expected.issubset(set(customers.columns))

    def test_orders_enriched_columns(self, orders_enriched):
        expected = {
            "order_id", "customer_id", "order_date", "order_status", "revenue",
            "cost", "profit", "profit_margin", "order_month", "order_year",
            "delivery_days", "is_repeat_customer", "customer_order_count",
        }
        assert expected.issubset(set(orders_enriched.columns))

    def test_rfm_columns(self, rfm):
        expected = {"customer_id", "recency", "frequency", "monetary", "R_score",
                     "F_score", "M_score", "segment"}
        assert expected.issubset(set(rfm.columns))


# ---------------------------------------------------------------------------
# 3. Primary key uniqueness
# ---------------------------------------------------------------------------
class TestPrimaryKeys:
    def test_customer_id_unique(self, customers):
        assert customers["customer_id"].is_unique

    def test_product_id_unique(self, products):
        assert products["product_id"].is_unique

    def test_order_id_unique(self, orders):
        assert orders["order_id"].is_unique

    def test_rfm_customer_id_unique(self, rfm):
        assert rfm["customer_id"].is_unique


# ---------------------------------------------------------------------------
# 4. Value validity
# ---------------------------------------------------------------------------
class TestValueValidity:
    def test_no_negative_revenue(self, orders_enriched):
        assert (orders_enriched["revenue"] >= 0).all()

    def test_no_negative_order_item_revenue(self, order_items_enriched):
        assert (order_items_enriched["revenue"] >= 0).all()

    def test_quantities_positive(self, order_items):
        assert (order_items["quantity"] > 0).all()

    def test_ages_within_reasonable_range(self, customers):
        assert customers["age"].between(13, 100).all()

    def test_rfm_scores_within_range(self, rfm):
        for col in ["R_score", "F_score", "M_score"]:
            assert rfm[col].between(1, 5).all()

    def test_rfm_segments_are_valid(self, rfm):
        valid_segments = {
            "Champions", "Loyal Customers", "Potential Loyalists", "New Customers",
            "At Risk", "Can't Lose Them", "Hibernating", "Lost",
        }
        assert set(rfm["segment"].unique()).issubset(valid_segments)

    def test_dates_are_valid(self, orders):
        assert orders["order_date"].notna().all()
        assert orders["order_date"].min() >= pd.Timestamp("2020-01-01")
        assert orders["order_date"].max() <= pd.Timestamp("2030-01-01")

    def test_delivery_date_not_before_order_date(self, orders_enriched):
        oe = orders_enriched.dropna(subset=["delivery_date"]) if "delivery_date" in orders_enriched.columns else orders_enriched
        if "delivery_date" in orders_enriched.columns:
            oe = orders_enriched.dropna(subset=["delivery_date"]).copy()
            oe["delivery_date"] = pd.to_datetime(oe["delivery_date"])
            oe["order_date"] = pd.to_datetime(oe["order_date"])
            assert (oe["delivery_date"] >= oe["order_date"]).all()


# ---------------------------------------------------------------------------
# 5. Referential integrity
# ---------------------------------------------------------------------------
class TestReferentialIntegrity:
    def test_orders_reference_valid_customers(self, orders, customers):
        valid_ids = set(customers["customer_id"])
        assert orders["customer_id"].isin(valid_ids).all()

    def test_order_items_reference_valid_orders(self, order_items, orders):
        valid_ids = set(orders["order_id"])
        assert order_items["order_id"].isin(valid_ids).all()

    def test_order_items_reference_valid_products(self, order_items, products):
        valid_ids = set(products["product_id"])
        assert order_items["product_id"].isin(valid_ids).all()

    def test_rfm_references_valid_customers(self, rfm, customers):
        valid_ids = set(customers["customer_id"])
        assert rfm["customer_id"].isin(valid_ids).all()


# ---------------------------------------------------------------------------
# 6. Calculated revenue correctness
# ---------------------------------------------------------------------------
class TestCalculations:
    def test_order_item_revenue_formula(self, order_items_enriched):
        recomputed = (
            order_items_enriched["quantity"]
            * order_items_enriched["unit_price"]
            * (1 - order_items_enriched["discount"])
        ).round(2)
        assert np.allclose(order_items_enriched["revenue"], recomputed, atol=0.05)

    def test_order_item_profit_formula(self, order_items_enriched):
        recomputed = (order_items_enriched["revenue"] - order_items_enriched["cost"]).round(2)
        assert np.allclose(order_items_enriched["profit"], recomputed, atol=0.05)

    def test_orders_enriched_revenue_matches_item_sum(self, orders_enriched, order_items_enriched):
        item_sum = order_items_enriched.groupby("order_id")["revenue"].sum()
        merged = orders_enriched.set_index("order_id")["revenue"]
        common_ids = item_sum.index.intersection(merged.index)
        assert np.allclose(
            item_sum.loc[common_ids].values,
            merged.loc[common_ids].values,
            atol=0.05,
        )


# ---------------------------------------------------------------------------
# 7. Full pipeline smoke test (runs the pipeline end-to-end)
# ---------------------------------------------------------------------------
def test_pipeline_runs_successfully():
    """
    This is a slower integration test that re-runs the entire pipeline
    from scratch and confirms it exits with code 0. Skip with:
        pytest tests/test_pipeline.py -v -k "not pipeline_runs"
    """
    script_path = os.path.join(PROJECT_ROOT, "scripts", "run_pipeline.py")
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=os.path.join(PROJECT_ROOT, "scripts"),
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Pipeline failed:\n{result.stdout}\n{result.stderr}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
