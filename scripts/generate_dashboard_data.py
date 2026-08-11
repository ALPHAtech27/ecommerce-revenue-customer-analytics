"""
generate_dashboard_data.py
---------------------------
Produces every Power BI-ready CSV extract used by the dashboard (see
dashboard/powerbi_dashboard_guide.md), plus the Customer Lifetime Value
(CLV) table.

All outputs are written to dashboard/dashboard_data/.

Run:
    python scripts/generate_dashboard_data.py
"""

import os
import sqlite3
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DASH_DIR = os.path.join(PROJECT_ROOT, "dashboard", "dashboard_data")


def build_sqlite_db():
    """
    Loads the cleaned/enriched tables into a SQLite database at
    data/processed/ecommerce.db so the SQL files in sql/ can be run
    directly (e.g. with DB Browser for SQLite, or `sqlite3` CLI).
    """
    db_path = os.path.join(PROCESSED_DIR, "ecommerce.db")
    conn = sqlite3.connect(db_path)

    table_files = {
        "customers": "customers_clean.csv",
        "products": "products_clean.csv",
        "orders": "orders_enriched.csv",
        "order_items": "order_items_enriched.csv",
        "payments": "payments_clean.csv",
        "shipping": "shipping_clean.csv",
        "reviews": "reviews_clean.csv",
        "rfm_segments": "rfm_customer_segments.csv",
    }

    for table_name, filename in table_files.items():
        df = pd.read_csv(os.path.join(PROCESSED_DIR, filename))
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    return db_path


def load():
    orders = pd.read_csv(os.path.join(PROCESSED_DIR, "orders_enriched.csv"), parse_dates=["order_date"])
    items = pd.read_csv(os.path.join(PROCESSED_DIR, "order_items_enriched.csv"))
    customers = pd.read_csv(os.path.join(PROCESSED_DIR, "customer_features.csv"))
    products = pd.read_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"))
    rfm = pd.read_csv(os.path.join(PROCESSED_DIR, "rfm_customer_segments.csv"))
    reviews = pd.read_csv(os.path.join(PROCESSED_DIR, "reviews_clean.csv"), parse_dates=["review_date"])
    shipping = pd.read_csv(
        os.path.join(PROCESSED_DIR, "shipping_clean.csv"),
        parse_dates=["shipping_date", "delivery_date"],
    )
    return orders, items, customers, products, rfm, reviews, shipping


def compute_clv(customers):
    """
    Practical, portfolio-level historical CLV.

    CLV = Average Order Value x Purchase Frequency (orders per active month)
          x Estimated Customer Lifespan (months)

    Assumptions (documented for interview transparency):
      - "Active" customers are those with >= 1 valid (non-cancelled) order.
      - Purchase frequency is measured as orders per month of observed
        tenure (customer_tenure_days / 30), floored at 1 month so brand
        new customers don't get a divide-by-zero / inflated frequency.
      - Estimated lifespan is capped at 36 months, a conservative assumption
        for an e-commerce vertical, and is derived from each customer's
        observed tenure scaled by a retention multiplier of 1.5x (i.e. we
        assume customers who have already stuck around tend to continue
        roughly 1.5x their tenure so far). This is a simplification, not a
        churn-model-based prediction -- it is meant to be directionally
        useful, not a guarantee.
    """
    df = customers.copy()
    df = df[df["order_count"] > 0].copy()

    tenure_months = (df["customer_tenure_days"] / 30).clip(lower=1)
    purchase_frequency = df["order_count"] / tenure_months

    estimated_lifespan_months = (tenure_months * 1.5).clip(upper=36)

    df["clv"] = (df["average_order_value"] * purchase_frequency * estimated_lifespan_months).round(2)
    df["clv_tier"] = pd.qcut(df["clv"].rank(method="first"), 4, labels=["Low", "Medium", "High", "Top"])

    return df[[
        "customer_id", "customer_name", "city", "state",
        "order_count", "total_revenue", "average_order_value",
        "customer_tenure_days", "clv", "clv_tier",
    ]]


