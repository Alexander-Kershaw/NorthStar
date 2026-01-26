***

# NorthStar 

***

**Local Analytics Warehouse, dbt Marts, Data Quality Suite, Semantic Layer. Streamlit BI**
 
NorthStar is an analytics engineering project that builds a realistic local warehouse from scratch:

- **Bronze**: synthetic operational data and product data written to Parquet
- **Staging**: type normalization, category standardization, referential integrity
- **Gold (Marts)**: facts and dimensions in a star-schema style
- **Reporting Marts**: dashboard-ready aggregates (uptime, MTTR, retention, revenue)
- **Data Quality**: dbt schema tests and singular tests (interval sanity, composite keys, range checks)
- **Semantic Layer**: MetricFlow metrics with a time spine (“single source of truth” KPIs)
- **Streamlit BI**: lightweight dashboard to prove end-to-end value

Northstar intents do demonstrate understanding of the fundamental data architectures that enable trustworthy and robust analytics that are resilient to metric corruption and quiet failures that impact the validity of downstream data.

---

## Stack
- **Python** (data generation and Streamlit)
- **DuckDB** (local warehouse)
- **Parquet** (lakehouse storage)
- **dbt and dbt-duckdb** (models, tests, docs)
- **MetricFlow** (dbt semantic layer metrics)
- **Streamlit** (BI demo app)

---

## Repository structure

```text
NorthStar/
├── dashboards 
│ └── northstar_BI # Streamlit dashboard
├── scripts/
│ └── generate_bronze.py # writes Bronze Parquet
├── data/
│ └── bronze/ # generated Parquet (gitignored)
├── dbt/
│ ├── models/
│ │ ├── staging/ # stg_* models + schema.yml tests
│ │ ├── marts/
│ │ │ ├── dimensions/ # dim_* models (Gold)
│ │ │ ├── facts/ # fct_* models (Gold)
│ │ │ └── reporting/ # mart_* reporting outputs
│ │ └── semantic_metrics.yml # semantic models + metrics
│ ├── tests/ # singular tests (custom SQL)
│ ├── warehouse/ # DuckDB file (gitignored)
│ ├── TESTING.md # test philosophy + coverage
│ └── SEMANTIC_LAYER.md # MetricFlow usage
├── requirements-streamlit.txt # dashboard deps
└── README.md
```

**Note:** 'data/' and 'dbt/warehouse/' are excluded from git.

---

## Data model overview 

### Staging models (contracts + cleaning)
- `stg_users`  
- `stg_subscriptions`  
- `stg_events` (strict event_type contract)  
- `stg_assets`  
- `stg_telemetry`  
- `stg_incidents` (includes interval sanity testing)

### Gold dimensions
- `dim_asset`
- `dim_user`
- `dim_time_spine` (Semantic Layer requirement)

### Gold facts
- `fct_asset_uptime_hourly`
- `fct_asset_uptime_daily`
- `fct_incidents`
- `fct_usage_daily`
- `fct_mrr_daily`

### Reporting marts (dashboard-ready)
- `mart_uptime_region_daily`
- `mart_worst_assets_daily`
- `mart_mttr_region_daily`
- `mart_retention_cohorts`
- `mart_revenue_summary_monthly`

---

## Key KPIs included
**Operational / Reliability**
- Uptime % (daily + regional aggregation)
- Worst-performing assets (top 10 per day)
- MTTR (Mean Time To Recovery) by region/type
- Incident rate per 100 assets

**Product**
- DAU (Daily Active Users)
- D7 / D30 retention (monthly cohorts)

**Revenue**
- Daily MRR (active subscription periods)
- Monthly revenue summary (avg and end-of-month MRR + paying users)

---

## Running the project

### 1) Create environment
Activate your environment however you prefer (conda/venv).

### 2) Generate Bronze Parquet
From repo root:

```bash
python scripts/generate_bronze.py
```

This writes Parquest files into: data/bronze

---

### dbt: build + test warehouse

from inside dbt/:

```bash
dbt build
```

This runs:

- models (staging and marts)
- all dbt tests (schemea and singular tests)

---

### Semantic Layer (MetricFlow)

List metrics with:

```bash
mf list metrics
```

Some example metric queries: 

