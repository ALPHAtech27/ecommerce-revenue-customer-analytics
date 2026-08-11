"""
feature_engineering.py
-----------------------
Builds the analytical "master" tables used by every downstream notebook,
SQL exploration, and dashboard export:

    data/processed/order_items_enriched.csv   -> line-item level with
                                                  revenue/cost/profit
    data/processed/orders_enriched.csv        -> order level with revenue,
                                                  profit, delivery_days, etc.
    data/processed/customer_features.csv      -> one row per customer with
                                                  order_count, AOV, revenue,
                                                  is_repeat_customer, etc.

Run:
    python scripts/feature_engineering.py
"""

import os
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def load_processed():
    customers = pd.read_csv(os.path.join(PROCESSED_DIR, "customers_clean.csv"), parse_dates=["signup_date"])
    products = pd.read_csv(os.path.join(PROCESSED_DIR, "products_clean.csv"))
    orders = pd.read_csv(
        os.path.join(PROCESSED_DIR, "orders_clean.csv"),
        parse_dates=["order_date", "shipping_date", "delivery_date"],
    )
    order_items = pd.read_csv(os.path.join(PROCESSED_DIR, "order_items_clean.csv"))
    payments = pd.read_csv(os.path.join(PROCESSED_DIR, "payments_clean.csv"))
    shipping = pd.read_csv(
        os.path.join(PROCESSED_DIR, "shipping_clean.csv"),
        parse_dates=["shipping_date", "delivery_date"],
    )
    reviews = pd.read_csv(os.path.join(PROCESSED_DIR, "reviews_clean.csv"), parse_dates=["review_date"])
    return customers, products, orders, order_items, payments, shipping, reviews


def build_order_items_enriched(order_items, products):
    df = order_items.merge(
        products[["product_id", "category", "sub_category", "brand", "cost_price", "selling_price"]],
        on="product_id",
        how="left",
    )

    # revenue = what the customer actually paid for this line item
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    df["discount_amount"] = (df["quantity"] * df["unit_price"] * df["discount"]).round(2)
    df["cost"] = (df["quantity"] * df["cost_price"]).round(2)
    df["profit"] = (df["revenue"] - df["cost"]).round(2)
    df["profit_margin"] = np.where(df["revenue"] > 0, (df["profit"] / df["revenue"]).round(4), 0)

    return df


def build_orders_enriched(orders, order_items_enriched, customers, payments, shipping):
    # aggregate line items up to order level
    order_agg = order_items_enriched.groupby("order_id").agg(
        revenue=("revenue", "sum"),
        cost=("cost", "sum"),
        profit=("profit", "sum"),
        discount_amount=("discount_amount", "sum"),
        item_count=("quantity", "sum"),
        distinct_products=("product_id", "nunique"),
    ).reset_index()

    df = orders.merge(order_agg, on="order_id", how="left")
    df[["revenue", "cost", "profit", "discount_amount", "item_count", "distinct_products"]] = (
        df[["revenue", "cost", "profit", "discount_amount", "item_count", "distinct_products"]].fillna(0)
    )
    df["profit_margin"] = np.where(df["revenue"] > 0, (df["profit"] / df["revenue"]).round(4), 0)

    # date parts
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["order_month_name"] = df["order_date"].dt.strftime("%b")
    df["order_week"] = df["order_date"].dt.isocalendar().week
    df["order_day"] = df["order_date"].dt.day
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

    # delivery performance
    df["delivery_days"] = (df["delivery_date"] - df["order_date"]).dt.days

    # payment method (join for convenience)
    df = df.merge(
        payments[["order_id", "payment_method", "payment_status"]],
        on="order_id", how="left",
    )

    # shipping method (join for convenience)
    df = df.merge(
        shipping[["order_id", "shipping_method", "shipping_cost"]],
        on="order_id", how="left",
    )

    # customer geography
    df = df.merge(
        customers[["customer_id", "city", "state"]],
        on="customer_id", how="left",
    )

    # repeat-customer / order-sequence features (based on ALL of a customer's orders)
    df = df.sort_values(["customer_id", "order_date"])
    df["customer_order_count"] = df.groupby("customer_id")["order_id"].transform("count")
    df["customer_order_seq"] = df.groupby("customer_id").cumcount() + 1
    df["is_repeat_customer"] = df["customer_order_count"] > 1
    df["is_first_order"] = df["customer_order_seq"] == 1

    df = df.sort_values("order_id").reset_index(drop=True)

    return df


