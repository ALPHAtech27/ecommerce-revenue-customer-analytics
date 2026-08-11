"""
rfm_segmentation.py
--------------------
Performs RFM (Recency, Frequency, Monetary) analysis and assigns each
customer to a business-friendly segment (Champions, Loyal Customers,
Potential Loyalists, New Customers, At Risk, Can't Lose Them,
Hibernating, Lost).

Reference date: the day after the most recent order in the dataset,
so recency is always >= 1 day for every customer.

Outputs:
    data/processed/rfm_customer_segments.csv
    data/processed/rfm_segment_summary.csv

Run:
    python scripts/rfm_segmentation.py
"""

import os
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def compute_rfm(orders_enriched):
    valid = orders_enriched[orders_enriched["order_status"] != "Cancelled"].copy()

    reference_date = valid["order_date"].max() + pd.Timedelta(days=1)

    rfm = valid.groupby("customer_id").agg(
        recency=("order_date", lambda x: (reference_date - x.max()).days),
        frequency=("order_id", "count"),
        monetary=("revenue", "sum"),
    ).reset_index()

    return rfm, reference_date


def score_rfm(rfm):
    # Quintile scores (1-5). For recency, LOWER days = BETTER = higher score,
    # so we reverse the labels for recency vs frequency/monetary.
    rfm = rfm.copy()

    rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["RFM_score"] = rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)
    rfm["RFM_sum"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    return rfm


def assign_segment(row):
    r, f, m = row["R_score"], row["F_score"], row["M_score"]

    # Champions: bought recently, buy often, spend the most
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    # Loyal Customers: buy regularly, good spend, decent recency
    if f >= 4 and m >= 3 and r >= 2:
        return "Loyal Customers"
    # Potential Loyalists: recent customers with average frequency
    if r >= 4 and f.__class__ and 2 <= f <= 3:
        return "Potential Loyalists"
    # New Customers: very recent, but low frequency (1-2 orders)
    if r >= 4 and f <= 2:
        return "New Customers"
    # Can't Lose Them: high monetary/frequency historically, but very low
    # recency -- checked before the broader "At Risk" bucket since these are
    # the highest-priority win-back customers
    if r == 1 and f >= 4 and m >= 4:
        return "Can't Lose Them"
    # At Risk: used to buy often/well but haven't come back recently
    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    # Hibernating: below-average across the board but not the worst
    if r <= 2 and f <= 2 and m <= 2 and row["RFM_sum"] > 3:
        return "Hibernating"
    # Lost: lowest scores across all three dimensions
    if r == 1 and f == 1 and m == 1:
        return "Lost"

    return "Hibernating"  # fallback bucket for anything not explicitly matched


SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Potential Loyalists", "New Customers",
    "At Risk", "Can't Lose Them", "Hibernating", "Lost",
]

SEGMENT_DESCRIPTIONS = {
    "Champions": "Bought recently, buy often, and spend the most. Reward and retain them.",
    "Loyal Customers": "Consistent repeat buyers with strong spend. Upsell higher-value products.",
    "Potential Loyalists": "Recent customers with moderate frequency. Nurture into loyal customers.",
    "New Customers": "Very recent first-time or low-frequency buyers. Focus on onboarding.",
    "At Risk": "Historically good customers who have not purchased recently. Win-back campaigns.",
    "Can't Lose Them": "Big spenders/frequent buyers who have gone quiet. High-priority win-back.",
    "Hibernating": "Below-average recency, frequency, and monetary value. Low-cost re-engagement.",
    "Lost": "Lowest scores across all RFM dimensions. Deprioritize or exclude from active marketing.",
}


def main():
    print("=" * 50)
    print("RFM CUSTOMER SEGMENTATION")
    print("=" * 50)

    orders_enriched = pd.read_csv(
        os.path.join(PROCESSED_DIR, "orders_enriched.csv"),
        parse_dates=["order_date"],
    )
    customers = pd.read_csv(os.path.join(PROCESSED_DIR, "customers_clean.csv"))

    print("\nComputing Recency, Frequency, Monetary per customer...")
    rfm, reference_date = compute_rfm(orders_enriched)
    print(f"Reference date used for recency: {reference_date.date()}")
    print(f"Customers with at least one valid order: {len(rfm):,}")

    print("\nScoring RFM (quintiles 1-5)...")
    rfm = score_rfm(rfm)

    print("Assigning business segments...")
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    rfm["segment_description"] = rfm["segment"].map(SEGMENT_DESCRIPTIONS)

    # attach customer info for convenience
    rfm = rfm.merge(customers[["customer_id", "customer_name", "city", "state"]], on="customer_id", how="left")

    cols = [
        "customer_id", "customer_name", "city", "state",
        "recency", "frequency", "monetary",
        "R_score", "F_score", "M_score", "RFM_score", "RFM_sum",
        "segment", "segment_description",
    ]
    rfm = rfm[cols]
    rfm.to_csv(os.path.join(PROCESSED_DIR, "rfm_customer_segments.csv"), index=False)

    # ---- segment summary ----
    total_customers = len(rfm)
    total_revenue = rfm["monetary"].sum()

    summary = rfm.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_revenue=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency", "mean"),
    ).reset_index()

    summary["pct_of_customers"] = (summary["customer_count"] / total_customers * 100).round(2)
    summary["pct_of_revenue"] = (summary["total_revenue"] / total_revenue * 100).round(2)
    summary["avg_revenue"] = summary["avg_revenue"].round(2)
    summary["avg_frequency"] = summary["avg_frequency"].round(2)
    summary["avg_recency"] = summary["avg_recency"].round(1)
    summary["total_revenue"] = summary["total_revenue"].round(2)

    # order by business priority instead of alphabetically
    summary["segment"] = pd.Categorical(summary["segment"], categories=SEGMENT_ORDER, ordered=True)
    summary = summary.sort_values("segment").reset_index(drop=True)

    summary.to_csv(os.path.join(PROCESSED_DIR, "rfm_segment_summary.csv"), index=False)

    print("\n" + "-" * 50)
    print("SEGMENT SUMMARY")
    print("-" * 50)
    print(summary.to_string(index=False))

    print(f"\nOutputs saved:")
    print(f"  {os.path.join(PROCESSED_DIR, 'rfm_customer_segments.csv')}")
    print(f"  {os.path.join(PROCESSED_DIR, 'rfm_segment_summary.csv')}")
    print("\nRFM segmentation completed successfully.")


if __name__ == "__main__":
    main()
