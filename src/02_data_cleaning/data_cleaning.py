# =========================================
# Phase 4F: Data Cleaning & Readiness
# =========================================

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
VAL_DIR = Path("data/validation")
PROC_DIR.mkdir(parents=True, exist_ok=True)
VAL_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load raw data
# -----------------------------
users = pd.read_csv(RAW_DIR / "users_raw.csv", parse_dates=["user_created_date"])
accounts = pd.read_csv(RAW_DIR / "accounts_raw.csv")
activity = pd.read_csv(RAW_DIR / "user_activity_daily_raw.csv", parse_dates=["activity_date"])
interventions = pd.read_csv(RAW_DIR / "interventions_raw.csv", parse_dates=["intervention_date"])
outcomes = pd.read_csv(RAW_DIR / "outcomes_raw.csv", parse_dates=["activation_date"])

# -----------------------------
# Merge intervention base
# -----------------------------
base = (
    interventions
    .merge(users, on=["user_id", "account_id"], how="left")
    .merge(accounts, on="account_id", how="left")
)

# -----------------------------
# Outcome observability flags
# -----------------------------
outcomes["outcome_observed_flag"] = outcomes["collab_activated_flag"].notna().astype(int)

base = base.merge(
    outcomes[[
        "user_id",
        "intervention_id",
        "collab_activated_flag",
        "outcome_observed_flag"
    ]],
    on=["user_id", "intervention_id"],
    how="left"
)

# -----------------------------
# Temporal clipping of activity
# -----------------------------
activity_clipped = activity.merge(
    base[["user_id", "intervention_date"]],
    on="user_id",
    how="inner"
)

activity_clipped = activity_clipped[
    activity_clipped["activity_date"] < activity_clipped["intervention_date"]
]

# -----------------------------
# Windowed aggregation (30 days pre-intervention)
# -----------------------------
activity_clipped["days_before_intv"] = (
    (activity_clipped["intervention_date"] - activity_clipped["activity_date"])
    .dt.days
)

window = activity_clipped[activity_clipped["days_before_intv"] <= 30]

agg = (
    window
    .groupby("user_id")
    .agg(
        login_days_l7=("login_flag", lambda x: x[activity_clipped.loc[x.index, "days_before_intv"] <= 7].sum()),
        login_days_30d=("login_flag", "sum"),
        core_actions_30d=("core_action_count", "sum"),
        collab_actions_30d=("collab_action_count", "sum"),
        time_spent_30d=("time_spent_minutes", "sum"),
        feature_diversity_avg_30d=("feature_diversity_count", "mean"),
        days_observed_30d=("activity_date", "nunique"),
        last_active_date=("activity_date", "max")
    )
    .reset_index()
)

base = base.merge(agg, on="user_id", how="left")

# -----------------------------
# Days since last active
# -----------------------------
base["days_since_last_active"] = (
    base["intervention_date"] - base["last_active_date"]
).dt.days

# -----------------------------
# Handle missing aggregates (sparse users)
# -----------------------------

# 1. Count / sum features
# Missing means zero observed activity
zero_fill_cols = [
    "login_days_30d",
    "core_actions_30d",
    "collab_actions_30d",
    "time_spent_30d",
    "feature_diversity_avg_30d",
    "days_observed_30d"
]

base[zero_fill_cols] = base[zero_fill_cols].fillna(0)

# 2. Recency feature (CRITICAL)
# If user has no activity in the window, they are maximally stale
WINDOW_DAYS = 30

base["days_since_last_active"] = base["days_since_last_active"].fillna(WINDOW_DAYS)


# -----------------------------
# Winsorize extreme spikes (p99)
# -----------------------------
for c in [
    "core_actions_30d",
    "time_spent_30d",
    "login_days_30d"
]:
    cap = base[c].quantile(0.99)
    base[c] = np.minimum(base[c], cap)

