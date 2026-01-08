# =========================================
# Phase 5B: Feature Engineering (User Level)
# =========================================

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
FEAT_DIR = Path("data/features")
FEAT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load inputs
# -----------------------------
base = pd.read_csv(PROC_DIR / "modeling_base_user_level.csv")
accounts = pd.read_csv(RAW_DIR / "accounts_raw.csv")

# -----------------------------
# Controlled account join
# -----------------------------
accounts_small = accounts[["account_id", "seat_count"]]

df = base.merge(accounts_small, on="account_id", how="left")

# -----------------------------
# Derive account_size_bucket
# -----------------------------
def bucket_seats(x):
    if x <= 10:
        return "small"
    elif x <= 50:
        return "mid"
    else:
        return "large"

df["account_size_bucket"] = df["seat_count"].apply(bucket_seats)

# Drop raw seat count immediately
df = df.drop(columns=["seat_count"])

# -----------------------------
# Derived behavioral features
# -----------------------------
df["momentum_ratio"] = df["login_days_l7"] / (df["login_days_30d"] + 1)

# Explicit interaction capturing "over-collaboration risk"
df["collab_intensity_ratio"] = (
    df["collab_actions_30d"] / (df["login_days_30d"] + 1)
)

# -----------------------------
# Log transforms for skewed counts
# -----------------------------
log_cols = [
    "login_days_30d",
    "login_days_l7",
    "core_actions_30d",
    "time_spent_30d",
    "collab_actions_30d"
]

for c in log_cols:
    df[f"log_{c}"] = np.log1p(df[c])

# -----------------------------
# One-hot encode categoricals
# -----------------------------
cat_cols = ["role_type", "plan_tier", "account_size_bucket"]

df = pd.get_dummies(
    df,
    columns=cat_cols,
    drop_first=True
)

# -----------------------------
# Final feature table
# -----------------------------
FEATURE_COLS = [
    # Identifiers (REQUIRED)
    "user_id",
    "account_id",
    "intervention_id",

    # Raw numeric
    "login_days_30d",
    "login_days_l7",
    "core_actions_30d",
    "collab_actions_30d",
    "time_spent_30d",
    "feature_diversity_avg_30d",
    "days_observed_30d",
    "days_since_last_active",

    # Derived
    "momentum_ratio",
    "collab_intensity_ratio",

    # Log transforms
    "log_login_days_30d",
    "log_login_days_l7",
    "log_core_actions_30d",
    "log_time_spent_30d",
    "log_collab_actions_30d",

    # Control & target flags (kept intentionally)
    "treatment_flag",
    "collab_activated_flag",
    "outcome_observed_flag"
] + [c for c in df.columns if c.startswith(
    ("role_type_", "plan_tier_", "account_size_bucket_")
)]

final_df = df[FEATURE_COLS]

final_df.to_csv(
    FEAT_DIR / "features_user_level.csv",
    index=False
)

print("Phase 5B complete: features_user_level.csv generated.")
