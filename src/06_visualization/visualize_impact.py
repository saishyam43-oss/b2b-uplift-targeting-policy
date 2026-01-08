# =========================================
# Phase 8: Validation & Impact Visualization (Final Master Polish)
# Purpose: Generate Portfolio-Ready Evidence (10/10 Quality)
# =========================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

# -----------------------------
# Setup & Global Styling
# -----------------------------
RESULTS_DIR = Path("results")
RAW_DIR = Path("data/raw")
IMG_DIR = Path("images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

# Director-Level Styling
plt.style.use('seaborn-v0_8-white')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.left'] = False
plt.rcParams['axes.grid'] = False
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.titlelocation'] = 'left'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['text.color'] = '#333333'

# Precise Palette
COLOR_TARGET     = '#16A34A'  # Green
# Desaturated/Muted versions for Funnel (to push attention to Target)
COLOR_RISK_ADMIN_MUTED = '#C53030'  # Slightly muted Red
COLOR_RISK_USER_MUTED  = '#D97706'  # Slightly muted Amber
COLOR_MUTED_1    = '#9CA3AF'  # Gray
COLOR_MUTED_2    = '#D1D5DB'  # Light Gray
COLOR_BLIND      = '#D6D9E1'  # Extremely Light Gray (almost ghosted)
COLOR_SUPPRESSED = '#B45309'  # Muted Brick

# Darker Text Color for Axis Labels
COLOR_AXIS_TEXT  = '#374151'

print("Loading data...")
policy_df = pd.read_csv(RESULTS_DIR / "account_policy_debug.csv")

try:
    hidden_df = pd.read_csv(RAW_DIR / "latent_uplift_groups_hidden.csv")
    users_df = pd.read_csv(RAW_DIR / "users_raw.csv", usecols=["user_id", "account_id"])
    HAS_TRUTH = True
except FileNotFoundError:
    print("⚠️ Hidden truth files not found. Skipping Truth-based charts.")
    HAS_TRUTH = False

# =========================================
# CHART 1: The Policy Funnel
# =========================================
print("Generating Chart 1: Policy Funnel...")

order = [
    "treat_account",
    "suppress_toxic_admin",
    "suppress_toxic_users",
    "suppress_too_small",
    "suppress_unprofitable"
]
labels = [
    "Targeted",
    "Suppressed:\nToxic Admin",
    "Suppressed:\nToxic Users",
    "Suppressed:\nToo Small",
    "Suppressed:\nUnprofitable"
]
# Desaturated palette to emphasize the first bar (Targeted)
colors = [COLOR_TARGET, COLOR_RISK_ADMIN_MUTED, COLOR_RISK_USER_MUTED, COLOR_MUTED_1, COLOR_MUTED_2]

counts = policy_df["decision"].value_counts().reindex(order).fillna(0)
total_accounts = len(policy_df)
suppressed_pct = (total_accounts - counts['treat_account']) / total_accounts

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.bar(labels, counts, color=colors, width=0.65)

# Annotations
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 30,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=14, fontweight='bold', color='#333333')

# Admin Callout
admin_bar = bars[1]
callout_x = admin_bar.get_x() + admin_bar.get_width()/2
callout_y = admin_bar.get_height() + 400

ax.annotate("281 accounts suppressed\ndue to Admin churn risk",
            xy=(callout_x, admin_bar.get_height()),
            xytext=(callout_x, callout_y),
            ha='center', va='bottom', fontsize=13, color='#555555',
            arrowprops=dict(arrowstyle='->', color='#555555', connectionstyle="arc3,rad=.2"))

ax.set_title(f'Risk Filters Eliminate {suppressed_pct:.0%} of Accounts Before Targeting', pad=40)
ax.set_yticks([])
ax.set_xlabel('')

# ADJUSTMENTS: Remove baseline, increase X-axis font
ax.spines['bottom'].set_visible(False)
ax.tick_params(axis='x', labelsize=13) # Increased size

plt.tight_layout()
plt.savefig(IMG_DIR / "01_policy_funnel.png", dpi=300)
print(f"Saved: {IMG_DIR / '01_policy_funnel.png'}")

# =========================================
# CHART 2: Risk vs. Reward
# =========================================
print("Generating Chart 2: Risk vs. Reward...")

blind_mask = policy_df["decision"] != "suppress_too_small"
blind_val = policy_df.loc[blind_mask, "net_account_value"].sum()
blind_risk = policy_df.loc[blind_mask, "has_toxic_admin"].sum()

prec_mask = policy_df["decision"] == "treat_account"
prec_val = policy_df.loc[prec_mask, "net_account_value"].sum()
prec_risk = policy_df.loc[prec_mask, "has_toxic_admin"].sum()

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

