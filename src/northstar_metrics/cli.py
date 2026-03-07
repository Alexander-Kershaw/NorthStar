from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(help="NorthStar project CLI")

ROOT = Path(__file__).resolve().parents[2]
DBT_DIR = ROOT / "dbt"
APP_FILE = ROOT / "dashboards" / "northstar_BI.py"
BRONZE_SCRIPT = ROOT / "scripts" / "generate_bronze.py"
AIRFLOW_COMPOSE = ROOT / "docker-compose.airflow.yml"


def run_command(command: str, cwd: Path | None = None) -> None:
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

# Generate Bronze data
@app.command("generate")
def generate_bronze() -> None:
    typer.echo("=====|Generating Bronze data...|=====")
    run_command(f"{sys.executable} {BRONZE_SCRIPT}", cwd=ROOT)
    typer.echo("Bronze generation complete.")

# dbt build for warehouse
@app.command("build")
def build_warehouse() -> None:
    typer.echo("=====|Running dbt build...|=====")
    run_command("dbt build", cwd=DBT_DIR)
    typer.echo("dbt build complete.")

# Geberate dbt docs
@app.command("docs")
def build_docs() -> None:
    typer.echo("=====|Generating dbt docs...|=====")
    run_command("dbt docs generate", cwd=DBT_DIR)
    typer.echo("dbt docs generated.")

# Launch streamlit dashboard
@app.command("dashboard")
def run_dashboard() -> None:
    typer.echo("=====|Launching Streamlit dashboard...|=====")
    run_command(f"streamlit run {APP_FILE}", cwd=ROOT)

# Start Apache Airflow stack
@app.command("airflow-up")
def airflow_up() -> None:
    typer.echo("=====|Starting Airflow...|=====")
    run_command(f"docker compose -f {AIRFLOW_COMPOSE} up -d", cwd=ROOT)
    typer.echo("Airflow started.")

# Stop Airflow stack
@app.command("airflow-down")
def airflow_down() -> None:
    typer.echo("=====|Stopping Airflow...|=====")
    run_command(f"docker compose -f {AIRFLOW_COMPOSE} down", cwd=ROOT)
    typer.echo("Airflow stopped.")

# Full run
@app.command("full-run")
def full_run() -> None:
    typer.echo("=====|Running full NorthStar pipeline...|=====")
    run_command(f"{sys.executable} {BRONZE_SCRIPT}", cwd=ROOT)
    run_command("dbt build", cwd=DBT_DIR)
    typer.echo("Full pipeline complete.")


if __name__ == "__main__":
    app()