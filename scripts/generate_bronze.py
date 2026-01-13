from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

# Define bronze data directory path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)


def make_users(n_users: int = 10_000, seed: int = 7) -> pd.DataFrame:
    """
    Generates a synthetic users source table

    Columns
    - user_id: stable primary key used everywhere else
    - created_at: enables cohorting + retention windows
    - country/channel: typical slicing dimensions
    """
    rng = np.random.default_rng(seed) # reproducible results

    start = np.datetime64("2024-01-01") # first user ever
    end = np.datetime64("2025-12-31") # last user ever

    # Random signup dates
    created_at = start + rng.integers(0, (end - start).astype("timedelta64[D]").astype(int) + 1, n_users).astype("timedelta64[D]")

    countries = np.array(["UK", "IE", "FR", "DE", "NL", "ES"]) # Some user countries of origin
    channels = np.array(["organic", "paid_search", "referral", "partner", "direct"]) # Some generic signup channels

    # Build user DataFrame
    df = pd.DataFrame(
        {
            "user_id": [f"U{str(i).zfill(6)}" for i in range(1, n_users + 1)],
            "created_at": pd.to_datetime(created_at),
            "country": rng.choice(countries, size=n_users, p=[0.55, 0.05, 0.10, 0.12, 0.10, 0.08]),
            "signup_channel": rng.choice(channels, size=n_users, p=[0.45, 0.20, 0.15, 0.05, 0.15]),
        }
    )

    # Inject some realistic "bronze problems" such as missing country + inconsistent casing
    bad_idx = rng.choice(df.index, size=int(0.01 * n_users), replace=False)
    df.loc[bad_idx, "country"] = None
    df.loc[rng.choice(df.index, size=int(0.02 * n_users), replace=False), "signup_channel"] = df["signup_channel"].str.upper()

    return df


def make_subscriptions(users: pd.DataFrame, seed: int = 11) -> pd.DataFrame:
    """
    Generates a synthetic 'subscriptions' source table (Bronze)

    One row will be defined as one continuous subscription period for a synthetic user
    
    Users behaviours:
    - never subscribe
    - subscribe and churn
    - upgrade once (This adds a second row for that user)
    """
    rng = np.random.default_rng(seed)

    # Define available plans
    plans = pd.DataFrame(
        {
            "plan_id": ["free", "basic", "pro", "enterprise"],
            "billing_period": ["none", "monthly", "monthly", "annual"],
            "price_gbp": [0, 19, 49, 499],
        }
    )

    # Defining probabilities of user subscription behaviour
    # approximately 60% stay free, 40% convert to paid subscriptions at some point
    will_pay = rng.random(len(users)) < 0.40
    pay_users = users.loc[will_pay, ["user_id", "created_at"]].copy()
 
    # Determine subscription start date (creating some delay after user creation)
    delay_days = rng.integers(0, 61, size=len(pay_users))
    start_dates = pay_users["created_at"] + pd.to_timedelta(delay_days, unit="D")

    # Choosing initial paid plan
    initial_plan = rng.choice(["basic", "pro"], size=len(pay_users), p=[0.70, 0.30])

    # Build subscriptions DataFrame
    subs = pd.DataFrame(
        {
            "subscription_id": [f"S{str(i).zfill(7)}" for i in range(1, len(pay_users) + 1)],
            "user_id": pay_users["user_id"].values,
            "plan_id": initial_plan,
            "start_date": pd.to_datetime(start_dates).dt.normalize(),
        }
    )

    # Determine churn probability (basic churns more than pro)
    churn_prob = np.where(subs["plan_id"].values == "basic", 0.35, 0.20) # basic: 35%, pro: 20%
    will_churn = rng.random(len(subs)) < churn_prob

    # Assuming if churn, set end_date between 30 and 240 days after subscription start
    churn_days = rng.integers(30, 241, size=len(subs))
    end_date = subs["start_date"] + pd.to_timedelta(churn_days, unit="D")
    subs["end_date"] = pd.NaT
    subs.loc[will_churn, "end_date"] = pd.to_datetime(end_date.loc[will_churn]).dt.normalize()

    # Assume a portion of PRO users upgrades to enterprise (results in second row)
    pro_mask = subs["plan_id"] == "pro"
    will_upgrade = pro_mask & (rng.random(len(subs)) < 0.10) # 10% of pro users upgrade

    upgrades = subs.loc[will_upgrade, ["user_id", "start_date", "end_date"]].copy()
    if not upgrades.empty:
        # Assuming upgrade happens 60-180 days after start
        upgrade_offset = rng.integers(60, 181, size=len(upgrades))
        upgrade_start = upgrades["start_date"] + pd.to_timedelta(upgrade_offset, unit="D")
        upgrade_start = pd.to_datetime(upgrade_start).dt.normalize()

        # Terminate the original PRO subscription on upgrade day
        subs.loc[will_upgrade, "end_date"] = upgrade_start.values

        # Create enterprise row starting on upgrade day
        upgrades = pd.DataFrame(
            {
                "subscription_id": [f"S{str(i).zfill(7)}" for i in range(len(subs) + 1, len(subs) + 1 + len(upgrade_start))],
                "user_id": upgrades["user_id"].values,
                "plan_id": "enterprise",
                "start_date": upgrade_start.values,
                "end_date": pd.NaT,  # enterprise stays active
            }
        )

        subs = pd.concat([subs, upgrades], ignore_index=True)

    #  Billing metadata by joining plans
    subs = subs.merge(plans, on="plan_id", how="left")

    # Bronze inconsistencies: occational inconsistent casing on plan_id sometimes
    mess_idx = rng.choice(subs.index, size=int(0.01 * len(subs)), replace=False)
    subs.loc[mess_idx, "plan_id"] = subs.loc[mess_idx, "plan_id"].str.upper()

    return subs


