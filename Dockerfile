FROM apache/airflow:2.9.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

RUN pip install --no-cache-dir \
    dbt-core \
    dbt-duckdb \
    duckdb \
    pandas \
    numpy \
    pyarrow

