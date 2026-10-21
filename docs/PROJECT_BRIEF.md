# Project brief

## Problem

An operations manager needs to know which markets and delivery services miss their promises, how much activity is affected, and which customer groups have stopped buying. Manual extracts mix order lines and orders, inflate counts and obscure data quality. Customer “churn” is frequently undefined in non-contractual commerce.

## Strategic objectives

1. Produce order-level delivery and sales KPIs from validated line records.
2. Automate ingestion and allow corrected batches without duplicate totals.
3. Define historical 90-day customer inactivity and right-censor unobserved outcomes.
4. Explain business recommendations and their limitations through an interactive dashboard.

## Business users and decisions

- Operations: prioritize investigation by late order volume, rate and shipping mode.
- Finance: reconcile net sales and recorded-profit fields before interpreting commercial performance.
- Customer analytics: use recency/frequency/monetary features for campaign design, not unsupported prediction claims.
- Analytics engineering: inspect source checksums, ingestion status and failed quality gates.

## Potential ROI

Efficiency: (manual minutes - automated operator minutes) × refreshes / 60 × hourly cost. Measure operator time separately from script runtime.

Delivery scenario: late completed orders × assumed preventable fraction × assumed avoidable cost per late order. The dashboard makes these assumptions editable.

Retention: incremental campaign benefit requires a randomized test, treatment costs and a credible margin estimate. An inactivity label cannot establish intervention uplift.

No realized monetary ROI is claimed. Source currency is unverified, so all monetary figures are dataset units.

## Definition of done

Reproduce a source download, validated ingestion, reporting marts, tested idempotency/corrections, cohort snapshot, aggregate dashboard and executive summary. Reviewers can inspect code and repeat the run without a paid BI license. Native Power BI assembly is a documented follow-up, not an included `.pbix`.
