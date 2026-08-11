# Business Recommendations

**E-Commerce Revenue & Customer Analytics**

Each recommendation below is tied to a specific finding in the data, with
the supporting numbers and the notebook/SQL query where it can be
verified. Recommendations are ordered by estimated impact.

---

### 1. Build a retention program specifically for Champions and Loyal Customers

**Finding:** Champions (20.8% of active customers) generate 56.9% of
total revenue; Champions + Loyal Customers together are 36.0% of
customers and 74.4% of revenue. (`notebooks/03_rfm_segmentation.ipynb`,
`sql/05_rfm_analysis.sql`)

**Recommendation:** Prioritize retention budget — loyalty perks, early
access, personalized outreach — on this segment before spreading spend
across the full customer base. Losing a single Champion customer is,
on average, equivalent to losing dozens of Hibernating customers in
revenue terms (avg. revenue per Champion: Rs 117,788 vs. Rs 14,804 for
Hibernating).

---

### 2. Launch a targeted win-back campaign for "At Risk" and "Can't Lose Them"

**Finding:** 1,937 customers in these two segments represent Rs 70.4M in
historically-proven revenue (avg. recency: 645-779 days since last
order, but avg. frequency of 2-3 orders and solid historical spend).
(`notebooks/03_rfm_segmentation.ipynb`)

**Recommendation:** These customers already have a purchase history and
demonstrated willingness to spend — a win-back campaign here should
outperform cold acquisition on cost-per-dollar-of-revenue-recovered.
Segment further by last-purchased category to personalize the offer.

---

### 3. Convert one-time buyers into repeat buyers

**Finding:** Only 36.68% of all registered customers place a second
order (59.10% among those who are "active," i.e. already ordered at
least once — the gap shows most customers never return after their
first purchase). (`scripts/feature_engineering.py` output,
`notebooks/02_customer_analysis.ipynb`)

**Recommendation:** Introduce a structured second-purchase incentive
(e.g., a time-boxed discount or free-shipping offer triggered
automatically after the first delivered order). Given how much more
Champions/Loyal Customers spend than one-time buyers, even a small lift
in second-purchase conversion compounds significantly over time.

---

### 4. Review discounting strategy — margin erodes faster than volume grows

**Finding:** Profit margin drops steadily as discount depth increases:
36.00% margin at 0% discount, 30.69% at 1-10%, 22.60% at 11-20%, and
just 12.92% at 21-30%. Meanwhile line-item volume at the 21-30% band
(21,625 items) is a fraction of the 0% band (155,445 items) — deep
discounts are not driving proportionally more volume.
(`notebooks/04_business_insights.ipynb`, `sql/04_product_analysis.sql`)

**Recommendation:** Audit which products/categories are routinely
discounted 20%+ and confirm the discount is actually driving incremental
volume rather than giving away margin on sales that would have happened
anyway. Consider capping standard discounts at 10-15% outside of
planned promotional events.

---

### 5. Reassess pricing or supplier cost in Books and Electronics

**Finding:** Books has both the lowest revenue (Rs 25.6M) and the lowest
margin (25.17%) of all 12 categories. Electronics is the clear revenue
leader (Rs 414M, 31% of total) but its margin (30.06%) is below several
much-smaller categories like Pet Supplies (35.70%) and Beauty & Personal
Care (34.99%). (`notebooks/04_business_insights.ipynb`,
`sql/02_revenue_analysis.sql`)

**Recommendation:** For Electronics specifically, even a 2-3 point
margin improvement (via supplier renegotiation or reduced blanket
discounting) would have an outsized dollar impact given its revenue
scale. For Books, evaluate whether the category is worth the shelf
space and marketing investment at its current margin profile.

---

### 6. Use CLV tiers to set acquisition spend ceilings

**Finding:** Estimated CLV ranges from an average of Rs 7,245 in the
"Low" tier to Rs 146,253 in the "Top" tier — a 20x spread.
(`notebooks/02_customer_analysis.ipynb`,
`data/processed/customer_lifetime_value.csv`)

**Recommendation:** Set different maximum customer-acquisition-cost
(CAC) thresholds by the acquisition channel's typical resulting CLV
tier. Acquisition spend that only reaches "Low" CLV-tier customers
should be capped well below spend directed at channels that historically
produce "Top" tier customers.

---

### 7. Investigate the highest payment-failure-rate channels

**Finding:** Credit Card (4.28%), UPI (4.17%), and Debit Card (4.16%)
show the highest payment failure rates; Net Banking is lowest at 3.80%.
UPI carries the most orders overall (38,820) so even a modest
improvement in its failure rate would recover meaningful lost revenue.
(`sql/06_business_questions.sql`)

**Recommendation:** Work with the payment gateway provider to diagnose
failure causes on UPI and Credit Card specifically (timeout thresholds,
retry logic, bank-side decline codes) given their high order volume.

---

### 8. Treat the Hibernating segment as a low-cost, high-volume re-engagement opportunity

**Finding:** Hibernating is the largest segment by customer count
(12,286 customers, 39.6% of the active base) but only 13.60% of revenue
— the opposite ratio from Champions. (`notebooks/03_rfm_segmentation.ipynb`)

**Recommendation:** Because this segment is large and individually
lower-value, use low-cost, automated re-engagement (email/push
campaigns, broad seasonal promotions) rather than expensive 1:1 outreach
— the per-customer economics don't support high-touch retention here the
way they do for Champions.

---

### 9. Monitor the New Customer → Potential Loyalist transition rate

**Finding:** New Customers (1,181 customers, 3.81% of the base) and
Potential Loyalists (3,415 customers, 11.0%) are both early-lifecycle
segments with relatively low average frequency (1.00 and 1.62 orders
respectively). (`notebooks/03_rfm_segmentation.ipynb`)

**Recommendation:** Track this transition rate as a leading indicator.
If New Customers aren't graduating into Potential Loyalists / Loyal
Customers over time, the onboarding and second-purchase experience needs
attention before acquisition spend is increased further.

---

### 10. Re-run this analysis on a monthly cadence with live data

**Finding:** This project's pipeline (`scripts/run_pipeline.py`) runs
end-to-end in under a minute and is fully parameterized/reproducible.

**Recommendation:** Point the same pipeline at a live data warehouse
export on a monthly cadence so RFM segments, CLV tiers, and the KPI
dashboard stay current — segment membership shifts as customers order
(or stop ordering), and stale segmentation leads to misdirected
retention spend.

---

## A note on what the data did NOT show clearly

In the interest of not overstating findings: the relationship between
shipping method / delivery time and review rating was **not strongly
differentiated** in this dataset (average ratings stayed in a narrow
3.86-3.92 band across all delivery-time buckets). In a real production
dataset this relationship is often stronger and worth investigating
directly — but it should be validated against real behavioral data
rather than assumed from this synthetic sample.
