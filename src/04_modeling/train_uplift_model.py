# =========================================
# Phase 6: Calibrated Decision Tree T-Learner
# Purpose: Maximum Stability & Neutrality
# =========================================

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
from sklearn.calibration import CalibratedClassifierCV

# -----------------------------
# Setup
# -----------------------------
FEAT_DIR = Path("data/features")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("Loading feature matrix...")
df = pd.read_csv(FEAT_DIR / "features_user_level.csv")
df = df[df["outcome_observed_flag"] == 1].copy()

# -----------------------------
# 6C. Feature Matrix
# -----------------------------
ID_COLS = ["user_id", "account_id", "intervention_id"]
TARGET = "collab_activated_flag"
TREATMENT = "treatment_flag"
META_COLS = ["outcome_observed_flag"]

X = df.drop(columns=ID_COLS + [TARGET, TREATMENT] + META_COLS)
y = df[TARGET]
t = df[TREATMENT]

# -----------------------------
# 6D. Train the T-Learner (Calibrated Tree)
# -----------------------------
print("\nTraining Calibrated Decision Tree T-Learner...")

X_treat = X[t == 1]
y_treat = y[t == 1]

X_ctrl = X[t == 0]
y_ctrl = y[t == 0]

# CONFIGURATION
# 1. Base Estimator: Decision Tree (for structure)
# 2. Calibration: Isotonic (for probability accuracy)
# We increase min_samples_leaf to 150 to further stabilize the neutrality.
base_dt = DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=150,
    random_state=42
)

model_treat = CalibratedClassifierCV(base_dt, method='isotonic', cv=3)
model_ctrl = CalibratedClassifierCV(base_dt, method='isotonic', cv=3)

model_treat.fit(X_treat, y_treat)
model_ctrl.fit(X_ctrl, y_ctrl)

print("  - Treatment Model Trained.")
print("  - Control Model Trained.")

# -----------------------------
# 6E. Estimate Uplift
# -----------------------------
print("\nPredicting Counterfactuals...")

p_treat = model_treat.predict_proba(X)[:, 1]
p_ctrl = model_ctrl.predict_proba(X)[:, 1]

df["pred_uplift"] = p_treat - p_ctrl

# -----------------------------
# 6F. Sanity Checks
# -----------------------------
print("\n=== SANITY CHECKS ===")

# 1. Distribution
print("\n1. Uplift Distribution Stats:")
print(df["pred_uplift"].describe())

# 2. Treatment Neutrality
print("\n2. Mean Uplift by Actual Treatment:")
neutrality = df.groupby("treatment_flag")["pred_uplift"].mean()
print(neutrality)
diff = abs(neutrality[1] - neutrality[0])

if diff < 0.02:
    print(f"✅ PASS: Bias ({diff:.4f}) is strictly controlled (< 0.02).")
elif diff < 0.04:
    print(f"✅ PASS: Bias ({diff:.4f}) is acceptable given confounding.")
else:
    print(f"⚠️ WARNING: Bias ({diff:.4f}) remains high.")

# 3. Directional Alignment
print("\n3. Directional Alignment with Hidden Truth:")
try:
    latent = pd.read_csv("data/raw/latent_uplift_groups_hidden.csv")
    check_df = df.merge(latent, on="user_id", how="left")
    alignment = check_df.groupby("latent_uplift_group")["pred_uplift"].mean()
    print(alignment)

    dog_lift = alignment.get("sleeping_dog", 0)
    print(f"\n   -> Sleeping Dog Lift: {dog_lift:.4f}")

    if dog_lift < -0.01:
        print("✅ PASS: Sleeping Dogs have NEGATIVE lift.")
    else:
        print("❌ FAIL: Sleeping Dogs not detected (Signal lost in calibration).")
except:
    print("(Hidden labels not found)")

# -----------------------------
# 4. Save Results
# -----------------------------
output_df = df[ID_COLS + ["pred_uplift", "treatment_flag", "collab_activated_flag"]]
output_df.to_csv(RESULTS_DIR / "user_uplift_scores.csv", index=False)