# -----------------------------
# Final modeling base (NO feature engineering)
# -----------------------------
modeling_base = base[[
    "user_id",
    "account_id",
    "intervention_id",
    "treatment_flag",
    "outcome_observed_flag",
    "collab_activated_flag",
    "login_days_l7",
    "login_days_30d",
    "core_actions_30d",
    "collab_actions_30d",
    "time_spent_30d",
    "feature_diversity_avg_30d",
    "days_observed_30d",
    "days_since_last_active",
    "plan_tier",
    "role_type"
]]

modeling_base.to_csv(
    PROC_DIR / "modeling_base_user_level.csv",
    index=False
)

# -----------------------------
# Generate Data Quality Summary
# -----------------------------

raw_rows = len(interventions)
clean_rows = len(modeling_base)

outcome_obs_rate = modeling_base["outcome_observed_flag"].mean()
zero_activity_rate = (modeling_base["days_observed_30d"] == 0).mean()

median_days_observed = modeling_base["days_observed_30d"].median()
p95_days_observed = modeling_base["days_observed_30d"].quantile(0.95)

winsorized_counts = {
    col: int((base[col] >= base[col].quantile(0.99)).sum())
    for col in ["core_actions_30d", "time_spent_30d", "login_days_30d"]
}

with open(VAL_DIR / "data_quality_summary.md", "w", encoding="utf-8") as f:
    f.write("# Data Quality Summary — Before vs After Cleaning\n\n")

    f.write("## 1. Row Counts\n")
    f.write(f"- Raw eligible users: {raw_rows}\n")
    f.write(f"- Cleaned modeling base: {clean_rows}\n\n")

    f.write("## 2. Outcome Observability\n")
    f.write(f"- Outcome observed rate: {outcome_obs_rate:.2%}\n")
    f.write(f"- Missing outcomes retained: {1 - outcome_obs_rate:.2%}\n\n")

    f.write("## 3. Activity Coverage (30d Pre-Intervention)\n")
    f.write(f"- Users with zero observed activity: {zero_activity_rate:.2%}\n")
    f.write(f"- Median days observed: {median_days_observed}\n")
    f.write(f"- 95th percentile days observed: {p95_days_observed}\n\n")

    f.write("## 4. Winsorization Impact (p99 caps)\n")
    for col, cnt in winsorized_counts.items():
        f.write(f"- {col}: {cnt} capped values\n")

print("Generated data_quality_summary.md")

# -----------------------------
# Generate Cleaning Decisions
# -----------------------------

with open(VAL_DIR / "cleaning_decisions.md", "w", encoding="utf-8") as f:
    f.write("# Cleaning Decisions — Explicit Non-Actions\n\n")

    f.write("## Outcomes\n")
    f.write("- Missing outcomes were NOT imputed\n")
    f.write("- Rows with missing outcomes were NOT dropped\n")
    f.write("- Outcome values were never used for cleaning decisions\n\n")

    f.write("## Activity Logs\n")
    f.write("- Activity was NOT forward-filled\n")
    f.write("- Missing days were NOT inferred\n")
    f.write("- Spikes were capped, not removed\n\n")

    f.write("## Treatment Assignment\n")
    f.write("- Treatment/control balance was NOT altered\n")
    f.write("- Confounding was NOT corrected during cleaning\n\n")

    f.write("## User Population\n")
    f.write("- No users were dropped as outliers\n")
    f.write("- No filtering was based on conversion outcomes\n\n")

    f.write("## Latent Truth\n")
    f.write("- Latent uplift groups were NOT used\n")
    f.write("- No validation or cleaning referenced hidden truth\n")

print("Generated cleaning_decisions.md")

# -----------------------------
# Data readiness report
# -----------------------------
with open(VAL_DIR / "data_readiness_report.md", "w", encoding="utf-8") as f:
    f.write("# Data Readiness Report\n\n")
    f.write(f"* Rows (eligible users): {len(modeling_base)}\n")
    f.write(f"* Outcome observed rate: {modeling_base['outcome_observed_flag'].mean():.2%}\n")
    f.write(f"* Median days observed (30d): {modeling_base['days_observed_30d'].median()}\n")
    f.write(f"* % users with zero activity in window: "
            f"{(modeling_base['days_observed_30d'] == 0).mean():.2%}\n")

print("Phase 4F complete.")
