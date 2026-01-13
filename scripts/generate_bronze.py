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


if __name__ == "__main__":
    users = make_users()
    users_path = BRONZE_DIR / "users.parquet"
    users.to_parquet(users_path, index=False)
    print(f"Wrote {len(users):,} rows -> {users_path}")
