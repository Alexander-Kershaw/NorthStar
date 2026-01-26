from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


REPO_DIR = "/opt/northstar"

default_args = {
    "owner": "northstar",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="northstar_pipeline",
    description="NorthStar: generate bronze -> dbt build (models + tests)",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="0 6 * * *", # bronze generation and dbt build daily at 06:00 UTC
    catchup=False, # False so old days are not backfilled
    tags=["northstar", "dbt", "duckdb"],
) as dag:

    generate_bronze = BashOperator(
        task_id="generate_bronze",
        bash_command=f"cd {REPO_DIR} && python scripts/generate_bronze.py",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {REPO_DIR}/dbt && dbt build --vars '{{\"bronze_dir\": \"/opt/northstar/data/bronze\"}}'",
    )

    generate_bronze >> dbt_build