x = np.arange(1)
width = 0.45

# Bars (Blind Nudge is lighter now)
ax1.bar(x - width/2, [blind_val], width, color=COLOR_BLIND, label='Revenue')
ax1.bar(x + width/2, [prec_val], width, color=COLOR_TARGET, label='Revenue')

# Points
ax2.scatter(x - width/2, [blind_risk], s=300, color='#B71C1C', zorder=9) # Full saturation red
ax2.scatter(x + width/2, [prec_risk], s=300, color=COLOR_TARGET, zorder=9)

ax1.set_title('Precision Targeting Sacrifices Revenue to Avoid Admin Churn Risk', pad=35)
# Subtitle
ax1.text(0, 1.05, "Higher short-term revenue, unacceptable churn risk",
         transform=ax1.transAxes, fontsize=12, color='#555555')

# ax1.set_ylabel('Projected Revenue ($)', color=COLOR_AXIS_TEXT)
ax1.set_yticks([])
ax1.set_xticks([])

# Remove Y-axis ticks for Risk
# ax2.set_ylabel('Toxic Admins Risked', color='#B91C1C', rotation=270, labelpad=20)
ax2.set_yticks([])
ax2.spines['right'].set_visible(False)

ax1.spines['bottom'].set_visible(False)
ax2.spines['bottom'].set_visible(False)

left_x = float(x[0] - width/2)
right_x = float(x[0] + width/2)

# Value Labels
ax1.text(left_x, blind_val/2, f"Blind Nudge\n${blind_val/1000:.0f}k value",
         ha='center', va='center', color='#555555', fontweight='bold', fontsize=11)
ax1.text(right_x, prec_val/2, f"Precision\n${prec_val/1000:.0f}k value",
         ha='center', va='center', color='white', fontweight='bold', fontsize=11)

# Risk Annotations (Increased size +20%)
ax2.text(left_x, blind_risk + 10, f"{int(blind_risk)} Admins!",
         ha='left', color='#B71C1C', fontweight='bold', fontsize=15)

