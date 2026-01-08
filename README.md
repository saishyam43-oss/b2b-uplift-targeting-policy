<p align="center">
  <img src="images/logo_causalyn.png" alt="Causalyn Logo" width="180"/>
</p>

# 🎯 Causalyn — Precision Account Targeting with Causal Uplift  
**Preventing Admin Churn While Capturing 80% of Value from 40% of Accounts**

---

## ⚡ TL;DR

**What this is**
- A decision system that determines **which B2B accounts should be nudged and which should be left alone**, using causal uplift modeling and explicit safety guardrails.

**How to read this**
- Skim the visuals and bold insights first.
- Read deeper only if you want to understand *how* the decisions were built and validated.

**Key outcome**
- Blind nudging generates **~$56K** short-term value but risks **churning 281 admins**.
- A precision policy targets **~40% of accounts**, captures **~80% of total value**, and **avoids all high-risk admin interventions**.
- Output is a **production-ready account policy**, not a model score.

➡️ **Decision**: Ship the Precision Policy. Do not ship blanket nudges.

---

## 🧠 Executive Summary

### 1️⃣ Policy Funnel — How 2,400 Accounts Became 964 Targets
<p align="center">
  <img src="images/01_policy_funnel.png" width="700"/>
</p>

- 60% of accounts are suppressed *before* value optimization.
- Suppression is driven by **risk and economics**, not model uncertainty.

---

### 2️⃣ Risk vs Reward — Why Blind Nudging Is Dangerous
<p align="center">
  <img src="images/02_risk_vs_reward.png" width="700"/>
</p>

- Blind nudging maximizes short-term revenue.
- It exposes **281 admins** to negative interventions, creating asymmetric downside.

---

### 3️⃣ Budget Efficiency — Where the Value Actually Comes From
<p align="center">
  <img src="images/03_budget_efficiency.png" width="700"/>
</p>

- ~80% of net value comes from ~40% of accounts.
- Enables aggressive budget cuts without proportional value loss.

---

### 4️⃣ Uplift Distribution — Guardrails Are Working
<p align="center">
  <img src="images/04_uplift_distribution.png" width="700"/>
</p>

- Targeted accounts skew strongly positive uplift.
- Suppressed accounts cluster near zero or negative uplift.
- Validation does **not** rely on hidden ground truth.

---

### 5️⃣ Failure Mode Audit — How the System Fails
<p align="center">
  <img src="images/05_failure_matrix.png" width="700"/>
</p>

- **0% of Sleeping Dogs** are targeted.
- Errors bias toward **under-targeting**, not harmful over-targeting.

---

## 🛡️ Policy Design

### Insight → Rule Mapping

**Insight: Prediction ≠ Decision**
- High conversion likelihood does not imply positive intervention impact.  
**Policy**: Rank by **uplift (incremental impact)**, not propensity.

**Insight: Risk Is Non-Linear**
- High-activity users can be harmed by nudges.  
**Policy**: Suppress any account with **admin-level negative uplift**.

**Insight: Accounts Are the Economic Unit**
- User-level wins can destroy account-level value.  
**Policy**: Aggregate uplift → **expected net value at account level**.

**Insight: Value Is Front-Loaded**
- Most value comes from a minority of accounts.  
**Policy**: Support phased rollout using **budget efficiency curves**.

---

## 🧪 Modeling & Validation

**The Confounding Problem**
- High-activity users were **more likely to be treated**.
- High-activity users were **more likely to convert anyway**.
- A naive model would overstate treatment impact.

**How This Was Addressed**
- Treatment bias explicitly injected during data generation.
- Uplift modeling used to isolate **incremental effect**, not correlation.
- Validation focused on:
  - Treatment neutrality
  - Directional alignment
  - Failure-mode bias (false positives vs false negatives)

**Why Accuracy Metrics Were Deprioritized**
- AUC measures prediction quality.
- This system is evaluated on **decision quality and safety**.

---

## 🧬 Data Generation & Ground Truth

- Synthetic B2B SaaS data engineered to replicate:
  - Heavy-tailed activity
  - Selection bias in treatment
  - Non-linear treatment effects
- Latent uplift groups used **only for post-hoc audit**, never training.

---

## 📂 Repository Structure

```text
├── data/
│   ├── documentation/
│   ├── raw/
│   ├── processed/
│   └── features/
├── images/
├── results/
└── src/
    ├── 01_data_generation/
    ├── 02_data_cleaning/
    ├── 03_feature_engineering/
    ├── 04_modeling/
    ├── 05_policy/
    └── 06_visualization/
```

---

## ⚠️ Limitations

- Synthetic environment designed for decision realism, not statistical benchmarking  
- Static policy (no online learning or adaptive feedback loop)  
- No long-term churn or downstream revenue attribution modeled  

These constraints are intentional to keep the project focused on **decision design**, not platform engineering.

---

## 🔮 What I’d Do Next in Production

- Introduce **LTV-weighted uplift** instead of flat value per activation  
- Add **online policy learning** with delayed outcome feedback  
- Extend from single-treatment to **multi-treatment optimization**  
- Integrate with experimentation platforms for controlled rollout  

---

## 🛠️ Tech Stack

Python · pandas · scikit-learn · matplotlib · Git

---

## 📣 Call to Action

This project reflects how I approach **Product Analytics and Decision Science** problems where the goal is not better models, but **better decisions under risk**.
