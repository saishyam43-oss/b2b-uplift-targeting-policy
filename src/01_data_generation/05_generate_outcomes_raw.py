# =========================================
# Phase 4E: Outcome Generation
# (Counterfactual, Latent-Group Driven)
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
OUTCOME_WINDOW_DAYS = 21

# Base probabilities by latent group
GROUP_PROBS = {
    "persuadable": {
        "treated": 0.60,
        "untreated": 0.10
    },
    "sleeping_dog": {
        "treated": 0.15,     # STRONGER backfire
        "untreated": 0.50
    },
    "sure_thing": {
        "treated": 0.75,
        "untreated": 0.70
    },
    "lost_cause": {
        "treated": 0.08,
        "untreated": 0.05
    }
}

# Noise parameters
PROB_NOISE_STD = 0.05
OUTCOME_MISSING_RATE = 0.06

# -----------------------------
# Load Data
# -----------------------------
interventions = pd.read_csv(
    RAW_DIR / "interventions_raw.csv",
    parse_dates=["intervention_date"]
)

latent_truth = pd.read_csv(
    RAW_DIR / "latent_uplift_groups_hidden.csv"
)

# -----------------------------
# Merge Hidden Truth (IN MEMORY)
# -----------------------------
df = interventions.merge(
    latent_truth,
    on="user_id",
    how="left"
)

# -----------------------------
# Simulate Counterfactual Worlds
# -----------------------------
prob_treated = []
prob_untreated = []

for _, row in df.iterrows():
    group = row["latent_uplift_group"]

    p_t = GROUP_PROBS[group]["treated"]
    p_u = GROUP_PROBS[group]["untreated"]

    # Inject individual-level noise
    # Sleeping Dogs get LOWER noise to preserve backfire signal
    if group == "sleeping_dog":
        p_t += np.random.normal(0, PROB_NOISE_STD * 0.5)
        p_u += np.random.normal(0, PROB_NOISE_STD * 0.5)
    else:
        p_t += np.random.normal(0, PROB_NOISE_STD)
        p_u += np.random.normal(0, PROB_NOISE_STD)

    # Clamp probabilities
    p_t = min(max(p_t, 0.01), 0.99)
    p_u = min(max(p_u, 0.01), 0.99)

    prob_treated.append(p_t)
    prob_untreated.append(p_u)

df["prob_outcome_if_treated"] = prob_treated
df["prob_outcome_if_untreated"] = prob_untreated

# -----------------------------
# Observe Only One World
# -----------------------------
observed_outcomes = []
activation_dates = []

for _, row in df.iterrows():

    if row["treatment_flag"] == 1:
        p = row["prob_outcome_if_treated"]
    else:
        p = row["prob_outcome_if_untreated"]

    outcome = np.random.rand() < p
    observed_outcomes.append(int(outcome))

    if outcome:
        delay = np.random.randint(1, OUTCOME_WINDOW_DAYS + 3)
        activation_dates.append(
            row["intervention_date"] + pd.Timedelta(days=delay)
        )
    else:
        activation_dates.append(pd.NaT)

df["collab_activated_flag"] = observed_outcomes
df["activation_date"] = activation_dates

# -----------------------------
# Apply Outcome Window Censoring
# -----------------------------
df.loc[
    (df["activation_date"] - df["intervention_date"]).dt.days
    > OUTCOME_WINDOW_DAYS,
    ["collab_activated_flag", "activation_date"]
] = [0, pd.NaT]

# -----------------------------
# Inject Missing Outcomes
# -----------------------------
missing_idx = df.sample(
    frac=OUTCOME_MISSING_RATE,
    random_state=42
).index

df.loc[missing_idx, ["collab_activated_flag", "activation_date"]] = [np.nan, pd.NaT]

# -----------------------------
# Construct Outcomes Table (RAW)
# -----------------------------
outcomes = df[[
    "user_id",
    "intervention_id",
    "collab_activated_flag",
    "activation_date"
]].copy()

outcomes["outcome_window_days"] = OUTCOME_WINDOW_DAYS

# -----------------------------
# Save Raw File
# -----------------------------
outcomes.to_csv(
    RAW_DIR / "outcomes_raw.csv",
    index=False
)

print("Phase 4E complete.")
print("Observed activation rate:", outcomes["collab_activated_flag"].mean())
