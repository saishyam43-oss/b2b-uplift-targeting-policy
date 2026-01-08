# Synthetic Data Generation Report

## 1. Loading Data...
✅ All files loaded successfully.

## 2. Shape & Integrity Checks
* **Accounts:** 2500
* **Users:** 28607
* **Activity Rows:** 444333
* **Interventions:** 12610
* **Outcomes:** 12610
* **Uniqueness:** User IDs are unique.

## 3. Causal Logic Validation
✅ PASS: No ineligible users were treated.
✅ PASS: All activity strictly precedes intervention.
✅ PASS: All activations strictly follow interventions.

## 4. Eligibility Sanity Checks
* **Total Users:** 28607
* **Eligible Users:** 12610
* **Population Eligibility Rate:** 44.08%
✅ PASS: Low-activity users are mostly excluded.
✅ PASS: Eligibility concentrates in mid-activity band.
✅ PASS: High-diversity users are mostly excluded.

## 5. Hidden Uplift Physics Check

| latent_uplift_group   |   Control Rate |   Treatment Rate |   Observed Lift |
|:----------------------|---------------:|-----------------:|----------------:|
| lost_cause            |          0.050 |            0.075 |           0.025 |
| persuadable           |          0.090 |            0.522 |           0.432 |
| sleeping_dog          |          0.461 |            0.134 |          -0.328 |
| sure_thing            |          0.602 |            0.667 |           0.065 |
✅ PASS: Hidden uplift physics validated.

## 6. Global Statistics
* **Treated Activation Rate:** 29.77%
* **Control Activation Rate:** 16.43%
* **Global ATE:** 13.34%

✅ Validation Complete.
