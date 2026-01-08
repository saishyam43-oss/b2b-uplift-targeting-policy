# Cleaning Decisions — Explicit Non-Actions

## Outcomes
- Missing outcomes were NOT imputed
- Rows with missing outcomes were NOT dropped
- Outcome values were never used for cleaning decisions

## Activity Logs
- Activity was NOT forward-filled
- Missing days were NOT inferred
- Spikes were capped, not removed

## Treatment Assignment
- Treatment/control balance was NOT altered
- Confounding was NOT corrected during cleaning

## User Population
- No users were dropped as outliers
- No filtering was based on conversion outcomes

## Latent Truth
- Latent uplift groups were NOT used
- No validation or cleaning referenced hidden truth