def make_events(users: pd.DataFrame, subscriptions: pd.DataFrame, seed: int = 21) -> pd.DataFrame:
    """
    Synthetic events source table (Bronze)

    Purpose is to implement typical user engagement metrics:
    - DAU/WAU/MAU (daily/weekly/monthly active users)
    - activation rate (number of users performing key actions within 7 days of signup)
    - retention cohorts (are us ers returning to use the product over time)

    Generated events:
    - one row per event (events as such: login, view_dashboard, export_report, create_alert, billing_view)
    """
    rng = np.random.default_rng(seed)

    # Identifying which users are paying at least once
    paying_user_ids = set(subscriptions["user_id"].unique())

    # array of possible event types and their probabilities (different for free and paid users)
    event_types = np.array(
        ["login", "view_dashboard", "export_report", "create_alert", "billing_view"]
    )
    event_probs_free = np.array([0.55, 0.35, 0.04, 0.03, 0.03]) # free users are less likely to do advanced actions
    event_probs_paid = np.array([0.45, 0.38, 0.08, 0.06, 0.03]) # paid users generally more engaged

    rows = []
    event_id = 1

    # Generate per-user to make retention patterns more authentic
    for _, u in users.iterrows():
        user_id = u["user_id"]
        created_at = pd.Timestamp(u["created_at"]).normalize()

        is_paid = user_id in paying_user_ids

        # How many active days does this user produce events for?
        # Assumptions -> Free users: usually fewer days, paid users: more days
        n_active_days = rng.integers(1, 10) if not is_paid else rng.integers(5, 40)

        # Choose days after signup when the user is active
        active_offsets = np.sort(rng.choice(np.arange(0, 180), size=n_active_days, replace=False))
        active_dates = created_at + pd.to_timedelta(active_offsets, unit="D")

        for day in active_dates:
            # Events per active day
            n_events = rng.integers(1, 4) if not is_paid else rng.integers(2, 8)

            probs = event_probs_paid if is_paid else event_probs_free
            chosen = rng.choice(event_types, size=n_events, p=probs, replace=True)

            for et in chosen:
                # Random time within the day
                seconds = rng.integers(0, 24 * 3600)
                ts = day + pd.to_timedelta(seconds, unit="s")

                rows.append(
                    {
                        "event_id": f"E{event_id:010d}",
                        "user_id": user_id,
                        "event_type": et,
                        "event_ts": ts,
                    }
                )
                event_id += 1

    df = pd.DataFrame(rows)

    # Inject bronze data inconsistencies: small amount of null event_type and casing issues
    bad_idx = rng.choice(df.index, size=int(0.002 * len(df)), replace=False)
    df.loc[bad_idx, "event_type"] = None

    casing_idx = rng.choice(df.index, size=int(0.01 * len(df)), replace=False)
    df.loc[casing_idx, "event_type"] = df.loc[casing_idx, "event_type"].astype(str).str.upper()

    return df


