<p align="center">
  <img src="images/logo_causalyn.png" alt="Causalyn Logo" width="300"/>
</p>

<h1 align="center">Causalyn — Precision Account Targeting with Causal Uplift</h1>  

> *Preventing Admin Churn While Capturing 80% of Value from 40% of Accounts*

---

## ⚡ Executive Snapshot

**The Problem** Blind nudging generates **~$56K** in short-term value but introduces asymmetric risk by exposing **281 Admins** to unwanted interventions. In B2B, irritating an Admin triggers account-level churn.

**My Solution** I designed a **Precision Targeting Policy** using Causal Uplift Modeling (T-Learner) wrapped in explicit safety guardrails.

**Key Outcomes** - **Safety:** I avoided **100%** of high-risk "Sleeping Dog" accounts (0.00% error rate).
- **Efficiency:** I captured **~80% of total upside** by targeting just the top **40%** of accounts.
- **Decision:** ➡️ **Ship the Precision Policy.** I rejected the blanket nudge approach to protect long-term retention.

---

## 🏢 Company Background

**Causalyn** is a fictional B2B SaaS company providing a workflow platform for enterprise teams.

The product’s success depends on **multi-user adoption within an account**, where:
- **Users** drive daily engagement.
- **Admins** control renewals and configuration.
- **Asymmetry:** A single negative Admin experience ("Rage Churn") outweighs dozens of positive User interactions.

---

## 🧠 Executive Summary

### 1. The Strategy: "Risk Filters First"
I started with 2,400 accounts. My policy explicitly eliminated **60%** of the population before optimization began, prioritizing safety (Toxic Admins) and economics (Profitability) over raw lift.

![Policy Funnel](images/01_policy_funnel.png)

### 2. The Trade-off: "Revenue vs. Churn Risk"
My analysis proved that while "Blind Nudging" (targeting everyone) maximizes theoretical revenue, it risks churning **281 Admins**. I chose to sacrifice ~40% of the potential revenue to reduce this risk to **zero**.

![Risk vs Reward](images/02_risk_vs_reward.png)

### 3. The Efficiency: "Diminishing Returns"
I identified that value is highly concentrated. By ranking accounts by **Net Expected Value**, we can capture **80% of the total upside** by targeting just the top **40%** of accounts.

![Budget Efficiency](images/03_budget_efficiency.png)

### 4. The Audit: "Zero Sleeping Dogs"
I validated the policy against a hidden ground-truth dataset. The results confirmed that my guardrails successfully suppressed **100%** of the "Sleeping Dog" segment.

![Safety Audit](images/05_failure_matrix.png)

---

## 📌 Consolidated Insights & Recommendations

### What My Analysis Revealed
1.  **Economic Units Matter:** Aggregating user scores to the account level reversed the decision for **~15% of accounts**, saving us from intervening in accounts with mixed sentiment.
2.  **Risk is Non-Linear:** High-activity users were often the most likely to react negatively (-4% lift). A standard propensity model would have targeted them; my causal model flagged them.
3.  **Guardrails > Thresholds:** Explicit business rules (e.g., "No Toxic Admins") proved more reliable than probability thresholds alone.

### My Recommendations
* **Targeting:** Roll out the intervention only to the **964 accounts** identified in [`results/final_target_accounts.csv`](results/final_target_accounts.csv).
* **Suppression:** Strictly suppress any account where a Key Decision Maker (Admin) shows negative predicted lift.
* **Budget:** Cap the campaign at the top 40% of accounts to maximize ROI.

---

## 🔍 The Challenge: Overcoming Selection Bias

The raw data contained a critical trap: **Selection Bias.**
Historically, CSMs targeted "Active Users" more often. However, these users were often "Sleeping Dogs" (annoyed by interruptions).

* **The Neutrality Gap:** This created a bias where the Treated group appeared to have a **lower average conversion** (-0.04 lift) than Control.
* **The Fix:** I implemented a **Calibrated T-Learner** (Two-Model approach).
* **The Result:** By calibrating the probabilities, I isolated the *incremental* effect of the intervention, separating "likely to buy" (Correlation) from "likely to be persuaded" (Causality).

---

## 🛡️ Policy Design & Safety Mechanisms

Prediction is not a decision. I engineered a policy layer to translate scores into actions.

| Protocol | The Logic | My Implementation |
| :--- | :--- | :--- |
| **Toxic Admin Protocol** | Admins control the contract. | If *any* Admin has negative predicted lift, suppress the *entire* account. |
| **Toxic User Threshold** | Users talk to each other. | Suppress accounts where >10% of users are predicted to react negatively. |
| **Profitability Constraint** | Support costs are real. | Suppress accounts where `(Exp. Revenue - Cost) <= 0`. |

---

## 📂 Project Structure & Code

This repository mirrors a production data science workflow. Click the links to view the source code.

| Directory | Description | Key Files |
| :--- | :--- | :--- |
| [📂 **data**](data/) | Synthetic B2B SaaS data (Users, Activity, Outcomes) | [`documentation/`](data/documentation/) |
| [📂 **src/01_data_generation**](src/01_data_generation/) | Confounding engine and ground truth generation | [`main_generation_pipeline.py`](src/01_data_generation/main_generation_pipeline.py) |
| [📂 **src/02_data_processing**](src/02_data_processing/) | Cleaning and Feature Engineering | [`02_feature_engineering.py`](src/02_data_processing/02_feature_engineering.py) |
| [📂 **src/03_models**](src/03_models/) | T-Learner training & Policy Logic | [`train_uplift_model.py`](src/03_models/train_uplift_model.py), [`account_policy.py`](src/03_models/account_policy.py) |
| [📂 **src/04_visualization**](src/04_visualization/) | Impact Analysis & Chart Generation | [`visualize_impact.py`](src/04_visualization/visualize_impact.py) |
| [📂 **results**](results/) | Final outputs and audit logs | [`final_target_accounts.csv`](results/final_target_accounts.csv) |

---

## ⚠️ Limitations

* **Synthetic Environment:** Designed for decision realism, not statistical benchmarking.
* **Static Policy:** No online learning or adaptive feedback loop.
* **Attribution:** No long-term churn or downstream revenue attribution modeled.

These constraints are intentional to keep the project focused on **decision design**, not platform engineering.

---

## 🔮 What I’d Do Next in Production

1.  **LTV-Weighted Uplift:** Optimize for Lifetime Value rather than one-time activation.
2.  **Online Policy Learning:** Implement a Contextual Bandit to adapt the policy in real-time.
3.  **Experimentation:** Integrate with A/B testing infrastructure to validate the "Toxic Admin" hypothesis in the wild.

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)
![Pandas](https://img.shields.io/badge/pandas-Data_Processing-150458?style=flat-square&logo=pandas)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-Causal_Modeling-F7931E?style=flat-square&logo=scikit-learn)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c?style=flat-square&logo=python)

---

## 📣 Call to Action

This project reflects how I approach **Product Analytics and Decision Science** problems where the goal is not just better models, but **better decisions under risk**.