```bash
mf query --metrics mrr_gbp --group-by metric_time__month
mf query --metrics dau --group-by metric_time
mf query --metrics uptime_pct --group-by metric_time__week
```

View **dbt/SEMANTIC_LAYER.md** for more details

---

## Streamlit Dashboard

From the repo root:

```bash
python -m pip install -r requirements-streamlit.txt
streamlit run app.py
```

**Dashboard includes:**
- Monthly MRR chart
- DAU chart (with configurable time window)
- Uptime by region (configurable and data-anchored window)

---

## Testing + Data Quality

NorthStar uses:

- dbt schema tests: not_null, unique, accepted_values, relationships

Also uses singular tests for:

- composite grain uniqueness (e.g. asset_id + ts)
- interval sanity (end_ts > start_ts)
- metric sanity ranges (uptime within [0,1], revenue non-negative)


See dbt/TESTING.md for full coverage and philosophy.

---

## Orchestration (Apache Airflow)

NorthStar includes a local Airflow setup to orchestrate the pipeline:

**DAG:** `northstar_pipeline`  
**Flow:** `generate_bronze` -> `dbt_build`

### What the DAG runs
1) **generate_bronze**
   - executes `python scripts/generate_bronze.py`
   - writes Bronze Parquet files to `data/bronze/`

2) **dbt_build**
   - executes `dbt build`
   - runs all staging and marts models and all dbt tests (data quality gates)

### Run Airflow locally
From the repo root:

```bash
docker compose -f docker-compose.airflow.yml up -d
```

### Airflow UI:

- `http://127.0.0.1:8080` (not `localhost`)
- login with admin user (user: alex)

### Trigger the pipeline

- Unpause `northstar_pipeline` in Airflow UI
- Trigger manual DAG run
- View task logs for `generate_bronze` and `dbt_build`

### Notes

- Airflow containers use a custom image via `build: .` making `dbt-duckdb` avaliable inside the scheduler/webserver
- Logs are written to `/opt/airflow/logs` volume (the log direcgtory inside the container)
- **Note:** Logs are backed by a Docker volume, logs persist across restarts

### Troubleshooting

#### **Airflow UI won’t load**
- Use: `http://127.0.0.1:8080` (not `localhost`)
- Check containers:
  ```bash
  docker compose -f docker-compose.airflow.yml ps
  ```

#### **Login won't work / forgot password**

List users: 

```bash
docker exec -it northstar-airflow-webserver-1 airflow users list
```

Or create new admin user: 

```bash
docker exec -it northstar-airflow-webserver-1 airflow users create \
  --username alex \
  --firstname Alex \
  --lastname Kershaw \
  --role Admin \
  --email alex@example.com \
  --password northstar
```

#### **Task logs show `dbt: command not found`**

Airflow containers were not built with the required dbt installation.

Rebuild the custom image:

```bash
docker compose -f docker-compose.airflow.yml down
docker compose -f docker-compose.airflow.yml build
docker compose -f docker-compose.airflow.yml up -d
```

Then verify dbt exists inside the container

```bash
docker exec -it northstar-airflow-webserver-1 dbt --version
```

#### **How to view Airflow logs**

View logs from inside the webserver container:

```bash
docker exec -it northstar-airflow-webserver-1 ls -R /opt/airflow/logs | head -200
```

For a specific task attempt log:

```bash
docker exec -it northstar-airflow-webserver-1 tail -n 200 \
/opt/airflow/logs/dag_id=northstar_pipeline/run_id=<RUN_ID>/task_id=dbt_build/attempt=1.log
```

List all DAG run folders:

```bash
docker exec -it northstar-airflow-webserver-1 find /opt/airflow/logs -maxdepth 3 -type d | head -200
```

#### **Reset everything**

**Note:** Wipes Airflow users and Airflow UI history

```bash
docker compose -f docker-compose.airflow.yml down -v
docker compose -f docker-compose.airflow.yml up -d
```

---


## Intention

NorthStar demonstrates practical analytics engineering skill:

- building a warehouse from raw operational-style data
- modeling facts/dimensions cleanly
- enforcing trust via tests and contracts
- producing business KPIs and dashboard-ready marts
- defining metrics once via a semantic layer
- shipping a working BI frontend
- orchestration implementation for schedualing 

***