def make_assets(n_assets: int = 250, seed: int = 31) -> pd.DataFrame:
    """
    Generates a synthetic assets table
    Context: NorthStar is based on a offshore wind farm data platform with various operational assets (turbines, met stations, edge gateways)
    One row per operational asset (device/turbine/station).
    Columns:
    - asset_id: stable primary key
    - asset_type: turbine, met_station, edge_gateway
    - region: operational region
    - installed_at: date of installation
    - capacity_kw: capacity in kW (for turbines, power draw for stations/gate)
    """
    rng = np.random.default_rng(seed)

    asset_types = np.array(["turbine", "met_station", "edge_gateway"])
    regions = np.array(["north_sea", "irish_sea", "channel", "atlantic"]) # some operational regions

    start = np.datetime64("2022-01-01")
    end = np.datetime64("2025-06-30")
    n_days = (end - start).astype("timedelta64[D]").astype(int) + 1
    installed_at = start + rng.integers(0, n_days, n_assets).astype("timedelta64[D]")

    # Build assets DataFrame
    df = pd.DataFrame(
        {
            "asset_id": [f"A{str(i).zfill(5)}" for i in range(1, n_assets + 1)],
            "asset_type": rng.choice(asset_types, size=n_assets, p=[0.55, 0.35, 0.10]),
            "region": rng.choice(regions, size=n_assets, p=[0.50, 0.20, 0.20, 0.10]),
            "installed_at": pd.to_datetime(installed_at),
        }
    )

    # Capacity depends on type of asset
    capacity = []
    for t in df["asset_type"]:
        if t == "turbine":
            capacity.append(int(rng.integers(2_000, 8_001))) # 2–8 MW (in kW)
        elif t == "met_station":
            capacity.append(int(rng.integers(5, 31))) # Small power draw for met stations
        else: 
            capacity.append(int(rng.integers(50, 301))) # Larger power draw for edge gateways
    df["capacity_kw"] = capacity

    # Bronze inconsistent data injections: inconsistent region casing occasionally
    mess_idx = rng.choice(df.index, size=int(0.02 * n_assets), replace=False)
    df.loc[mess_idx, "region"] = df.loc[mess_idx, "region"].str.upper()

    return df


