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


if __name__ == "__main__":
    users = make_users()
    users_path = BRONZE_DIR / "users.parquet"
    users.to_parquet(users_path, index=False)
    print(f"Wrote {len(users):,} rows -> {users_path}")

    subscriptions = make_subscriptions(users)
    subs_path = BRONZE_DIR / "subscriptions.parquet"
    subscriptions.to_parquet(subs_path, index=False)
    print(f"Wrote {len(subscriptions):,} rows -> {subs_path}")

