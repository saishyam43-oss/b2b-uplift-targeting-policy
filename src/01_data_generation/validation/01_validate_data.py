# =========================================
# Script: 01_validate_data.py
# Purpose: Causal Audit & Statistical Health Check
# =========================================

import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
VAL_DIR = RAW_DIR / "validation"
VAL_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = VAL_DIR / "generation_report.md"

def log(msg, mode="a"):
    print(msg)
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        f.write(msg + "\n")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("# Synthetic Data Generation Report\n\n")

# -----------------------------
# 1. Load Data
# -----------------------------
log("## 1. Loading Data...")

users = pd.read_csv(RAW_DIR / "users_raw.csv", parse_dates=["user_created_date"])
accounts = pd.read_csv(RAW_DIR / "accounts_raw.csv")
activity = pd.read_csv(RAW_DIR / "user_activity_daily_raw.csv", parse_dates=["activity_date"])
interventions = pd.read_csv(RAW_DIR / "interventions_raw.csv", parse_dates=["intervention_date"])
outcomes = pd.read_csv(RAW_DIR / "outcomes_raw.csv", parse_dates=["activation_date"])
latent = pd.read_csv(RAW_DIR / "latent_uplift_groups_hidden.csv")

log("✅ All files loaded successfully.")

# -----------------------------
# 2. Shape & Integrity Checks
# -----------------------------
log("\n## 2. Shape & Integrity Checks")

log(f"* **Accounts:** {len(accounts)}")
log(f"* **Users:** {len(users)}")
log(f"* **Activity Rows:** {len(activity)}")
log(f"* **Interventions:** {len(interventions)}")
log(f"* **Outcomes:** {len(outcomes)}")

assert users["user_id"].nunique() == len(users), "❌ Duplicate user_ids detected"
log("* **Uniqueness:** User IDs are unique.")

# -----------------------------
# 3. Causal Logic Validation
# -----------------------------
log("\n## 3. Causal Logic Validation")

# A. Eligibility hard gate
bad_treatment = interventions[
    (interventions["eligibility_flag"] == 0) &
    (interventions["treatment_flag"] == 1)
]
assert len(bad_treatment) == 0, "❌ Ineligible users were treated"
log("✅ PASS: No ineligible users were treated.")

# B. Activity strictly before intervention
max_activity = activity.groupby("user_id")["activity_date"].max().reset_index()
tmp = interventions.merge(max_activity, on="user_id", how="left")

leakage = tmp[tmp["intervention_date"] <= tmp["activity_date"]]
assert len(leakage) == 0, "❌ Activity after intervention detected"
log("✅ PASS: All activity strictly precedes intervention.")

# C. Intervention strictly before outcome
tmp2 = interventions.merge(outcomes, on=["user_id", "intervention_id"])
bad_outcomes = tmp2[
    (tmp2["collab_activated_flag"] == 1) &
    (tmp2["activation_date"] <= tmp2["intervention_date"])
]
assert len(bad_outcomes) == 0, "❌ Activation before intervention detected"
log("✅ PASS: All activations strictly follow interventions.")

# -----------------------------
# 4. Eligibility Sanity Checks (REALISTIC)
# -----------------------------
log("\n## 4. Eligibility Sanity Checks")

# Population-level eligibility rate
elig_count = len(interventions)
total_users = len(users)
elig_rate = elig_count / total_users

log(f"* **Total Users:** {total_users}")
log(f"* **Eligible Users:** {elig_count}")
log(f"* **Population Eligibility Rate:** {elig_rate:.2%}")

assert elig_rate < 0.90, (
    f"❌ Eligibility rate ({elig_rate:.2%}) too high. Gate is too open."
)

# Aggregate activity per user
activity_agg = (
    activity
    .groupby("user_id")
    .agg(
        login_days=("login_flag", "sum"),
        avg_diversity=("feature_diversity_count", "mean")
    )
    .reset_index()
)

elig_activity = users.merge(activity_agg, on="user_id", how="left").fillna(0)
elig_activity["is_eligible"] = elig_activity["user_id"].isin(interventions["user_id"])

# ---- Check 4A: Low-activity users mostly excluded (Lost Causes)
low_activity_users = elig_activity[elig_activity["login_days"] < 3]
low_activity_eligible_rate = low_activity_users["is_eligible"].mean()

assert low_activity_eligible_rate < 0.20, (
    "❌ Too many low-activity users are eligible. "
    "Lost Causes are leaking into eligibility."
)

log("✅ PASS: Low-activity users are mostly excluded.")

# ---- Check 4B: Eligibility concentrates in mid-activity band (Stuck Users)
q25, q75 = elig_activity["login_days"].quantile([0.25, 0.75])
mid_band = elig_activity[
    (elig_activity["login_days"] >= q25) &
    (elig_activity["login_days"] <= q75)
]

mid_band_eligible_rate = mid_band["is_eligible"].mean()

assert mid_band_eligible_rate > 0.40, (
    "❌ Eligibility is not focused on mid-activity users. "
    "Gate is not targeting 'stuck but trying' users."
)

log("✅ PASS: Eligibility concentrates in mid-activity band.")

# ---- Check 4C: High-diversity users mostly excluded (Sure Things)
high_div_users = elig_activity[elig_activity["avg_diversity"] > 2]
high_div_eligible_rate = high_div_users["is_eligible"].mean()

assert high_div_eligible_rate < 0.30, (
    "❌ Too many high-diversity users are eligible. "
    "Explorers / collaborators should not be nudged."
)

log("✅ PASS: High-diversity users are mostly excluded.")

# -----------------------------
# 5. Hidden Uplift Physics Check
# -----------------------------
log("\n## 5. Hidden Uplift Physics Check")

master = (
    interventions
    .merge(outcomes, on=["user_id", "intervention_id"])
    .merge(latent, on="user_id")
)

uplift = (
    master
    .groupby(["latent_uplift_group", "treatment_flag"])
    ["collab_activated_flag"]
    .mean()
    .unstack()
)

uplift.columns = ["Control Rate", "Treatment Rate"]
uplift["Observed Lift"] = uplift["Treatment Rate"] - uplift["Control Rate"]

log("\n" + uplift.to_markdown(floatfmt=".3f"))

assert uplift.loc["persuadable", "Observed Lift"] > 0.10, "❌ Persuadables not lifting"
assert uplift.loc["sleeping_dog", "Observed Lift"] < -0.05, "❌ Sleeping Dogs not backfiring"

log("✅ PASS: Hidden uplift physics validated.")

# -----------------------------
# 6. Global Statistics
# -----------------------------
log("\n## 6. Global Statistics")

treated_cr = master[master["treatment_flag"] == 1]["collab_activated_flag"].mean()
control_cr = master[master["treatment_flag"] == 0]["collab_activated_flag"].mean()

log(f"* **Treated Activation Rate:** {treated_cr:.2%}")
log(f"* **Control Activation Rate:** {control_cr:.2%}")
log(f"* **Global ATE:** {(treated_cr - control_cr):.2%}")

log("\n✅ Validation Complete.")
