# =========================================
# Phase 4A: Raw Data Generation
# Accounts + Users ONLY
# =========================================

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Global Parameters (LOCKED)
# -----------------------------
N_ACCOUNTS = 2500
AVG_USERS_PER_ACCOUNT = 12

PLAN_DISTRIBUTION = {
    "starter": 0.55,
    "growth": 0.30,
    "enterprise": 0.15
}

INDUSTRIES = [
    "FinTech", "Healthcare", "SaaS", "Logistics",
    "Retail", "Manufacturing", "Education"
]

ROLES = {
    "admin": 0.15,
    "power_user": 0.35,
    "basic": 0.50
}

GEO_REGIONS = ["NA", "EU", "APAC", "LATAM"]

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2024-06-01")

# -----------------------------
# Helper Functions
# -----------------------------
def random_dates(start, end, n):
    delta = (end - start).days
    return start + pd.to_timedelta(
        np.random.randint(0, delta, size=n), unit="D"
    )

# -----------------------------
# Step 1: Generate Accounts
# -----------------------------
account_ids = [f"acct_{i:05d}" for i in range(N_ACCOUNTS)]

account_plan = np.random.choice(
    list(PLAN_DISTRIBUTION.keys()),
    size=N_ACCOUNTS,
    p=list(PLAN_DISTRIBUTION.values())
)

seat_count = []
cs_assigned = []

for plan in account_plan:
    if plan == "enterprise":
        seat_count.append(np.random.randint(50, 300))
        cs_assigned.append(1)
    elif plan == "growth":
        seat_count.append(np.random.randint(15, 80))
        cs_assigned.append(np.random.binomial(1, 0.5))
    else:
        seat_count.append(np.random.randint(3, 20))
        cs_assigned.append(0)

accounts = pd.DataFrame({
    "account_id": account_ids,
    "account_created_date": random_dates(START_DATE, END_DATE, N_ACCOUNTS),
    "plan_tier": account_plan,
    "industry": np.random.choice(INDUSTRIES, size=N_ACCOUNTS),
    "seat_count": seat_count,
    "cs_assigned_flag": cs_assigned,
    # Noisy, lagging, unreliable by design
    "account_health_score": np.clip(
        np.random.normal(loc=0.6, scale=0.15, size=N_ACCOUNTS),
        0.1, 0.95
    )
})

# -----------------------------
# Step 2: Generate Users
# -----------------------------
users_list = []

user_counter = 0

for _, acct in accounts.iterrows():
    # Right-skewed user distribution
    n_users = max(
        1,
        int(np.random.lognormal(mean=2.3, sigma=0.6))
    )

    for _ in range(n_users):
        user_counter += 1
        users_list.append({
            "user_id": f"user_{user_counter:07d}",
            "account_id": acct["account_id"],
            "user_created_date": acct["account_created_date"]
            + pd.to_timedelta(np.random.randint(0, 30), unit="D"),
            "role_type": np.random.choice(
                list(ROLES.keys()),
                p=list(ROLES.values())
            ),
            "geo_region": np.random.choice(GEO_REGIONS),
            # Incomplete invite chains by design
            "invited_by_user_id": None
            if np.random.rand() < 0.7 else "unknown_user"
        })

users = pd.DataFrame(users_list)

# -----------------------------
# Intentional Inconsistencies
# -----------------------------

# Some accounts have more active users than seat count
overfilled_accounts = np.random.choice(
    accounts["account_id"],
    size=int(0.05 * N_ACCOUNTS),
    replace=False
)

for acct_id in overfilled_accounts:
    idx = accounts.index[accounts["account_id"] == acct_id][0]
    accounts.loc[idx, "seat_count"] = max(
        1,
        accounts.loc[idx, "seat_count"] - np.random.randint(1, 5)
    )

# -----------------------------
# Save Raw Files
# -----------------------------
accounts.to_csv(RAW_DIR/"accounts_raw.csv", index=False)
users.to_csv(RAW_DIR/"users_raw.csv", index=False)

print("Phase 4A complete.")
print(f"Accounts generated: {len(accounts)}")
print(f"Users generated: {len(users)}")
