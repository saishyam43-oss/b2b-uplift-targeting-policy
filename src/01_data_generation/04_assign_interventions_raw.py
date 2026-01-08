# =========================================
# Phase 4D: Eligibility + Treatment Assignment
# (Causally Aligned, Confounded by Design)
# =========================================

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Parameters (LOCKED)
# -----------------------------
MIN_ACTIVE_DAYS = 5
TREATMENT_BASE_RATE = 0.25  # among eligible users only

ROLE_TREATMENT_MULTIPLIER = {
    "admin": 1.4,
    "power_user": 1.1,
    "basic": 0.8
}

PLAN_TREATMENT_MULTIPLIER = {
    "enterprise": 1.3,
    "growth": 1.1,
    "starter": 0.9
}

# -----------------------------
# Load Raw Data
# -----------------------------
users = pd.read_csv("data/raw/users_raw.csv")
accounts = pd.read_csv("data/raw/accounts_raw.csv")

activity = pd.read_csv(
    "data/raw/user_activity_daily_raw.csv",
    parse_dates=["activity_date"]
)

# -----------------------------
# Aggregate Pre-Treatment Activity
# -----------------------------
activity_agg = (
    activity
    .groupby("user_id")
    .agg(
        active_days=("login_flag", "sum"),
        avg_feature_diversity=("feature_diversity_count", "mean"),
        total_core_actions=("core_action_count", "sum"),
        last_activity_date=("activity_date", "max")
    )
    .reset_index()
)

df = (
    users
    .merge(activity_agg, on="user_id", how="left")
    .merge(
        accounts[["account_id", "plan_tier"]],
        on="account_id",
        how="left"
    )
    .fillna({
        "active_days": 0,
        "avg_feature_diversity": 0,
        "total_core_actions": 0
    })
)

# -----------------------------
# Step 1: Eligibility Logic (FIRST)
# -----------------------------
df["eligibility_flag"] = (
    (df["active_days"] >= 6) &                     # consistently active
    (df["total_core_actions"] >= 25) &              # real solo effort
    (df["avg_feature_diversity"] <= 1.2)            # siloed behavior
).astype(int)

# -----------------------------
# Step 2: Derive User-Relative Intervention Date
# -----------------------------
# Intervention happens shortly AFTER the observation window
df["intervention_date"] = (
    df["last_activity_date"]
    + pd.to_timedelta(
        np.random.randint(1, 4, size=len(df)), unit="D"
    )
)

# -----------------------------
# Step 3: Treatment Assignment (CONFONDED)
# -----------------------------
treatment_flags = []

for _, row in df.iterrows():

    # Hard gate: ineligible users are never treated
    if row["eligibility_flag"] == 0:
        treatment_flags.append(0)
        continue

    # Base probability
    p = TREATMENT_BASE_RATE

    # Confounding: higher activity → higher treatment probability
    activity_boost = min(row["active_days"] / 20, 1.0)
    p *= (1 + activity_boost)

    # Role bias
    p *= ROLE_TREATMENT_MULTIPLIER[row["role_type"]]

    # Plan bias
    p *= PLAN_TREATMENT_MULTIPLIER[row["plan_tier"]]

    # Clamp probability
    p = min(max(p, 0.05), 0.95)

    treatment_flags.append(int(np.random.rand() < p))

df["treatment_flag"] = treatment_flags

# -----------------------------
# Final Safety Check
# -----------------------------
assert (
    df.loc[df["eligibility_flag"] == 0, "treatment_flag"] == 0
).all(), "ERROR: Ineligible users were treated."

# -----------------------------
# Eligibility Diagnostics (Population-Level)
# -----------------------------
elig_rate_population = df["eligibility_flag"].mean()
eligible_count = df["eligibility_flag"].sum()
total_users = len(df)

print(f"Total users: {total_users}")
print(f"Eligible users: {eligible_count}")
print(f"Population eligibility rate: {elig_rate_population:.2%}")

# -----------------------------
# Construct Interventions Table
# -----------------------------
interventions = df[df["eligibility_flag"] == 1].copy()

interventions["intervention_id"] = [
    f"intv_{i:07d}" for i in range(len(interventions))
]

interventions["delivery_channel"] = np.random.choice(
    ["in_app", "email", "both"],
    size=len(interventions),
    p=[0.5, 0.3, 0.2]
)

interventions = interventions[[
    "intervention_id",
    "user_id",
    "account_id",
    "intervention_date",
    "eligibility_flag",
    "treatment_flag",
    "delivery_channel"
]]

# -----------------------------
# Save Raw File
# -----------------------------
interventions.to_csv(
    RAW_DIR/"interventions_raw.csv",
    index=False
)

print("Phase 4D complete.")
