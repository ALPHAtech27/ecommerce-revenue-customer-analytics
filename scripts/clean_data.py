"""
clean_data.py
--------------
Loads the raw CSVs from data/raw/, detects and fixes realistic data
quality issues, validates referential integrity across tables, and
writes cleaned CSVs to data/processed/.

Run:
    python scripts/clean_data.py
"""

import os
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def load_raw():
    tables = {}
    for name in ["customers", "products", "orders", "order_items", "payments", "shipping", "reviews"]:
        path = os.path.join(RAW_DIR, f"{name}.csv")
        tables[name] = pd.read_csv(path)
    return tables


def clean_customers(df):
    before = len(df)
    dup_before = df.duplicated().sum()

    df = df.drop_duplicates().copy()

    # standardize text fields
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["state"] = df["state"].astype(str).str.strip().str.title()
    df["customer_name"] = df["customer_name"].astype(str).str.strip()
    df["gender"] = df["gender"].astype(str).str.strip().str.title()

    # dates
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")

    # invalid ages -> null, then impute with median age
    invalid_age_mask = (df["age"] < 13) | (df["age"] > 100)
    n_invalid_age = invalid_age_mask.sum()
    df.loc[invalid_age_mask, "age"] = np.nan

    missing_age = df["age"].isna().sum()
    median_age = df["age"].median()
    df["age"] = df["age"].fillna(median_age).astype(int)

    missing_email = df["email"].isna().sum()
    df["email"] = df["email"].fillna("unknown@unknown.com")

    after = len(df)
    print(f"  Raw customers: {before:,}")
    print(f"  Exact duplicates removed: {dup_before:,}")
    print(f"  Invalid ages corrected: {n_invalid_age:,}")
    print(f"  Missing ages imputed (median={median_age:.0f}): {missing_age:,}")
    print(f"  Missing emails filled: {missing_email:,}")
    print(f"  Final customers: {after:,}")

    return df


