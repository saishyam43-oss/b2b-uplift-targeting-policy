# =========================================
# Phase 4C: Latent Uplift Group Assignment
# (Hidden Ground Truth)
# =========================================

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load Required Raw Data
# -----------------------------
users = pd.read_csv("data/raw/users_raw.csv")
activity = pd.read_csv(
    "data/raw/user_activity_daily_raw.csv",
    parse_dates=["activity_date"]
)

# -----------------------------
# Aggregate Pre-Treatment Signals
# -----------------------------
activity_agg = (
    activity
    .groupby("user_id")
    .agg(
        active_days=("login_flag", "sum"),
        avg_core_actions=("core_action_count", "mean"),
        avg_feature_diversity=("feature_diversity_count", "mean"),
        total_time_spent=("time_spent_minutes", "sum"),
        collab_days=("collab_action_count", lambda x: (x > 0).sum())
    )
    .reset_index()
)

user_signals = users.merge(activity_agg, on="user_id", how="left").fillna(0)

# -----------------------------
# Normalize Signals (0-1) for Logic
# -----------------------------
def min_max(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)

user_signals["activity_score"] = (
    0.7 * min_max(user_signals["avg_core_actions"]) +
    0.3 * min_max(user_signals["total_time_spent"])
)

user_signals["collab_tendency"] = min_max(user_signals["avg_feature_diversity"])

# -----------------------------
# Latent Group Assignment Logic
# -----------------------------
latent_groups = []

for _, row in user_signals.iterrows():

    a = row["activity_score"]
    c = row["collab_tendency"]

    # --- BASE PROBABILITIES ---
    probs = {
        "sure_thing": 0.35 * a + 0.25 * c,
        "persuadable": 0.40 * (1 - c) + 0.25 * a,
        "sleeping_dog": 0.30 * a * (1 - c),
        "lost_cause": 0.50 * (1 - a)
    }

    # --- LOGIC OVERRIDE FOR TOXIC USERS ---
    # If High Activity AND Low Diversity -> Force Sleeping Dog
    # This aligns the label with the features generated in Phase 4B
    if a > 0.6 and c < 0.25:
        probs["sleeping_dog"] += 0.5  # Massive boost to ensure assignment
        probs["persuadable"] *= 0.1   # Penalize persuadable (they are stuck, not open)

    # Add noise to prevent perfect separability
    for k in probs:
        probs[k] += np.random.normal(0, 0.02)

    # Ensure valid probability distribution
    probs = {k: max(v, 0.01) for k, v in probs.items()}
    total = sum(probs.values())
    probs = {k: v / total for k, v in probs.items()}

    latent_groups.append(
        np.random.choice(
            list(probs.keys()),
            p=list(probs.values())
        )
    )

# -----------------------------
# Save Hidden Labels
# -----------------------------
output = pd.DataFrame({
    "user_id": user_signals["user_id"],
    "latent_uplift_group": latent_groups
})

output.to_csv(RAW_DIR / "latent_uplift_groups_hidden.csv", index=False)
print("Phase 4C complete: latent_uplift_groups_hidden.csv generated.")
