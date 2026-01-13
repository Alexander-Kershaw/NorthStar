***

# dbt Testing Guide 

***

NorthStar uses **dbt tests** to enforce trust in the warehouse models.
The objective is to make sure that downstream dashboards and metrics are built on data that is:

- complete (no unexpected nulls)
- consistent (valid categories and types)
- reliable (keys are unique)
- joinable (facts reference real dimensions)
- logically correct (time intervals make sense)

In a production setting, these tests would run in CI on every pull request.
Here, they run locally with:

```bash
dbt test
```

***

## Testing Philosophy

***

Data pipeline have the potentiality to inconspicuously fail in ways that do not crash any code, but instead cause the corruption of analytics.

For instance:

- duplicated user ID's can artificially inflate counts
- incorrect categories splitting metrics ("PRO" vs "pro")
- orphaned foreign keys breaking joins
- invalid timestamps causing a misleading time series

Therefore, dbt testing has been applied to ensure that such issues are caught before any downstream actions

***

## Tests Used 

***

### Generic Schema Tests:

Used to validate columns and relationships. Here are some of the tests that have been used:

- not_null -> used on primary keys and essential timestamps as missing keys may cause broken joins and imperceptible metric errors

- unique -> ensuring there are no duplicates so counts are not inflated and dimensional modelling assumptions are not broken

- accepted_values -> Columns must only contain know categories, this avoids category fragmentation and protects definitions (e.g. LOGIN vs login)

- relationships -> ensures referential integrity by ensuring a foreign key in one model exists in the referenced model

Example: 

stg_telemetry.asset_id must exist in stg_assets.asset_id

stg_incidents.asset_id must exist in stg_assets.asset_id

This is important as it prevents orphan records and ensured joins behave as intended.


***

### Singular Custom SQL Tests

Singular tests (located in dbt/tests) exist as raw SQL.

Singular custom tests have been applied in ensiring incidents have valid time windows (end_ts > start_ts). This protects intervalic data (which is very easily corrupted) and downtime analytics from logically incoherent values.

***

Specifics of the testing and constraints may be inspected in dbt/staging/schema.yml where the dbt tests are defined

***