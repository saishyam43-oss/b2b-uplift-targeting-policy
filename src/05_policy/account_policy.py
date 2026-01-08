# =========================================
# Phase 7: Account-Level Decision Policy
# Purpose: Aggregate User Scores -> Account Decisions (With Admin Guardrails)
# =========================================

import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# Configuration (The "Business Logic")
# -----------------------------
VALUE_PER_CONVERSION = 50.00  # $50 Value for a "Collab Activation"
COST_PER_NUDGE = 1.00         # $1 Cost per email/in-app message
SLEEPING_DOG_THRESHOLD = -0.01 # Uplift below this is "Toxic"

# -----------------------------
# Setup
# -----------------------------
RESULTS_DIR = Path("results")
RAW_DIR = Path("data/raw")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("Loading data...")
# Load predictions
df = pd.read_csv(RESULTS_DIR / "user_level_uplift_scores.csv")

# Load User Roles (Crucial for the Admin Guardrail)
users = pd.read_csv(RAW_DIR / "users_raw.csv", usecols=["user_id", "role_type"])

# Merge Roles onto Predictions
df = df.merge(users, on="user_id", how="left")

# -----------------------------
# 1. Account Aggregation
# -----------------------------
print("Aggregating to Account Level...")

def get_account_stats(x):
    n_users = len(x)
    sum_uplift = x["pred_uplift"].sum()

    # 1. General Toxicity: How many users are negative?
    n_dogs = (x["pred_uplift"] < SLEEPING_DOG_THRESHOLD).sum()
    dog_rate = n_dogs / n_users

    # 2. SPECIFIC GUARDRAIL: Toxic Admin
    # Is there ANY Admin who is a Sleeping Dog?
    # Logic: Role is 'admin' AND Uplift is Negative
    toxic_admin_mask = (x["role_type"] == "admin") & (x["pred_uplift"] < SLEEPING_DOG_THRESHOLD)
    has_toxic_admin = toxic_admin_mask.any()

    # Financial Calculation
    expected_revenue = sum_uplift * VALUE_PER_CONVERSION
    cost = n_users * COST_PER_NUDGE
    net_value = expected_revenue - cost

    return pd.Series({
        "n_users": n_users,
        "n_dogs": n_dogs,
        "dog_rate": dog_rate,
        "has_toxic_admin": has_toxic_admin,
        "sum_uplift": sum_uplift,
        "expected_revenue": expected_revenue,
        "cost": cost,
        "net_account_value": net_value
    })

# FIX: Added include_groups=False to silence FutureWarning
accounts = df.groupby("account_id").apply(get_account_stats, include_groups=False).reset_index()

# -----------------------------
# 2. Decision Logic (The Policy)
# -----------------------------
def make_decision(row):
    # Guardrail 1: THE TOXIC ADMIN (Highest Priority)
    # If the decision maker is a Sleeping Dog, DO NOT TOUCH the account.
    if row["has_toxic_admin"]:
        return "suppress_toxic_admin"

    # Guardrail 2: General Toxicity
    # If > 10% of users are haters, leave them alone.
    if row["dog_rate"] > 0.10:
        return "suppress_toxic_users"

    # Guardrail 3: Profitability
    # Don't spend money to lose money.
    if row["net_account_value"] <= 0:
        return "suppress_unprofitable"

    # Guardrail 4: Small Account Noise
    if row["n_users"] < 2:
        return "suppress_too_small"

    # If passed all gates -> TREAT
    return "treat_account"

accounts["decision"] = accounts.apply(make_decision, axis=1)

# -----------------------------
# 3. Impact Analysis
# -----------------------------
print("\n=== ACCOUNT DECISION SUMMARY ===")
print(accounts["decision"].value_counts())

treatable = accounts[accounts["decision"] == "treat_account"]
toxic_admin_saves = accounts[accounts["decision"] == "suppress_toxic_admin"]

print(f"\nTotal Accounts: {len(accounts)}")
print(f"Treatable Accounts: {len(treatable)} ({len(treatable)/len(accounts):.1%})")
print(f"Toxic Admin Saves: {len(toxic_admin_saves)} (Accounts saved from potential churn)")
print(f"Projected Net Value (Treatable): ${treatable['net_account_value'].sum():,.2f}")

# -----------------------------
# 4. Save Final List
# -----------------------------
# We save the LIST of accounts to target
target_list = treatable[["account_id", "net_account_value", "n_users"]]
target_list.to_csv(RESULTS_DIR / "final_target_accounts.csv", index=False)
print(f"\nTarget list saved to: {RESULTS_DIR / 'final_target_accounts.csv'}")

# Save full debug log (useful for analyzing why accounts were suppressed)
accounts.to_csv(RESULTS_DIR / "account_policy_debug.csv", index=False)
