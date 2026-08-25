"""
SkyGuard AI - Genuine SHAP Explainability Analysis (Offline)
Computes REAL SHAP (SHapley Additive exPlanations) values for the multivariate
Isolation Forest anomaly detector, using the `shap` library against real NOAA
historical background data (see data/real_stations/).

Why this is a separate, offline script rather than part of the live pipeline:
the per-packet explanation shown in the Streamlit UI and returned by the API
(backend/app/xai/explainer.py) is a fast hand-rolled additive heuristic, NOT
SHAP, despite earlier documentation calling it that -- see README.md and
docs/ARCHITECTURE.md for the corrected wording. A real SHAP explainer
(Kernel/Permutation) needs many model evaluations per explained point, which
would blow the pipeline's <10ms real-time latency budget if run per-packet.
Genuine SHAP is computed HERE instead, offline, as model-level explainability
evidence -- exactly the kind of artifact "Explainable AI (SHAP/LIME)" in the
problem statement is asking for, without pretending the live per-packet path
is doing something it isn't.

Run:
    python benchmark/run_shap_analysis.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import shap

from backend.app.models.isolation_forest import multivariate_detector

FEATURE_NAMES = [
    "temperature", "pressure", "humidity",
    "delta_temp", "delta_pres", "delta_hum",
    "vpd", "dew_point_depression"
]


def build_test_points():
    """
    A handful of illustrative points to explain: several real historical
    observations (should score as normal) plus a few synthetic anomalous
    signatures (should score as outliers), so the SHAP report shows
    contrastive attributions for both regimes.
    """
    real_features = multivariate_detector._load_real_features()
    rng = np.random.RandomState(7)
    real_samples = real_features[rng.choice(len(real_features), size=10, replace=False)] \
        if real_features is not None else np.empty((0, 8))

    synthetic_anomalies = np.array([
        # temp, pressure, humidity, d_temp, d_pres, d_hum, vpd, dew_point_depression
        [45.0, 1012.0, 30.0, 20.0, 0.5, 5.0, 30.0, 20.0],   # sensor spike
        [25.0, 1013.0, 60.0, 0.1, 0.1, 0.1, 12.0, 8.0],      # (near-)normal
        [10.0, 950.0, 95.0, 0.2, 3.0, 1.0, 0.5, 0.5],        # rapid pressure drop
        [54.5, 1013.0, 96.0, 25.0, 0.0, 30.0, 42.0, 25.0],   # physics-violation extreme
    ], dtype=np.float64)

    labels = [f"real_sample_{i}" for i in range(len(real_samples))] + [
        "synthetic_sensor_spike", "synthetic_near_normal",
        "synthetic_pressure_drop_event", "synthetic_physics_violation"
    ]
    X = np.vstack([real_samples, synthetic_anomalies]) if len(real_samples) else synthetic_anomalies
    return X, labels


def predict_fn(X):
    X_scaled = multivariate_detector.scaler.transform(X)
    # Negate so higher output = more anomalous (SHAP conventions read more naturally
    # as "this feature pushed the anomaly score up", matching the rest of the pipeline).
    return -multivariate_detector.model.decision_function(X_scaled)


def main():
    print("=" * 70)
    print("🔍 SKYGUARD AI — GENUINE SHAP EXPLAINABILITY ANALYSIS")
    print("=" * 70)

    if multivariate_detector.real_data_samples == 0:
        print("\n[WARN] No real background data loaded (data/real_stations/processed/ empty).")
        print("Run data/real_stations/fetch_and_process.py first for a grounded background set.")

    real_features = multivariate_detector._load_real_features()
    if real_features is None:
        print("[ERROR] Cannot build a background set without real data. Aborting.")
        return

    rng = np.random.RandomState(42)
    background_idx = rng.choice(len(real_features), size=min(100, len(real_features)), replace=False)
    background = shap.kmeans(real_features[background_idx], 20)

    X_explain, labels = build_test_points()

    print(f"\nBackground: {len(real_features[background_idx])} real observations -> 20 kmeans centroids")
    print(f"Explaining {len(X_explain)} points ({len(labels)} labeled)...")

    t0 = time.time()
    explainer = shap.KernelExplainer(predict_fn, background)
    shap_values = explainer.shap_values(X_explain, nsamples=200, silent=True)
    elapsed = time.time() - t0
    print(f"SHAP computation took {elapsed:.1f}s for {len(X_explain)} points "
          f"(this is why it runs offline, not per-packet)")

    mean_abs_importance = np.mean(np.abs(shap_values), axis=0)
    order = np.argsort(-mean_abs_importance)

    print("\nGlobal Feature Importance (mean |SHAP value|):")
    lines = [
        "# SkyGuard AI — Genuine SHAP Explainability Report",
        "",
        f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Explainer**: `shap.KernelExplainer` over the Isolation Forest's `decision_function`",
        f"**Background**: {len(real_features[background_idx])} real NOAA ISD-Lite observations, "
        f"reduced to 20 kmeans centroids",
        f"**Points explained**: {len(X_explain)}",
        "",
        "This is a REAL, computed SHAP analysis -- distinct from the fast additive-heuristic "
        "attribution shown live in the UI/API (backend/app/xai/explainer.py), which is not SHAP "
        "despite what earlier documentation called it. See this script's module docstring for why "
        "genuine SHAP runs offline rather than per-packet.",
        "",
        "## Global Feature Importance (mean |SHAP value| across explained points)",
        "",
        "| Rank | Feature | Mean \\|SHAP value\\| |",
        "| :--- | :--- | :--- |",
    ]
    for rank, i in enumerate(order, start=1):
        print(f"  {rank}. {FEATURE_NAMES[i]:<22} {mean_abs_importance[i]:.4f}")
        lines.append(f"| {rank} | {FEATURE_NAMES[i]} | {mean_abs_importance[i]:.4f} |")

    lines.append("")
    lines.append("## Per-Point SHAP Attributions")
    lines.append("")
    lines.append("| Point | " + " | ".join(FEATURE_NAMES) + " |")
    lines.append("| :--- | " + " | ".join(["---"] * len(FEATURE_NAMES)) + " |")
    for label, row in zip(labels, shap_values):
        lines.append(f"| {label} | " + " | ".join(f"{v:+.3f}" for v in row) + " |")

    out_path = Path(__file__).resolve().parent / "shap_analysis_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ SHAP report generated at {out_path.relative_to(Path(__file__).resolve().parent.parent)}\n")


if __name__ == "__main__":
    main()