def clean_products(df):
    before = len(df)
    df = df.drop_duplicates(subset=["product_id"]).copy()

    df["category"] = df["category"].astype(str).str.strip().str.title()
    df["sub_category"] = df["sub_category"].astype(str).str.strip().str.title()
    df["brand"] = df["brand"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()

    missing_cost = df["cost_price"].isna().sum()
    # impute missing cost price using category median
    df["cost_price"] = df.groupby("category")["cost_price"].transform(
        lambda s: s.fillna(s.median())
    )

    # guard against selling_price <= cost_price (data entry errors)
    bad_margin_mask = df["selling_price"] <= df["cost_price"]
    n_bad_margin = bad_margin_mask.sum()
    df.loc[bad_margin_mask, "selling_price"] = (df.loc[bad_margin_mask, "cost_price"] * 1.25).round(2)

    after = len(df)
    print(f"  Raw products: {before:,}")
    print(f"  Duplicate product_ids removed: {before - after:,}")
    print(f"  Missing cost_price imputed (category median): {missing_cost:,}")
    print(f"  Invalid margins corrected: {n_bad_margin:,}")
    print(f"  Final products: {after:,}")

    return df


def clean_orders(df, valid_customer_ids):
    before = len(df)
    dup_before = df.duplicated(subset=["order_id"]).sum()
    df = df.drop_duplicates(subset=["order_id"]).copy()

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["shipping_date"] = pd.to_datetime(df["shipping_date"], errors="coerce")
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")

    missing_status = df["order_status"].isna().sum()
    df["order_status"] = df["order_status"].fillna("Unknown")
    df["order_status"] = df["order_status"].astype(str).str.strip().str.title()

    # fix delivery_date < order_date (impossible) -> set to null
    bad_delivery_mask = df["delivery_date"] < df["order_date"]
    n_bad_delivery = bad_delivery_mask.sum()
    df.loc[bad_delivery_mask, "delivery_date"] = pd.NaT

    # referential integrity: drop orders for customers that don't exist
    fk_before = len(df)
    df = df[df["customer_id"].isin(valid_customer_ids)]
    fk_dropped = fk_before - len(df)

    after = len(df)
    print(f"  Raw orders: {before:,}")
    print(f"  Duplicate order_ids removed: {dup_before:,}")
    print(f"  Missing order_status filled as 'Unknown': {missing_status:,}")
    print(f"  Invalid delivery dates corrected: {n_bad_delivery:,}")
    print(f"  Orders with invalid customer_id removed: {fk_dropped:,}")
    print(f"  Final orders: {after:,}")

    return df


def clean_order_items(df, valid_order_ids, valid_product_ids):
    before = len(df)

    # remove invalid quantities (<=0 or absurd outliers > 50)
    bad_qty_mask = (df["quantity"] <= 0) | (df["quantity"] > 50)
    n_bad_qty = bad_qty_mask.sum()
    df = df[~bad_qty_mask].copy()

    missing_price = df["unit_price"].isna().sum()
    df["unit_price"] = df.groupby("product_id")["unit_price"].transform(
        lambda s: s.fillna(s.median())
    )
    # if still missing (product had no valid prices at all), drop
    df = df.dropna(subset=["unit_price"])

    df["discount"] = df["discount"].fillna(0).clip(0, 0.9)

    fk_before = len(df)
    df = df[df["order_id"].isin(valid_order_ids) & df["product_id"].isin(valid_product_ids)]
    fk_dropped = fk_before - len(df)

    after = len(df)
    print(f"  Raw order_items: {before:,}")
    print(f"  Invalid quantities removed: {n_bad_qty:,}")
    print(f"  Missing unit_price imputed (product median): {missing_price:,}")
    print(f"  Orphaned rows (bad order/product FK) removed: {fk_dropped:,}")
    print(f"  Final order_items: {after:,}")

    return df


def clean_payments(df, valid_order_ids):
    before = len(df)
    df = df.drop_duplicates(subset=["payment_id"]).copy()

    missing_amt = df["payment_amount"].isna().sum()
    df["payment_amount"] = df["payment_amount"].fillna(0)
    df["payment_amount"] = df["payment_amount"].clip(lower=0)

    df["payment_method"] = df["payment_method"].astype(str).str.strip().str.title()
    df["payment_status"] = df["payment_status"].astype(str).str.strip().str.title()

    fk_before = len(df)
    df = df[df["order_id"].isin(valid_order_ids)]
    fk_dropped = fk_before - len(df)

    after = len(df)
    print(f"  Raw payments: {before:,}")
    print(f"  Missing payment_amount filled with 0: {missing_amt:,}")
    print(f"  Orphaned rows (bad order FK) removed: {fk_dropped:,}")
    print(f"  Final payments: {after:,}")

    return df


def clean_shipping(df, valid_order_ids):
    before = len(df)
    df = df.drop_duplicates(subset=["shipping_id"]).copy()
    # each order has exactly one shipment in this schema -- keep the first
    # shipping record per order_id (duplicates come from upstream duplicate
    # order rows that slipped into shipping generation)
    df = df.drop_duplicates(subset=["order_id"]).copy()

    df["shipping_date"] = pd.to_datetime(df["shipping_date"], errors="coerce")
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")
    df["shipping_method"] = df["shipping_method"].astype(str).str.strip().str.title()

    missing_cost = df["shipping_cost"].isna().sum()
    df["shipping_cost"] = df.groupby("shipping_method")["shipping_cost"].transform(
        lambda s: s.fillna(s.median())
    )

    fk_before = len(df)
    df = df[df["order_id"].isin(valid_order_ids)]
    fk_dropped = fk_before - len(df)

    after = len(df)
    print(f"  Raw shipping: {before:,}")
    print(f"  Duplicate order_id shipments removed: {before - len(df) - fk_dropped if before - len(df) - fk_dropped > 0 else 0:,}")
    print(f"  Missing shipping_cost imputed (method median): {missing_cost:,}")
    print(f"  Orphaned rows (bad order FK) removed: {fk_dropped:,}")
    print(f"  Final shipping: {after:,}")

    return df


def clean_reviews(df, valid_order_ids, valid_customer_ids, valid_product_ids):
    before = len(df)
    df = df.drop_duplicates(subset=["review_id"]).copy()
    # this dataset models one review per order -- drop stray duplicates
    # caused by upstream duplicate order rows
    df = df.drop_duplicates(subset=["order_id"]).copy()

    missing_rating = df["rating"].isna().sum()
    df["rating"] = df["rating"].fillna(df["rating"].median())
    df["rating"] = df["rating"].round().astype(int).clip(1, 5)

    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")

    fk_before = len(df)
    df = df[
        df["order_id"].isin(valid_order_ids)
        & df["customer_id"].isin(valid_customer_ids)
        & df["product_id"].isin(valid_product_ids)
    ]
    fk_dropped = fk_before - len(df)

    after = len(df)
    print(f"  Raw reviews: {before:,}")
    print(f"  Missing ratings imputed (median): {missing_rating:,}")
    print(f"  Orphaned rows (bad FK) removed: {fk_dropped:,}")
    print(f"  Final reviews: {after:,}")

    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("=" * 50)
    print("DATA CLEANING PIPELINE")
    print("=" * 50)

    raw = load_raw()

    print("\n[1/7] Cleaning customers...")
    customers = clean_customers(raw["customers"])

    print("\n[2/7] Cleaning products...")
    products = clean_products(raw["products"])

    valid_customer_ids = set(customers["customer_id"])
    valid_product_ids = set(products["product_id"])

    print("\n[3/7] Cleaning orders...")
    orders = clean_orders(raw["orders"], valid_customer_ids)
    valid_order_ids = set(orders["order_id"])

    print("\n[4/7] Cleaning order_items...")
    order_items = clean_order_items(raw["order_items"], valid_order_ids, valid_product_ids)

    print("\n[5/7] Cleaning payments...")
    payments = clean_payments(raw["payments"], valid_order_ids)

    print("\n[6/7] Cleaning shipping...")
    shipping = clean_shipping(raw["shipping"], valid_order_ids)

    print("\n[7/7] Cleaning reviews...")
    reviews = clean_reviews(raw["reviews"], valid_order_ids, valid_customer_ids, valid_product_ids)

    # save
    customers.to_csv(os.path.join(PROCESSED_DIR, "customers_clean.csv"), index=False)
    products.to_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"), index=False)
    orders.to_csv(os.path.join(PROCESSED_DIR, "orders_clean.csv"), index=False)
    order_items.to_csv(os.path.join(PROCESSED_DIR, "order_items_clean.csv"), index=False)
    payments.to_csv(os.path.join(PROCESSED_DIR, "payments_clean.csv"), index=False)
    shipping.to_csv(os.path.join(PROCESSED_DIR, "shipping_clean.csv"), index=False)
    reviews.to_csv(os.path.join(PROCESSED_DIR, "reviews_clean.csv"), index=False)

    print("\n" + "-" * 50)
    print("DATA QUALITY SUMMARY")
    print("-" * 50)
    summary = pd.DataFrame({
        "table": ["customers", "products", "orders", "order_items", "payments", "shipping", "reviews"],
        "raw_rows": [len(raw["customers"]), len(raw["products"]), len(raw["orders"]),
                     len(raw["order_items"]), len(raw["payments"]), len(raw["shipping"]), len(raw["reviews"])],
        "clean_rows": [len(customers), len(products), len(orders), len(order_items),
                        len(payments), len(shipping), len(reviews)],
    })
    summary["rows_removed"] = summary["raw_rows"] - summary["clean_rows"]
    print(summary.to_string(index=False))

    print(f"\nCleaned data saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
