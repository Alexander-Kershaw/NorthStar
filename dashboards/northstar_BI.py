import streamlit as st
import duckdb
from pathlib import Path
import os

st.set_page_config(page_title="NorthStar BI", layout="wide")
st.title("NorthStar BI")
st.caption("Local DuckDB, dbt marts, and MetricFlow dashboarding demo")

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
DB_PATH = DBT_DIR / "warehouse" / "northstar.duckdb"

os.chdir(DBT_DIR)

# Sidebar controls
days_back = st.slider("Days of activity to display", min_value=7, max_value=180, value=60, step=7)

@st.cache_data
# Load monthly revenue summary from DuckDB
def load_monthly_revenue(DB_PATH: str):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        select
            month_start,
            avg_mrr_gbp,
            end_of_month_mrr_gbp,
            avg_paying_users,
            end_of_month_paying_users
        from mart_revenue_summary_monthly
        order by month_start
    """).df()
    con.close()
    return df

# Load daily active users from DuckDB
@st.cache_data
def load_dau(DB_PATH: str, days_back: int):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(f"""
        select
            date_day,
            count(distinct user_id) as dau
        from fct_usage_daily
        where is_active = 1
          and date_day >= current_date - interval {days_back} day
        group by 1
        order by 1
    """).df()
    con.close()
    return df

# Load list of regions from DuckDB
@st.cache_data
def load_regions(DB_PATH: str):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    regions = con.execute("""
        select distinct region
        from dim_asset
        order by 1
    """).fetchall()
    con.close()
    return [r[0] for r in regions]

# Load uptime by region from DuckDB
@st.cache_data
def load_uptime_by_region(DB_PATH: str, region: str, days_back: int):
    con = duckdb.connect(str(DB_PATH), read_only=True)

    # Anchor to the latest available date in the mart
    max_day = con.execute("""
        select max(date_day) as max_day
        from mart_uptime_region_daily
        where region is not null
    """).fetchone()[0]

    if max_day is None:
        con.close()
        return None

    df = con.execute("""
        select
            date_day,
            avg_uptime_pct
        from mart_uptime_region_daily
        where region = ?
          and date_day >= (?::date - (? * interval 1 day))
          and date_day <= ?::date
        order by 1
    """, [region, max_day, days_back, max_day]).df()

    con.close()
    return df

try:
    df = load_monthly_revenue(DB_PATH)
    st.subheader("Monthly revenue summary")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("MRR (end of month)")
    chart_df = df.set_index("month_start")[["end_of_month_mrr_gbp"]]
    st.line_chart(chart_df)

    st.subheader("Daily Active Users (DAU)")
    dau_df = load_dau(DB_PATH, days_back)
    st.line_chart(dau_df.set_index("date_day")[["dau"]])

    st.subheader("Uptime by region")
    regions = load_regions(DB_PATH)
    if regions:
        selected_region = st.selectbox("Region", regions, index=0)
        up_df = load_uptime_by_region(DB_PATH, selected_region, days_back)

        if up_df is None or up_df.empty:
            st.info("No uptime rows returned for that region/date window.")
        else:
            st.line_chart(up_df.set_index("date_day")[["avg_uptime_pct"]])
    else:
        st.info("No regions found in dim_asset.")


except Exception as e:
    st.error("Could not load data from DuckDB. Check DB_PATH and that dbt has built the marts.")
    st.code(str(e))
