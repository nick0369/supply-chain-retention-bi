# Executive summary — measured historical results

## Problem
Operations needs a single reconciled view of order-level delivery performance and a documented customer inactivity definition.

## Summary
Processed 180,519 order lines into 65,752 distinct orders. COMPLETE/CLOSED orders: 28,965. Completed-order late rate: 57.42%. Net sales: 14,476,738.58 dataset monetary units. Currency is unverified; do not label INR/USD.

## Delivery findings
- Africa / First Class: 100.00% late across 238 completed orders.
- Europe / First Class: 100.00% late across 1,311 completed orders.
- LATAM / First Class: 100.00% late across 1,163 completed orders.

## Customer analysis
Snapshot: 2017-01-31; observed through: 2018-01-31. Inactivity means no completed purchase in the following 90 days; label maturity: True. This is descriptive, not a prediction model.

Data coverage warning: No completed-purchase customer IDs overlap the final 90 days and earlier history. Verify identifier continuity and source coverage before treating recent inactivity as business churn.

## Recommendations
Investigate shipping-mode promise settings and fulfillment bottlenecks in the listed groups; compare absolute late counts, order sizes and service costs before changing a promise. Use RFM/inactivity groups to design a controlled retention experiment. Validate customer-ID continuity and observation completeness first.

## Conclusion
The system produces auditable order metrics and repeatable customer cohorts. No causal churn reduction, delivery improvement or realized ROI has been demonstrated. Apparent retention patterns may reflect dataset construction or incomplete capture rather than business behavior.
