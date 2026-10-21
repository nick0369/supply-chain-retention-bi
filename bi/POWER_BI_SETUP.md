# Native Power BI implementation

No `.pbix` is included. The working browser dashboard is accompanied by these instructions and DAX measures for Power BI Desktop assembly.

1. Run the pipeline and import `data/processed/orders.csv` and `customer_snapshot.csv`, or connect to PostgreSQL views.
2. Set ordered_at to Date/Time and IDs/completed/late_flag to whole numbers. Use a calendar dimension for order-date slicing.
3. Keep snapshot analytics separate from order-date filters unless you explicitly model snapshot_date and its semantics.
4. Add each measure from `measures.dax` separately. Use percent formatting for rates, decimals for monetary units; source currency is unverified.
5. Operations page: four cards, market/mode slicers, late-rate bar chart, monthly net sales and a detail matrix.
6. Customer page: snapshot date/observation end text, recency segments, cohort heatmap, future inactivity labels only when mature.
7. Assurance page: checks and source fingerprint from reports/validation.json; if desired transform JSON using Power Query.
8. Public reports must exclude account-level identifiers and all personal source columns. Publish to web exposes underlying data.
9. Refresh after the ETL succeeds; service refresh of a local database or CSV folder may require a gateway and license eligibility.

Palette and page layouts follow `dashboard/style.css`. Explain every denominator and preserve the order grain.