def make_telemetry(assets: pd.DataFrame, start: str = "2025-01-01", end: str = "2025-03-31", seed: int = 41,) -> pd.DataFrame:
    """
    Synthetic telemetry source table. This table will contain time series data for each asset 
    showing operational status and wind speed measurements. Simulates real-world telemetry data with realistic patterns.

    Structure:
    - one row per asset per hour in the time range

    Columns:
    - asset_id (foreign key to assets table)
    - ts (timestamp) (hourly)
    - status ("up" / "down") (binary operational status)
    - wind_speed_ms (float) (measured wind speed in m/s)

    Inject realistic downtime patterns:
    - rare random failures (simulate brief glitches in data)
    - occasional multi-hour outages (storm/maintenance events) 
    """
    rng = np.random.default_rng(seed)

    # Hourly time index
    ts_index = pd.date_range(start=start, end=end, freq="h", inclusive="both", tz="UTC")
    n_t = len(ts_index)
    n_a = len(assets)

    # Cross join asset_id x timestamps (vectorized with numpy for performance)
    asset_ids = np.repeat(assets["asset_id"].values, n_t)
    ts = np.tile(ts_index.values, n_a)

    # Build asset telemetry DataFrame
    df = pd.DataFrame({"asset_id": asset_ids, "ts": pd.to_datetime(ts)})

    # Wind by region (some rough differences)
    region_map = assets.set_index("asset_id")["region"].astype(str).str.lower().to_dict()
    region = pd.Series(df["asset_id"]).map(region_map).fillna("north_sea")

    # Base wind speed by region
    region_base = {
        "north_sea": 9.5,
        "irish_sea": 8.5,
        "channel": 7.5,
        "atlantic": 10.5,
    }
    # Fill missing regions with average base
    base = region.map(region_base).fillna(9.0).astype(float).values

    # Daily wind cycle with noise 
    hour = pd.to_datetime(df["ts"]).dt.hour.values
    daily = 1.5 * np.sin(2 * np.pi * hour / 24.0)
    noise = rng.normal(0, 1.2, size=len(df))

    # Final wind speed calculation with clipping at 0
    wind = np.clip(base + daily + noise, 0, None)
    df["wind_speed_ms"] = wind.round(2)

    # Status generation
    # Start with "up" everywhere (normal functioning operation)
    status = np.array(["up"] * len(df), dtype=object)

    # Define random single-hour failures (very rare)
    random_fail = rng.random(len(df)) < 0.0015
    status[random_fail] = "down"

    # Inject a few multi-hour outage windows per asset (for maintenance/storm events)
    # This creates realistic contiguous downtime periods in conjunction with random failures
    for asset_id in assets["asset_id"].values:
        # 0-3 outage windows per asset across the time range
        n_outages = rng.integers(0, 4)
        if n_outages == 0:
            continue

        asset_mask = df["asset_id"].values == asset_id
        idxs = np.where(asset_mask)[0]

        for _ in range(n_outages):
            start_idx = rng.choice(idxs)
            duration = int(rng.integers(2, 15))  # 2 to 14 hours
            end_idx = min(start_idx + duration, idxs[-1])

            status[start_idx:end_idx] = "down"

    df["status"] = status

    # Incoporate some bronze inconsistencies e.g. missing wind speed values (simulating sensor glitches) 
    miss_idx = rng.choice(df.index, size=int(0.001 * len(df)), replace=False)
    df.loc[miss_idx, "wind_speed_ms"] = np.nan

    return df


if __name__ == "__main__":
    users = make_users()
    users_path = BRONZE_DIR / "users.parquet"
    users.to_parquet(users_path, index=False)
    print(f"Wrote {len(users):,} rows -> {users_path}")

    subscriptions = make_subscriptions(users)
    subs_path = BRONZE_DIR / "subscriptions.parquet"
    subscriptions.to_parquet(subs_path, index=False)
    print(f"Wrote {len(subscriptions):,} rows -> {subs_path}")

    events = make_events(users, subscriptions)
    events_path = BRONZE_DIR / "events.parquet"
    events.to_parquet(events_path, index=False)
    print(f"Wrote {len(events):,} rows -> {events_path}")

    assets = make_assets()
    assets_path = BRONZE_DIR / "assets.parquet"
    assets.to_parquet(assets_path, index=False)
    print(f"Wrote {len(assets):,} rows -> {assets_path}")

    telemetry = make_telemetry(assets)
    telemetry_path = BRONZE_DIR / "telemetry.parquet"
    telemetry.to_parquet(telemetry_path, index=False)
    print(f"Wrote {len(telemetry):,} rows -> {telemetry_path}")