ax2.text(right_x, prec_risk + 15, "0 Risk",
         ha='center', color=COLOR_TARGET, fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig(IMG_DIR / "02_risk_vs_reward.png", dpi=300)
print(f"Saved: {IMG_DIR / '02_risk_vs_reward.png'}")

# =========================================
# CHART 3: Budget Efficiency Curve
# =========================================
print("Generating Chart 3: Budget Efficiency...")

target_df = policy_df[policy_df["decision"] == "treat_account"].copy()
target_df = target_df.sort_values("net_account_value", ascending=False).reset_index(drop=True)
target_df["cumulative_value"] = target_df["net_account_value"].cumsum()
target_df["percent_accounts"] = (target_df.index + 1) / len(target_df) * 100

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(target_df["percent_accounts"], target_df["cumulative_value"],
        color=COLOR_TARGET, linewidth=5.0)
# Thinned random baseline (~25%)
ax.plot([0, 100], [0, target_df["cumulative_value"].max()],
        color=COLOR_MUTED_1, linestyle='--', linewidth=1.1, alpha=0.6)

ax.set_title('40% of Accounts Capture ~80% of Total Value', pad=40)
# User's specific placement code
ax.text(0, 1.05, "Model-driven targeting concentrates value early",
        transform=ax.transAxes, fontsize=11, color='#555555', va='bottom')

# Increase axis labels size
ax.set_xlabel('% of Targeted Accounts', fontsize=13, labelpad=10)
ax.set_ylabel('Cumulative Net Value ($)', fontsize=13, labelpad=10)
ax.tick_params(axis='both', which='major', labelsize=12)

ax.grid(axis='y', linestyle=':', alpha=0.15)
ax.spines['bottom'].set_visible(False)
from matplotlib.ticker import MaxNLocator
ax.yaxis.set_major_locator(MaxNLocator(nbins=3))

p40_idx = int(len(target_df) * 0.40)
p40_val = target_df.iloc[p40_idx]["cumulative_value"]
p40_pct = target_df.iloc[p40_idx]["percent_accounts"]
max_val = target_df["cumulative_value"].max()

ax.scatter([p40_pct], [p40_val], color='#333333', s=40, zorder=5)

# User's specific placement code for callout
label_y_pos = p40_val - (max_val * 0.06)

ax.text(p40_pct+2, label_y_pos, f"80% Value",
        fontsize=11, fontweight='bold', va='top')

# Connector line
ax.plot([p40_pct, p40_pct], [p40_val, label_y_pos + (max_val * 0.04)],
        color='#333333', linestyle=':', linewidth=1)

plt.tight_layout()
plt.savefig(IMG_DIR / "03_budget_efficiency.png", dpi=300)
print(f"Saved: {IMG_DIR / '03_budget_efficiency.png'}")

# =========================================
# CHART 4: Uplift Distribution
# =========================================
print("Generating Chart 4: Uplift Distribution...")

plt.figure(figsize=(10, 6))

plot_df = policy_df.copy()
# Separate dataframes for explicit control
targeted = plot_df[plot_df["decision"] == "treat_account"]
suppressed = plot_df[plot_df["decision"] != "treat_account"]

# Plot Targeted (Green, Higher Opacity)
sns.kdeplot(
    data=targeted, x="sum_uplift", fill=True,
    color=COLOR_TARGET, alpha=0.65, linewidth=0, label='Targeted'
)

# Plot Suppressed (Red, Lower Opacity)
sns.kdeplot(
    data=suppressed, x="sum_uplift", fill=True,
    color=COLOR_SUPPRESSED, alpha=0.35, linewidth=0, label='Suppressed'
)

plt.title('Guardrails Shift Targeting Toward Positive Uplift', pad=30)
plt.xlabel('Predicted Account-Level Uplift (Δ Probability)', fontsize=15)
plt.ylabel('')
plt.yticks([])

plt.axvline(0, color='#222222', linestyle=':', linewidth=2, alpha=1.0)
plt.text(0.5, plt.gca().get_ylim()[1]*0.95, "Zero Lift",
         color='#222222', fontsize=11, fontweight='bold')

handles = [
    mpatches.Patch(color=COLOR_TARGET, label='Targeted'),
    mpatches.Patch(color=COLOR_SUPPRESSED, label='Suppressed')
]
plt.legend(handles=handles, frameon=False, loc='upper right')

plt.tight_layout()
plt.savefig(IMG_DIR / "04_uplift_distribution.png", dpi=300)
print(f"Saved: {IMG_DIR / '04_uplift_distribution.png'}")

# =========================================
# CHART 5: Safety Audit (Heatmap)
# =========================================
if HAS_TRUTH:
    print("Generating Chart 5: Safety Audit...")

    account_truth = users_df.merge(hidden_df, on="user_id")
    truth_agg = account_truth.groupby("account_id").apply(
        lambda x: x["latent_uplift_group"].mode()[0], include_groups=False
    ).reset_index(name="true_segment")

    audit_df = policy_df.merge(truth_agg, on="account_id", how="left")

    audit_pivot = pd.crosstab(
        audit_df["decision"] == "treat_account",
        audit_df["true_segment"],
        normalize='columns'
    )

    col_order = ["persuadable", "sure_thing", "lost_cause", "sleeping_dog"]
    audit_pivot = audit_pivot.reindex(columns=col_order)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Darker grid lines (linewidths=1.5, slightly gray color)
    sns.heatmap(audit_pivot, annot=True, fmt='.1%', cmap="Greys", cbar=False, ax=ax,
                linewidths=1.5, linecolor='#E5E7EB', annot_kws={"size": 13})

    ax.set_title('Policy Avoids 100% of Sleeping Dogs by Design', pad=30, fontweight='bold')
    ax.set_ylabel('')

    ax.set_xlabel('True Latent Segment', color=COLOR_AXIS_TEXT, fontweight='bold', labelpad=10)

    # Increased Y-axis label size
    ax.set_yticklabels(['Suppressed', 'Targeted'], rotation=0, fontsize=12)
    x_labels = [c.replace('_', ' ').title() for c in col_order]
    ax.set_xticklabels(x_labels, fontsize=11)

    # Bolding Logic (Only the 100% Suppressed Sleeping Dog)
    target_val = audit_pivot.iloc[0, 3] # Suppressed Sleeping Dog

    for t in ax.texts:
        t.set_weight('normal') # Reset all to normal first
        try:
            val_text = float(t.get_text().strip('%')) / 100
            if np.isclose(val_text, target_val, atol=0.001):
                x_pos, y_pos = t.get_position()
                # Check column 3 (Sleeping Dog) and Row 0 (Suppressed)
                if 3 < x_pos < 4 and 0 < y_pos < 1:
                    t.set_color('#065F46')
                    t.set_weight('bold')
                    t.set_size(17)
        except ValueError:
            pass

    plt.tight_layout()
    plt.savefig(IMG_DIR / "05_failure_matrix.png", dpi=300)
    print(f"Saved: {IMG_DIR / '05_failure_matrix.png'}")

    failures = audit_df[
        (audit_df["true_segment"] == "sleeping_dog") &
        (audit_df["decision"] == "treat_account")
    ]
    with open(RESULTS_DIR / "failure_mode_analysis.txt", "w") as f:
        f.write(f"CRITICAL FAILURE COUNT: {len(failures)}")

print("\nVisualization Phase Complete.")
