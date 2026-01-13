***
***
# NorthStar
***
***

NorthStar is a local analytics engineering flagship project: **DuckDB + Parquet lakehouse + dbt metrics layer + automated data quality tests**.

This repo simulates a realistic production workflow:
- **Bronze**: raw operational data ingested as Parquet
- **Silver**: cleaned + standardized staging models (dbt)
- **Gold**: star schema marts (facts + dimensions)
- **Metrics**: defined once and reused (single source of truth)
- **Quality**: automated tests for trust (not-null, unique, relationships, accepted values, freshness)

## Tech Stack
- **Python** (synthetic data + tooling)
- **DuckDB** (local warehouse)
- **Parquet** (lakehouse storage)
- **dbt-duckdb** (transformations + docs + tests)

***
## Project Status
Completed: 

- Repo bootstrapped

In progress:
 
- Generate Bronze data (users, subscriptions, events, assets, telemetry, incidents)  
- Build dbt staging models (Silver)  
- Build star schema marts (Gold)  
-  Define 10 business metrics  
-  Add dashboard + CI quality gates

***
## Planned Business Metrics (v1)
Revenue / Growth:
- MRR, ARR, ARPU
- Net Revenue Retention (NRR)

Product / Retention:
- DAU / WAU / MAU
- D30 retention rate
- Activation rate (key event within 7 days)

Reliability / Ops:
- Asset uptime %
- Incident rate per 100 assets
- Mean time to recovery (MTTR)

***

## Repo Layout (will evolve)
```text
NorthStar/
  data/
    bronze/
    silver/
    gold/
  scripts/
  dbt/
  dashboards/


```