# =========================================
# Phase 4B: Raw User Activity (Pre-Treatment)
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
OBSERVATION_DAYS = 30
TOXIC_USER_RATE = 0.08  # 8% of users are "Toxic Power Users" (Sleeping Dogs)

LOGIN_PROB_BY_ROLE = {
    "admin": 0.80,
    "power_user": 0.55,
    "basic": 0.30
}

# -----------------------------
# Load Raw Users
# -----------------------------
users = pd.read_csv(
    "data/raw/users_raw.csv",
    parse_dates=["user_created_date"]
)

# Identify "Toxic" Users (High Activity, Low Diversity)
toxic_user_ids = set(users.sample(frac=TOXIC_USER_RATE, random_state=42)["user_id"])

activity_rows = []

# -----------------------------
# Generate Activity
# -----------------------------
print(f"Generating activity for {len(users)} users...")

for _, user in users.iterrows():

    user_id = user["user_id"]
    is_toxic = user_id in toxic_user_ids
    role = user["role_type"]

    # Define user-specific activity window
    activity_end_date = user["user_created_date"] + pd.Timedelta(days=OBSERVATION_DAYS)
    activity_start_date = activity_end_date - pd.Timedelta(days=OBSERVATION_DAYS)

    dates = pd.date_range(activity_start_date, activity_end_date, freq="D")

    # Base login probability
    base_login_prob = LOGIN_PROB_BY_ROLE[role]

    # Toxic users are OBSESSIVE (High login rate)
    if is_toxic:
        base_login_prob = 0.95

    for d in dates:
        # Determine Login
        if np.random.rand() < base_login_prob:

            # --- CORE ACTIONS ---
            if is_toxic:
                # Toxic users spam core actions (Mean 60)
                n_core = int(max(10, np.random.normal(60, 10)))
            elif role == "basic":
                # Basic users: Increased to 5 to pass 'Total Actions >= 25' gate
                n_core = int(np.random.poisson(5))
            else:
                # Healthy Power/Admin
                n_core = int(np.random.poisson(8))

            # --- COLLAB ACTIONS ---
            if is_toxic:
                n_collab = 0
            else:
                # Healthy users collaborate occasionally
                n_collab = int(np.random.poisson(1)) if np.random.rand() < 0.3 else 0

            # --- DIVERSITY COUNT (THE CRITICAL FIX) ---
            if is_toxic:
                # Toxic: High Activity but Low Diversity (Stuck)
                # Skew heavily to 1 to pass <= 1.2 threshold reliably (Mean 1.1)
                n_diversity = np.random.choice([1, 2], p=[0.9, 0.1])
            elif role == "basic":
                # Basic: Low Activity AND Low Diversity (Stuck -> ELIGIBLE TARGET)
                # Skew heavily to 1 to pass <= 1.2 threshold reliably (Mean 1.1)
                n_diversity = np.random.choice([1, 2], p=[0.9, 0.1])
            else:
                # Healthy Power/Admin: High Diversity (Not Stuck -> Ineligible)
                n_diversity = np.random.randint(3, 7)

            # --- TIME SPENT ---
            if is_toxic:
                t_spent = n_core * np.random.randint(3, 6)
            else:
                t_spent = max(5, n_core * 5 + np.random.randint(-5, 15))

            activity_rows.append({
                "user_id": user_id,
                "activity_date": d,
                "login_flag": 1,
                "core_action_count": n_core,
                "collab_action_count": n_collab,
                "time_spent_minutes": t_spent,
                "feature_diversity_count": n_diversity
            })

# -----------------------------
# Save
# -----------------------------
activity_df = pd.DataFrame(activity_rows)
activity_df.to_csv(RAW_DIR / "user_activity_daily_raw.csv", index=False)
print("Phase 4B complete: user_activity_daily_raw.csv generated.")