def main():
    os.makedirs(DASH_DIR, exist_ok=True)

    print("=" * 50)
    print("GENERATING DASHBOARD-READY DATASETS")
    print("=" * 50)

    orders, items, customers, products, rfm, reviews, shipping = load()
    valid_orders = orders[orders["order_status"] != "Cancelled"].copy()

    # ---------------------------------------------------------------
    # 1. Executive KPI summary (single-row table -> Power BI card visuals)
    # ---------------------------------------------------------------
    print("\n[1/9] Executive KPI summary...")
    total_revenue = valid_orders["revenue"].sum()
    total_profit = valid_orders["profit"].sum()
    total_orders = len(valid_orders)
    total_customers = customers[customers["order_count"] > 0]["customer_id"].nunique()
    aov = total_revenue / total_orders
    repeat_rate = (customers["is_repeat_customer"].sum() / total_customers) * 100
    profit_margin = (total_profit / total_revenue) * 100

    kpi = pd.DataFrame([{
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "average_order_value": round(aov, 2),
        "repeat_purchase_rate_pct": round(repeat_rate, 2),
        "profit_margin_pct": round(profit_margin, 2),
    }])
    kpi.to_csv(os.path.join(DASH_DIR, "kpi_summary.csv"), index=False)
    print(f"  Saved kpi_summary.csv")

    # ---------------------------------------------------------------
    # 2. Monthly revenue / profit / orders trend
    # ---------------------------------------------------------------
    print("[2/9] Monthly revenue trend...")
    monthly = valid_orders.groupby("year_month").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "count"),
    ).reset_index().sort_values("year_month")
    monthly["revenue_mom_pct"] = (monthly["revenue"].pct_change() * 100).round(2)
    monthly["profit_mom_pct"] = (monthly["profit"].pct_change() * 100).round(2)
    monthly.to_csv(os.path.join(DASH_DIR, "monthly_trends.csv"), index=False)
    print(f"  Saved monthly_trends.csv ({len(monthly)} months)")

    # ---------------------------------------------------------------
    # 3. Category / sub-category performance
    # ---------------------------------------------------------------
    print("[3/9] Category performance...")
    item_orders = items.merge(valid_orders[["order_id"]], on="order_id", how="inner")
    category_perf = item_orders.groupby(["category", "sub_category"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        quantity=("quantity", "sum"),
        discount_amount=("discount_amount", "sum"),
    ).reset_index()
    category_perf["profit_margin_pct"] = (category_perf["profit"] / category_perf["revenue"] * 100).round(2)
    category_perf = category_perf.sort_values("revenue", ascending=False)
    category_perf.to_csv(os.path.join(DASH_DIR, "category_performance.csv"), index=False)
    print(f"  Saved category_performance.csv ({len(category_perf)} rows)")

    # ---------------------------------------------------------------
    # 4. Top products
    # ---------------------------------------------------------------
    print("[4/9] Product performance...")
    product_perf = item_orders.merge(
        products[["product_id", "product_name", "category", "brand"]].drop_duplicates("product_id"),
        on="product_id", how="left", suffixes=("", "_p"),
    )
    product_summary = product_perf.groupby(["product_id", "product_name", "category", "brand"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        quantity_sold=("quantity", "sum"),
    ).reset_index()
    product_summary["profit_margin_pct"] = (product_summary["profit"] / product_summary["revenue"] * 100).round(2)
    product_summary = product_summary.sort_values("revenue", ascending=False)
    product_summary.to_csv(os.path.join(DASH_DIR, "product_performance.csv"), index=False)
    print(f"  Saved product_performance.csv ({len(product_summary)} products)")

    # ---------------------------------------------------------------
    # 5. Geographic performance
    # ---------------------------------------------------------------
    print("[5/9] Geographic performance...")
    geo = valid_orders.groupby(["state", "city"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "count"),
        customers=("customer_id", "nunique"),
    ).reset_index()
    geo["average_order_value"] = (geo["revenue"] / geo["orders"]).round(2)
    geo = geo.sort_values("revenue", ascending=False)
    geo.to_csv(os.path.join(DASH_DIR, "geographic_performance.csv"), index=False)
    print(f"  Saved geographic_performance.csv ({len(geo)} city/state rows)")

    # ---------------------------------------------------------------
    # 6. Payment analysis
    # ---------------------------------------------------------------
    print("[6/9] Payment analysis...")
    payment_perf = orders.groupby("payment_method").agg(
        orders=("order_id", "count"),
        revenue=("revenue", "sum"),
    ).reset_index()
    payment_status = orders.groupby(["payment_method", "payment_status"]).size().reset_index(name="count")
    payment_perf.to_csv(os.path.join(DASH_DIR, "payment_method_performance.csv"), index=False)
    payment_status.to_csv(os.path.join(DASH_DIR, "payment_status_breakdown.csv"), index=False)
    print(f"  Saved payment_method_performance.csv, payment_status_breakdown.csv")

    # ---------------------------------------------------------------
    # 7. Shipping / delivery performance
    # ---------------------------------------------------------------
    print("[7/9] Shipping performance...")
    ship = shipping.merge(orders[["order_id", "delivery_days", "order_date"]], on="order_id", how="left")
    ship_perf = ship.groupby("shipping_method").agg(
        shipments=("shipping_id", "count"),
        avg_shipping_cost=("shipping_cost", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
    ).reset_index()
    ship_perf["avg_shipping_cost"] = ship_perf["avg_shipping_cost"].round(2)
    ship_perf["avg_delivery_days"] = ship_perf["avg_delivery_days"].round(2)
    ship_perf["late_delivery_rate_pct"] = (
        ship.assign(late=lambda d: d["delivery_days"] > 7)
        .groupby("shipping_method")["late"].mean() * 100
    ).round(2).values
    ship_perf.to_csv(os.path.join(DASH_DIR, "shipping_performance.csv"), index=False)
    print(f"  Saved shipping_performance.csv")

    # ---------------------------------------------------------------
    # 8. Review / rating analysis
    # ---------------------------------------------------------------
    print("[8/9] Review analysis...")
    review_products = reviews.merge(
        products[["product_id", "category"]].drop_duplicates("product_id"), on="product_id", how="left"
    )
    rating_by_category = review_products.groupby("category").agg(
        avg_rating=("rating", "mean"),
        review_count=("review_id", "count"),
    ).reset_index()
    rating_by_category["avg_rating"] = rating_by_category["avg_rating"].round(2)
    rating_by_category = rating_by_category.sort_values("avg_rating", ascending=False)
    rating_by_category.to_csv(os.path.join(DASH_DIR, "rating_by_category.csv"), index=False)

    rating_delivery = reviews.merge(
        orders[["order_id", "delivery_days"]], on="order_id", how="left"
    ).dropna(subset=["delivery_days"])
    rating_delivery["delivery_bucket"] = pd.cut(
        rating_delivery["delivery_days"],
        bins=[-1, 3, 5, 7, 10, 100],
        labels=["0-3 days", "4-5 days", "6-7 days", "8-10 days", "10+ days"],
    )
    rating_vs_delivery = rating_delivery.groupby("delivery_bucket", observed=True).agg(
        avg_rating=("rating", "mean"),
        review_count=("review_id", "count"),
    ).reset_index()
    rating_vs_delivery["avg_rating"] = rating_vs_delivery["avg_rating"].round(2)
    rating_vs_delivery.to_csv(os.path.join(DASH_DIR, "rating_vs_delivery_time.csv"), index=False)
    print(f"  Saved rating_by_category.csv, rating_vs_delivery_time.csv")

    # ---------------------------------------------------------------
    # 9. RFM + CLV extracts (copied/derived for dashboard convenience)
    # ---------------------------------------------------------------
    print("[9/9] RFM segment + CLV extracts...")
    rfm.to_csv(os.path.join(DASH_DIR, "rfm_customer_segments.csv"), index=False)

    segment_summary = pd.read_csv(os.path.join(PROCESSED_DIR, "rfm_segment_summary.csv"))
    segment_summary.to_csv(os.path.join(DASH_DIR, "rfm_segment_summary.csv"), index=False)

    clv = compute_clv(customers)
    clv.to_csv(os.path.join(PROCESSED_DIR, "customer_lifetime_value.csv"), index=False)
    clv.to_csv(os.path.join(DASH_DIR, "customer_lifetime_value.csv"), index=False)
    print(f"  Saved rfm extracts + customer_lifetime_value.csv ({len(clv)} customers)")
    print(f"  Average CLV: Rs {clv['clv'].mean():,.2f} | Median CLV: Rs {clv['clv'].median():,.2f}")

    print("\nBuilding SQLite database for sql/ queries...")
    db_path = build_sqlite_db()
    print(f"  Saved {db_path}")

    print("\nAll dashboard-ready datasets generated successfully.")
    print(f"Location: {DASH_DIR}")


if __name__ == "__main__":
    main()
