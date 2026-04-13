import numpy as np
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from constants import FEATURE_COLS
from feature_engineering import engineer_single_row


def predict_patient(inputs: dict, art: dict):
    """Run inference on one patient dict. Returns (prob, shap_row, X_df)."""
    row = engineer_single_row(inputs)

    for c, le in art["le_map"].items():
        v = row.get(c, le.classes_[0])
        if v not in le.classes_:
            v = le.classes_[0]
        row[c+"_enc"] = int(le.transform([v])[0])

    X        = pd.DataFrame([{f: row.get(f, 0) for f in FEATURE_COLS}]).astype(float)
    prob     = float(art["model"].predict_proba(X)[0, 1])
    explainer = art.get("explainer")
    if explainer is not None:
        shap_row = explainer.shap_values(X)[0]
    else:
        booster = art["model"].get_booster()
        dmatrix = xgb.DMatrix(X, feature_names=list(X.columns))
        shap_row = booster.predict(dmatrix, pred_contribs=True)[0][:-1]
    return prob, shap_row, X


def shap_waterfall_fig(shap_row, n=12):
    """Return a matplotlib Figure of the SHAP waterfall bar chart."""
    top_idx = np.argsort(np.abs(shap_row))[::-1][:n]
    feats   = [FEATURE_COLS[i] for i in top_idx]
    vals    = [shap_row[i]     for i in top_idx]
    colors  = ["#e74c3c" if v > 0 else "#27ae60" for v in vals]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(feats[::-1], vals[::-1], color=colors[::-1], height=0.55)
    ax.axvline(0, color="black", lw=0.8, ls="--")

    for bar, v in zip(bars, vals[::-1]):
        ax.text(
            v + (0.002 if v >= 0 else -0.002),
            bar.get_y() + bar.get_height() / 2,
            f"{v:+.3f}", va="center",
            ha="left" if v >= 0 else "right",
            fontsize=8, color="#333",
        )

    ax.set_xlabel("SHAP value  (impact on log-odds of HIGH risk)")
    ax.set_title("Feature Contributions — SHAP Waterfall")
    ax.spines[["top", "right"]].set_visible(False)
    red_p   = mpatches.Patch(color="#e74c3c", label="↑ Increases risk")
    green_p = mpatches.Patch(color="#27ae60", label="↓ Decreases risk")
    ax.legend(handles=[red_p, green_p], fontsize=9)
    plt.tight_layout()
    return fig


def shap_global_importance_fig(shap_vals):
    """Bar chart of mean absolute SHAP values across all features."""
    mean_abs = np.abs(shap_vals).mean(axis=0)
    order    = np.argsort(mean_abs)[::-1]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(
        [FEATURE_COLS[i] for i in order[::-1]],
        [mean_abs[i]      for i in order[::-1]],
        color="#2e86de",
    )
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Global Feature Importance")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig, order


def shap_beeswarm_fig(shap_vals, X_te, order, n_top=10):
    """Beeswarm scatter for top-N features across 500 test patients."""
    top_idx = order[:n_top]
    fig, ax = plt.subplots(figsize=(6, 5))
    np.random.seed(0)

    for rank, fi in enumerate(top_idx[::-1]):
        sv_col = shap_vals[:500, fi]
        fv     = X_te.iloc[:500, fi].values
        fv_n   = (fv - fv.min()) / (np.ptp(fv) + 1e-9)
        jitter = np.random.uniform(-0.3, 0.3, len(sv_col))
        ax.scatter(sv_col, np.full_like(sv_col, rank) + jitter,
                   c=fv_n, cmap="RdBu_r", alpha=0.4, s=7)

    ax.set_yticks(range(n_top))
    ax.set_yticklabels([FEATURE_COLS[i] for i in top_idx[::-1]])
    ax.axvline(0, color="black", lw=0.8, ls="--")
    ax.set_xlabel("SHAP value")
    ax.set_title(f"Beeswarm — Top {n_top} Features")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig


def shap_heatmap_fig(shap_vals, order, n=10, n_patients=200):
    """Heatmap of SHAP values: top-N features × n_patients."""
    import matplotlib.colors as mcolors
    import pandas as pd

    top_n   = order[:n]
    hm_data = pd.DataFrame(
        shap_vals[:n_patients][:, top_n],
        columns=[FEATURE_COLS[i] for i in top_n],
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(
        hm_data.T.values, aspect="auto", cmap="RdBu_r",
        norm=mcolors.TwoSlopeNorm(vcenter=0),
    )
    ax.set_yticks(range(n))
    ax.set_yticklabels(hm_data.columns)
    ax.set_xlabel("Patient index (test set)")
    ax.set_title("SHAP Heatmap")
    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    return fig
