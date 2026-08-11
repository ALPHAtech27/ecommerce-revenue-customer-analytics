"""
generate_data.py
-----------------
Generates a realistic SYNTHETIC e-commerce dataset used throughout this
project. No real customer, order, or product data is used anywhere in
this repository -- everything is created programmatically with a fixed
random seed so the pipeline is 100% reproducible.

Tables produced (saved as CSV into data/raw/):
    customers.csv
    products.csv
    orders.csv
    order_items.csv
    payments.csv
    shipping.csv
    reviews.csv

Run:
    python scripts/generate_data.py

The script intentionally injects a small, controlled amount of data
quality issues (missing values, duplicates, inconsistent text casing,
a few bad dates, a few negative/outlier values) so that the cleaning
pipeline (scripts/clean_data.py) has real work to do -- this mirrors
what you actually encounter with production e-commerce data exports.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
SEED = 42
N_CUSTOMERS = 50_000
N_PRODUCTS = 320
N_ORDERS = 110_000          # a few thousand get filtered out during cleaning
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

rng = np.random.default_rng(SEED)


def days_between(start, end):
    return (end - start).days


def random_dates(start, end, size):
    """Vectorized random date generator between start and end (inclusive)."""
    total_days = days_between(start, end)
    offsets = rng.integers(0, total_days + 1, size=size)
    return np.array([start + timedelta(days=int(o)) for o in offsets])


# ---------------------------------------------------------------------------
# 1. CUSTOMERS
# ---------------------------------------------------------------------------
def generate_customers(n=N_CUSTOMERS):
    first_names = [
        "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
        "Linda", "David", "Elizabeth", "William", "Barbara", "Richard",
        "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
        "Priya", "Amit", "Rahul", "Sneha", "Anjali", "Vikram", "Neha",
        "Rohan", "Pooja", "Arjun", "Kavya", "Sanjay", "Divya", "Karan",
        "Meera", "Aditya", "Isha", "Nikhil", "Ritu", "Varun",
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Sharma", "Verma", "Gupta", "Rao",
        "Reddy", "Nair", "Iyer", "Mehta", "Kapoor", "Chopra", "Malhotra",
        "Singh", "Kumar", "Patel", "Shah", "Joshi", "Desai", "Pillai",
    ]

    cities_states = [
        ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"),
        ("Nagpur", "Maharashtra"), ("Delhi", "Delhi"),
        ("Bengaluru", "Karnataka"), ("Mysuru", "Karnataka"),
        ("Hyderabad", "Telangana"), ("Warangal", "Telangana"),
        ("Chennai", "Tamil Nadu"), ("Coimbatore", "Tamil Nadu"),
        ("Kolkata", "West Bengal"), ("Siliguri", "West Bengal"),
        ("Ahmedabad", "Gujarat"), ("Surat", "Gujarat"),
        ("Jaipur", "Rajasthan"), ("Udaipur", "Rajasthan"),
        ("Lucknow", "Uttar Pradesh"), ("Kanpur", "Uttar Pradesh"),
        ("Bhopal", "Madhya Pradesh"), ("Indore", "Madhya Pradesh"),
        ("Patna", "Bihar"), ("Chandigarh", "Punjab"),
        ("Kochi", "Kerala"), ("Thiruvananthapuram", "Kerala"),
        ("Guwahati", "Assam"), ("Bhubaneswar", "Odisha"),
        ("Ranchi", "Jharkhand"), ("Raipur", "Chhattisgarh"),
        ("Dehradun", "Uttarakhand"), ("Panaji", "Goa"),
    ]

    customer_id = np.arange(1, n + 1)
    fn = rng.choice(first_names, size=n)
    ln = rng.choice(last_names, size=n)
    customer_name = [f"{f} {l}" for f, l in zip(fn, ln)]

    # gender with a realistic distribution
    gender = rng.choice(["Male", "Female", "Other"], size=n, p=[0.49, 0.49, 0.02])

    # age skewed toward 22-45, some in tails
    age = rng.normal(33, 9, size=n).round().astype(int)
    age = np.clip(age, 18, 75)

    city_idx = rng.integers(0, len(cities_states), size=n)
    city = [cities_states[i][0] for i in city_idx]
    state = [cities_states[i][1] for i in city_idx]

    signup_date = random_dates(START_DATE, END_DATE - timedelta(days=1), n)

    email = []
    for i in range(n):
        handle = f"{fn[i].lower()}.{ln[i].lower()}{customer_id[i]}"
        domain = rng.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
        email.append(f"{handle}@{domain}")

    df = pd.DataFrame({
        "customer_id": customer_id,
        "customer_name": customer_name,
        "email": email,
        "gender": gender,
        "age": age,
        "city": city,
        "state": state,
        "signup_date": signup_date,
    })

    # --- inject realistic data quality issues -------------------------------
    # 1) missing emails
    missing_email_idx = rng.choice(n, size=int(n * 0.01), replace=False)
    df.loc[missing_email_idx, "email"] = np.nan

    # 2) missing age
    missing_age_idx = rng.choice(n, size=int(n * 0.015), replace=False)
    df.loc[missing_age_idx, "age"] = np.nan

    # 3) inconsistent casing / whitespace on city & state (common export bug)
    messy_idx = rng.choice(n, size=int(n * 0.05), replace=False)
    df.loc[messy_idx, "city"] = df.loc[messy_idx, "city"].str.upper()
    messy_idx2 = rng.choice(n, size=int(n * 0.03), replace=False)
    df.loc[messy_idx2, "state"] = " " + df.loc[messy_idx2, "state"].str.lower() + " "

    # 4) a handful of duplicate customer rows (exact dupes)
    dup_rows = df.sample(n=int(n * 0.004), random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 5) a few invalid ages (data entry errors)
    bad_age_idx = rng.choice(len(df), size=40, replace=False)
    df.loc[bad_age_idx, "age"] = rng.choice([-5, 0, 130, 200], size=40)

    return df


# ---------------------------------------------------------------------------
# 2. PRODUCTS
# ---------------------------------------------------------------------------
def generate_products(n=N_PRODUCTS):
    category_map = {
        "Electronics": ["Mobiles", "Laptops", "Headphones", "Cameras", "Accessories"],
        "Fashion": ["Men's Clothing", "Women's Clothing", "Footwear", "Watches", "Bags"],
        "Home & Kitchen": ["Cookware", "Furniture", "Home Decor", "Storage", "Lighting"],
        "Beauty & Personal Care": ["Skincare", "Haircare", "Makeup", "Fragrances"],
        "Sports & Fitness": ["Gym Equipment", "Sportswear", "Cycling", "Outdoor"],
        "Books": ["Fiction", "Non-Fiction", "Academic", "Children"],
        "Toys & Baby": ["Toys", "Baby Care", "Games"],
        "Grocery": ["Snacks", "Beverages", "Staples", "Organic"],
        "Automotive": ["Car Accessories", "Bike Accessories", "Tools"],
        "Office Supplies": ["Stationery", "Printers", "Furniture"],
        "Pet Supplies": ["Pet Food", "Pet Accessories"],
        "Health": ["Supplements", "Medical Devices", "Wellness"],
    }
    brands = [
        "Nova", "Zenith", "Urban Craft", "Vertex", "Pulse", "Aria", "Kingsman",
        "Orbit", "Lumen", "Sable", "Crestline", "Nimbus", "Solace", "Verve",
        "Meridian", "Ecliptic", "Highline", "Pioneer", "Bluecrest", "Falcon",
    ]

    categories = list(category_map.keys())

    product_id = np.arange(1, n + 1)
    cat_choices = rng.choice(categories, size=n)
    sub_choices = [rng.choice(category_map[c]) for c in cat_choices]
    brand_choices = rng.choice(brands, size=n)

    # cost price by category tier (electronics pricier than grocery, etc.)
    category_base_cost = {
        "Electronics": 4500, "Fashion": 700, "Home & Kitchen": 1200,
        "Beauty & Personal Care": 350, "Sports & Fitness": 900, "Books": 250,
        "Toys & Baby": 450, "Grocery": 150, "Automotive": 1100,
        "Office Supplies": 400, "Pet Supplies": 350, "Health": 500,
    }
    base_cost = np.array([category_base_cost[c] for c in cat_choices])
    cost_price = np.round(base_cost * rng.lognormal(mean=0, sigma=0.5, size=n), 2)
    cost_price = np.clip(cost_price, 30, None)

    # margin varies 20% - 90%
    margin_pct = rng.uniform(0.20, 0.90, size=n)
    selling_price = np.round(cost_price * (1 + margin_pct), 2)

    product_name = [
        f"{brand_choices[i]} {sub_choices[i]} {['Pro','Max','Lite','Plus','Classic','Air'][i % 6]}"
        for i in range(n)
    ]

    df = pd.DataFrame({
        "product_id": product_id,
        "product_name": product_name,
        "category": cat_choices,
        "sub_category": sub_choices,
        "brand": brand_choices,
        "cost_price": cost_price,
        "selling_price": selling_price,
    })

    # inject a few quality issues
    missing_cost_idx = rng.choice(n, size=8, replace=False)
    df.loc[missing_cost_idx, "cost_price"] = np.nan

    inconsistent_idx = rng.choice(n, size=15, replace=False)
    df.loc[inconsistent_idx, "category"] = df.loc[inconsistent_idx, "category"].str.lower()

    return df


# ---------------------------------------------------------------------------
# 3. ORDERS
# ---------------------------------------------------------------------------
def generate_orders(n_orders, customers_df):
    order_id = np.arange(1, n_orders + 1)

    # Not all customers order equally -- use a power-law-like weighting so
    # a subset of customers are frequent buyers (realistic for RFM/CLV work)
    weights = rng.pareto(a=2.0, size=len(customers_df)) + 0.1
    weights = weights / weights.sum()
    customer_ids = rng.choice(customers_df["customer_id"].values, size=n_orders, p=weights)

    order_date = random_dates(START_DATE, END_DATE, n_orders)

    status_choices = ["Delivered", "Shipped", "Cancelled", "Returned", "Processing"]
    status_probs = [0.78, 0.08, 0.06, 0.05, 0.03]
    order_status = rng.choice(status_choices, size=n_orders, p=status_probs)

    df = pd.DataFrame({
        "order_id": order_id,
        "customer_id": customer_ids,
        "order_date": order_date,
        "order_status": order_status,
    })

    # shipping_date / delivery_date only make sense for shipped/delivered/returned orders
    ship_lag = rng.integers(0, 3, size=n_orders)
    deliver_lag = rng.integers(2, 10, size=n_orders)

    shipping_date = df["order_date"] + pd.to_timedelta(ship_lag, unit="D")
    delivery_date = shipping_date + pd.to_timedelta(deliver_lag, unit="D")

    no_ship_mask = df["order_status"].isin(["Cancelled", "Processing"])
    shipping_date = shipping_date.where(~no_ship_mask, pd.NaT)
    delivery_date = delivery_date.where(~no_ship_mask, pd.NaT)

    # for "Shipped" status, no delivery date yet
    shipped_only_mask = df["order_status"] == "Shipped"
    delivery_date = delivery_date.where(~shipped_only_mask, pd.NaT)

    df["shipping_date"] = shipping_date
    df["delivery_date"] = delivery_date

    df["payment_id"] = order_id + 500_000  # 1:1 with payments table

    # --- inject data quality issues ---
    dup_rows = df.sample(n=int(n_orders * 0.003), random_state=SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)

    bad_date_idx = rng.choice(len(df), size=25, replace=False)
    df.loc[bad_date_idx, "delivery_date"] = df.loc[bad_date_idx, "order_date"] - pd.to_timedelta(5, unit="D")

    missing_status_idx = rng.choice(len(df), size=60, replace=False)
    df.loc[missing_status_idx, "order_status"] = np.nan

    return df


# ---------------------------------------------------------------------------
# 4. ORDER ITEMS
# ---------------------------------------------------------------------------
def generate_order_items(orders_df, products_df):
    # each order has 1-5 line items
    n_orders = len(orders_df)
    items_per_order = rng.integers(1, 6, size=n_orders)
    total_items = items_per_order.sum()

    order_id_rep = np.repeat(orders_df["order_id"].values, items_per_order)
    product_ids = rng.choice(products_df["product_id"].values, size=total_items)

    price_lookup = products_df.set_index("product_id")["selling_price"].to_dict()
    unit_price = np.array([price_lookup.get(p, np.nan) for p in product_ids])

    quantity = rng.integers(1, 6, size=total_items)
    discount = np.round(rng.choice(
        [0, 0, 0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        size=total_items,
        p=[0.35, 0.10, 0.05, 0.12, 0.13, 0.10, 0.08, 0.05, 0.02]
    ), 2)

    df = pd.DataFrame({
        "order_item_id": np.arange(1, total_items + 1),
        "order_id": order_id_rep,
        "product_id": product_ids,
        "quantity": quantity,
        "unit_price": unit_price.round(2),
        "discount": discount,
    })

    # inject a few negative/outlier quantities and missing unit prices
    bad_qty_idx = rng.choice(len(df), size=20, replace=False)
    df.loc[bad_qty_idx, "quantity"] = rng.choice([-2, 0, 500], size=20)

    missing_price_idx = rng.choice(len(df), size=30, replace=False)
    df.loc[missing_price_idx, "unit_price"] = np.nan

    return df


# ---------------------------------------------------------------------------
# 5. PAYMENTS
# ---------------------------------------------------------------------------
def generate_payments(orders_df, order_items_df):
    order_value = (
        order_items_df.assign(
            line_total=lambda d: d["quantity"] * d["unit_price"] * (1 - d["discount"])
        )
        .groupby("order_id")["line_total"]
        .sum()
    )

    df = orders_df[["order_id", "payment_id"]].copy()
    df["payment_amount"] = df["order_id"].map(order_value).fillna(0).round(2)

    methods = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery", "Wallet"]
    method_probs = [0.20, 0.15, 0.35, 0.10, 0.12, 0.08]
    df["payment_method"] = rng.choice(methods, size=len(df), p=method_probs)

    status_choices = ["Success", "Failed", "Refunded", "Pending"]
    status_probs = [0.90, 0.04, 0.04, 0.02]
    df["payment_status"] = rng.choice(status_choices, size=len(df), p=status_probs)

    df = df[["payment_id", "order_id", "payment_method", "payment_status", "payment_amount"]]

    missing_amt_idx = rng.choice(len(df), size=15, replace=False)
    df.loc[missing_amt_idx, "payment_amount"] = np.nan

    return df


# ---------------------------------------------------------------------------
# 6. SHIPPING
# ---------------------------------------------------------------------------
def generate_shipping(orders_df):
    valid = orders_df.dropna(subset=["shipping_date"]).copy()
    n = len(valid)

    methods = ["Standard", "Express", "Same-Day", "Economy"]
    method_probs = [0.55, 0.25, 0.05, 0.15]
    shipping_method = rng.choice(methods, size=n, p=method_probs)

    base_cost = {"Standard": 60, "Express": 150, "Same-Day": 250, "Economy": 30}
    shipping_cost = np.array([base_cost[m] for m in shipping_method]) * rng.uniform(0.8, 1.3, size=n)

    df = pd.DataFrame({
        "shipping_id": np.arange(1, n + 1),
        "order_id": valid["order_id"].values,
        "shipping_date": valid["shipping_date"].values,
        "delivery_date": valid["delivery_date"].values,
        "shipping_method": shipping_method,
        "shipping_cost": shipping_cost.round(2),
    })

    missing_cost_idx = rng.choice(len(df), size=25, replace=False)
    df.loc[missing_cost_idx, "shipping_cost"] = np.nan

    return df


# ---------------------------------------------------------------------------
# 7. REVIEWS
# ---------------------------------------------------------------------------
def generate_reviews(orders_df, order_items_df):
    delivered = orders_df[orders_df["order_status"] == "Delivered"][["order_id", "customer_id", "delivery_date"]]
    # not every delivered order gets reviewed
    reviewed = delivered.sample(frac=0.55, random_state=SEED)

    items_lookup = order_items_df.groupby("order_id")["product_id"].first()
    reviewed = reviewed.copy()
    reviewed["product_id"] = reviewed["order_id"].map(items_lookup)
    reviewed = reviewed.dropna(subset=["product_id"])

    n = len(reviewed)
    # ratings skew positive, as is typical, with some low-rating tail
    rating = rng.choice([1, 2, 3, 4, 5], size=n, p=[0.06, 0.08, 0.14, 0.32, 0.40])

    review_delay = rng.integers(1, 15, size=n)
    review_date = pd.to_datetime(reviewed["delivery_date"]) + pd.to_timedelta(review_delay, unit="D")

    df = pd.DataFrame({
        "review_id": np.arange(1, n + 1),
        "order_id": reviewed["order_id"].values,
        "customer_id": reviewed["customer_id"].values,
        "product_id": reviewed["product_id"].astype(int).values,
        "rating": rating,
        "review_date": review_date.values,
    })

    missing_rating_idx = rng.choice(len(df), size=10, replace=False)
    df.loc[missing_rating_idx, "rating"] = np.nan

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    print("=" * 50)
    print("GENERATING SYNTHETIC E-COMMERCE DATASET")
    print("=" * 50)

    print("\n[1/7] Generating customers...")
    customers = generate_customers()
    customers.to_csv(os.path.join(RAW_DIR, "customers.csv"), index=False)
    print(f"Customers generated: {len(customers):,}")

    print("\n[2/7] Generating products...")
    products = generate_products()
    products.to_csv(os.path.join(RAW_DIR, "products.csv"), index=False)
    print(f"Products generated: {len(products):,}")

    print("\n[3/7] Generating orders...")
    orders = generate_orders(N_ORDERS, customers)
    orders.to_csv(os.path.join(RAW_DIR, "orders.csv"), index=False)
    print(f"Orders generated: {len(orders):,}")

    print("\n[4/7] Generating order items...")
    order_items = generate_order_items(orders, products)
    order_items.to_csv(os.path.join(RAW_DIR, "order_items.csv"), index=False)
    print(f"Order items generated: {len(order_items):,}")

    print("\n[5/7] Generating payments...")
    payments = generate_payments(orders, order_items)
    payments.to_csv(os.path.join(RAW_DIR, "payments.csv"), index=False)
    print(f"Payments generated: {len(payments):,}")

    print("\n[6/7] Generating shipping records...")
    shipping = generate_shipping(orders)
    shipping.to_csv(os.path.join(RAW_DIR, "shipping.csv"), index=False)
    print(f"Shipping records generated: {len(shipping):,}")

    print("\n[7/7] Generating reviews...")
    reviews = generate_reviews(orders, order_items)
    reviews.to_csv(os.path.join(RAW_DIR, "reviews.csv"), index=False)
    print(f"Reviews generated: {len(reviews):,}")

    print("\n" + "-" * 50)
    print("BASIC STATISTICS")
    print("-" * 50)
    print(f"Unique customers who ordered: {orders['customer_id'].nunique():,}")
    print(f"Date range: {orders['order_date'].min()} to {orders['order_date'].max()}")
    print(f"Product categories: {products['category'].str.title().nunique()}")
    print(f"Average items per order: {len(order_items) / len(orders):.2f}")

    print("\nData saved successfully.")
    print(f"Location: {RAW_DIR}")


if __name__ == "__main__":
    main()
