
***
# Bronze Layer (Raw Sources)
***
This folder contains the **raw source tables** for the NorthStar lakehouse.

In an authentic production environment, this layer represents the *closest possible copy* of raw operational data extracted from:
- application databases
- event tracking streams
- asset telemetry systems
- incident management systems

**Important principle:**  
Bronze data is allowed to be messy and inconsistent.

This is intentional and normal. Downstream layers (Silver/Gold) will clean, standardise, test, and model the data properly in preparation for the core NorthStar features.

---

## Contents

All files are written as **Parquet** for fast local analytics and compatibility with DuckDB + dbt.

| Table | File | Description | Grain (one row per...) |
|------|------|-------------|------------------------|
| Users | `users.parquet` | User accounts and signup metadata | user |
| Subscriptions | `subscriptions.parquet` | Subscription periods and plan changes | subscription period |
| Events | `events.parquet` | Product usage events (analytics tracking) | event |
| Assets | `assets.parquet` | Operational assets (devices/stations/turbines) | asset |
| Telemetry | `telemetry.parquet` | Hourly asset status + wind speed readings | asset-hour |
| Incidents | `incidents.parquet` | Outage incident windows derived from downtime | incident |

---

## Data quality notes (intentional imperfections)

These tables include the injection of *realistic issues you would expect in production data*, such as:

### `users.parquet`
- ~1% missing `country`
- ~2% inconsistent casing in `signup_channel` (e.g. `ORGANIC`)

### `subscriptions.parquet`
- Users may never subscribe (remain "free")
- Churn is represented via `end_date`
- Upgrades create a new subscription row (plan changes are history, not overwritten)
- ~1% inconsistent casing in `plan_id` (e.g. `PRO`)

### `events.parquet`
- Paying users generate more events on average
- ~0.2% missing `event_type`
- ~1% casing issues in `event_type` (e.g. `LOGIN`)

### `assets.parquet`
- Mixed asset types and regions
- ~2% casing issues in `region`

### `telemetry.parquet`
- Hourly data across a fixed time range
- Includes random 1-hour failures and multi-hour outage windows
- ~0.1% missing `wind_speed_ms`

### `incidents.parquet`
- Derived from contiguous downtime periods in telemetry
- Severity is based on outage duration
- Includes some casing issues in `severity` and `cause`

These imperfections are important because they allow the **Silver layer** to demonstrate:
- standardisation of formats (lowercase/uppercase fixes)
- null handling
- accepted values constraints
- relationships and uniqueness testing
- reliable production modelling practices

---

## Bronze Generation Instruction

Bronze data is produced locally with:

```bash
python scripts/00_generate_bronze.py
```

This script generates synthetic data with:

- numpy seed for reproducible randomness
- realistic behavioural patterns (conversion, churn ...etc..)
- authentic operational patterns (uptime, outages, incidents)