def build_customer_features(orders_enriched, customers):
    valid_orders = orders_enriched[orders_enriched["order_status"] != "Cancelled"]

    agg = valid_orders.groupby("customer_id").agg(
        order_count=("order_id", "count"),
        total_revenue=("revenue", "sum"),
        total_profit=("profit", "sum"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
        avg_delivery_days=("delivery_days", "mean"),
    ).reset_index()

    agg["average_order_value"] = (agg["total_revenue"] / agg["order_count"]).round(2)
    agg["is_repeat_customer"] = agg["order_count"] > 1
    agg["customer_tenure_days"] = (agg["last_order_date"] - agg["first_order_date"]).dt.days

    df = customers.merge(agg, on="customer_id", how="left")

    # customers with no valid orders (all cancelled or never ordered)
    df["order_count"] = df["order_count"].fillna(0).astype(int)
    df["total_revenue"] = df["total_revenue"].fillna(0)
    df["total_profit"] = df["total_profit"].fillna(0)
    df["average_order_value"] = df["average_order_value"].fillna(0)
    df["is_repeat_customer"] = df["is_repeat_customer"].fillna(False)
    df["customer_tenure_days"] = df["customer_tenure_days"].fillna(0)

    return df


def main():
    print("=" * 50)
    print("FEATURE ENGINEERING")
    print("=" * 50)

    print("\nLoading processed data...")
    customers, products, orders, order_items, payments, shipping, reviews = load_processed()

    print("Building order_items_enriched (revenue, cost, profit)...")
    order_items_enriched = build_order_items_enriched(order_items, products)
    order_items_enriched.to_csv(os.path.join(PROCESSED_DIR, "order_items_enriched.csv"), index=False)
    print(f"  {len(order_items_enriched):,} line items")

    print("Building orders_enriched (revenue, profit, delivery, repeat flags)...")
    orders_enriched = build_orders_enriched(orders, order_items_enriched, customers, payments, shipping)
    orders_enriched.to_csv(os.path.join(PROCESSED_DIR, "orders_enriched.csv"), index=False)
    print(f"  {len(orders_enriched):,} orders")

    print("Building customer_features (order_count, AOV, revenue, repeat flag)...")
    customer_features = build_customer_features(orders_enriched, customers)
    customer_features.to_csv(os.path.join(PROCESSED_DIR, "customer_features.csv"), index=False)
    print(f"  {len(customer_features):,} customers")

    print("\n" + "-" * 50)
    print("SUMMARY STATISTICS")
    print("-" * 50)
    total_revenue = orders_enriched[orders_enriched["order_status"] != "Cancelled"]["revenue"].sum()
    total_profit = orders_enriched[orders_enriched["order_status"] != "Cancelled"]["profit"].sum()
    repeat_rate = customer_features["is_repeat_customer"].mean() * 100
    active_repeat_rate = (
        customer_features[customer_features["order_count"] > 0]["is_repeat_customer"].mean() * 100
    )
    print(f"Total revenue (excl. cancelled): Rs {total_revenue:,.2f}")
    print(f"Total profit:                    Rs {total_profit:,.2f}")
    print(f"Overall profit margin:           {(total_profit/total_revenue)*100:.2f}%")
    print(f"Repeat purchase rate (of ALL registered customers): {repeat_rate:.2f}%")
    print(f"Repeat purchase rate (of ACTIVE customers only):    {active_repeat_rate:.2f}%")

    print("\nFeature engineering completed successfully.")


if __name__ == "__main__":
    main()
