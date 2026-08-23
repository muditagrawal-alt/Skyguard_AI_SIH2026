"""
SkyGuard AI - Quantitative Benchmark & Evaluation Suite
Evaluates Detection Precision, Recall, F1-Score, Zero-False-Alarm Convective Weather Check,
Inference Latency, and Imputation RMSE across all test categories.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import random
import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

from backend.app.core.config import config
from backend.app.core.data_generator import VirtualAWSNetworkSimulator, AnomalyInjectionRequest
from backend.app.core.pipeline import SkyGuardPipeline

DEFAULT_SEED = 42


def run_comprehensive_benchmark(seed: int = DEFAULT_SEED):
    # The simulator's diurnal noise and anomaly pulses use the unseeded global `random`
    # module, so without pinning a seed here every benchmark run produces different
    # KPI numbers -- making the README's reported table impossible to reproduce or audit.
    random.seed(seed)
    np.random.seed(seed)

    print("=" * 70)
    print("🚀 RUNNING SKYGUARD AI COMPREHENSIVE BENCHMARK EVALUATION")
    print(f"   (seed={seed}, deterministic and reproducible)")
    print("=" * 70)

    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()
    station_id = "AWS_ALPHA_MOUNTAIN"

    # Category Test Configuration
    test_cases = [
        {"name": "Clean Normal Diurnal Baseline", "type": None, "steps": 250, "is_anomaly": 0},
        {"name": "Injected Temperature Spikes", "type": "spike", "sensor": "temperature", "intensity": 1.2, "steps": 60, "is_anomaly": 1},
        {"name": "Injected Sensor Flatlines", "type": "flatline", "sensor": "temperature", "intensity": 1.0, "steps": 60, "is_anomaly": 1},
        {"name": "Injected Calibration Drift", "type": "drift", "sensor": "temperature", "intensity": 1.0, "steps": 60, "is_anomaly": 1},
        {"name": "Injected Thermodynamic Violations", "type": "physics_violation", "sensor": "all", "intensity": 1.0, "steps": 60, "is_anomaly": 1},
        {"name": "Injected Telemetry Packet Loss", "type": "packet_loss", "sensor": "all", "intensity": 1.0, "steps": 40, "is_anomaly": 1},
        {"name": "Severe Thunderstorm (0% False Alarm Test)", "type": "thunderstorm", "sensor": "all", "intensity": 1.0, "steps": 80, "is_anomaly": 0}
    ]

    y_true_all = []
    y_pred_all = []
    latencies_ms = []
    imputation_errors_temp = []
    category_results = []
    storm_false_alarms = 0
    storm_total_steps = 0

    for tc in test_cases:
        c_name = tc["name"]
        c_type = tc["type"]
        steps = tc["steps"]
        expected_label = tc["is_anomaly"]
        print(f"Testing: {c_name} ({steps} steps)...")

        # Re-instantiate clean test environment for isolated metric evaluation
        test_sim = VirtualAWSNetworkSimulator()
        test_pipe = SkyGuardPipeline()

        # Warm up pipeline buffer with 20 baseline steps
        for _ in range(20):
            w_raw = test_sim.generate_next_reading(station_id, dt_seconds=1.0)
            test_pipe.process_reading(w_raw, dt_seconds=1.0)

        # Inject anomaly if specified
        if c_type is not None:
            test_sim.inject_anomaly(AnomalyInjectionRequest(
                station_id=station_id,
                anomaly_type=c_type,
                sensor=tc.get("sensor", "temperature"),
                intensity=tc.get("intensity", 1.0),
                duration_steps=steps
            ))

        y_true_cat = []
        y_pred_cat = []

        for step_i in range(steps):
            t0 = time.perf_counter()
            raw = test_sim.generate_next_reading(station_id, dt_seconds=1.0)
            res = test_pipe.process_reading(raw, dt_seconds=1.0)
            lat = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(lat)

            # System flags as hardware/data fault (excluding genuine natural extreme weather)
            is_fault_flagged = res["ensemble"]["is_anomaly"] and not res["root_cause"]["is_genuine_weather"]

            pred_bin = 1 if is_fault_flagged else 0

            # "spike" is a pulsed injection (~1/3 of steps actually perturbed -- see
            # VirtualAWSNetworkSimulator._apply_injections). Labeling every step in the
            # window as ground-truth-anomaly regardless would score correctly-rejected
            # clean readings as missed detections. Use the generator's own record of
            # which steps it actually perturbed instead of a blanket window label.
            if c_type == "spike":
                step_label = 1 if "spike" in raw.get("injected_anomalies_effective", []) else 0
            else:
                step_label = expected_label

            y_true_cat.append(step_label)
            y_pred_cat.append(pred_bin)
            y_true_all.append(step_label)
            y_pred_all.append(pred_bin)

            # Imputation error measurement during fault injection
            if step_label == 1:
                clean_t = raw["clean_ground_truth"]["temperature"]
                imp_t = res["imputed"]["temperature"]
                if clean_t is not None and imp_t is not None:
                    imputation_errors_temp.append(abs(clean_t - imp_t))

            # Thunderstorm False Alarm Tracking
            if c_type == "thunderstorm":
                storm_total_steps += 1
                if is_fault_flagged:
                    storm_false_alarms += 1

        # Category Metrics
        cat_acc = np.mean(np.array(y_true_cat) == np.array(y_pred_cat)) * 100.0
        category_results.append({
            "Category": c_name,
            "Steps": steps,
            "Expected": "Anomaly (1)" if expected_label == 1 else "Normal/Weather (0)",
            "Accuracy": f"{cat_acc:.1f}%"
        })

    # Global KPI Calculations
    precision = precision_score(y_true_all, y_pred_all, zero_division=0)
    recall = recall_score(y_true_all, y_pred_all, zero_division=0)
    f1 = f1_score(y_true_all, y_pred_all, zero_division=0)
    avg_latency = np.mean(latencies_ms)
    p95_latency = np.percentile(latencies_ms, 95)
    mean_imputation_mae = np.mean(imputation_errors_temp) if imputation_errors_temp else 0.0
    storm_far = (storm_false_alarms / max(1, storm_total_steps)) * 100.0

    print("\n" + "=" * 70)
    print("📊 SKYGUARD AI BENCHMARK RESULTS")
    print("=" * 70)
    print(f"• Total Evaluated Observations: {len(y_true_all)}")
    print(f"• Overall Detection Precision:  {precision * 100:.2f}%")
    print(f"• Overall Detection Recall:     {recall * 100:.2f}%")
    print(f"• Overall Anomaly F1-Score:     {f1 * 100:.2f}%")
    print(f"• Genuine Storm False Alarm:    {storm_far:.2f}% (Target: 0.00%)")
    print(f"• Average Inference Latency:    {avg_latency:.3f} ms / reading")
    print(f"• 95th Percentile Latency:      {p95_latency:.3f} ms / reading")
    print(f"• Self-Healing Imputation MAE:  {mean_imputation_mae:.2f} °C")
    print("=" * 70)

    # Category Table
    cat_df = pd.DataFrame(category_results)
    print("\n📋 Category-by-Category Performance Breakdown:")
    print(cat_df.to_string(index=False))

    # Generate Markdown Report
    report_content = f"""# SkyGuard AI — Quantitative Benchmark Evaluation Report

**Evaluation Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Random Seed**: {seed} (deterministic -- re-run with `--seed {seed}` to reproduce exactly)
**Total Processed Observations**: {len(y_true_all)}
**Architecture**: Physics-Informed ML Ensemble (Magnus-Tetens + Autoencoder + Isolation Forest + CUSUM + Welford)

---

## 1. Key Performance Indicators (KPIs)

| Metric | Measured Value | Operational Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Detection Precision** | **{precision * 100:.2f}%** | > 90.0% | {'✅ PASS' if precision >= 0.90 else '⚠️ REVIEW'} |
| **Detection Recall** | **{recall * 100:.2f}%** | > 90.0% | {'✅ PASS' if recall >= 0.90 else '⚠️ REVIEW'} |
| **Overall F1-Score** | **{f1 * 100:.2f}%** | > 92.0% | {'✅ PASS' if f1 >= 0.92 else '⚠️ REVIEW'} |
| **False Alarm Rate on Storms** | **{storm_far:.2f}%** | < 2.0% | {'✅ PASS' if storm_far <= 2.0 else '⚠️ REVIEW'} |
| **Mean Inference Latency** | **{avg_latency:.3f} ms** | < 5.0 ms | {'✅ PASS' if avg_latency <= 5.0 else '⚠️ REVIEW'} |
| **95th Percentile Latency** | **{p95_latency:.3f} ms** | < 10.0 ms | {'✅ PASS' if p95_latency <= 10.0 else '⚠️ REVIEW'} |
| **Self-Healing Imputation MAE** | **{mean_imputation_mae:.2f} °C** | < 1.0 °C | {'✅ PASS' if mean_imputation_mae <= 1.0 else '⚠️ REVIEW'} |

---

## 2. Category-by-Category Performance

{cat_df.to_markdown(index=False)}

---

## 3. Key Findings

1. **Thunderstorm False Alarm Rate**: {storm_far:.2f}% of steps during a genuine, gradually-intensifying convective storm were misclassified as a sensor fault ({'meets' if storm_far <= 2.0 else 'does NOT yet meet'} the < 2.0% target). Root cause: the CUSUM drift detector cannot distinguish "the sensor is drifting" from "the weather is genuinely trending" from a single station's own time series alone during the slow ramp-in of an event, before the root-cause classifier's genuine-weather gate ($RH > 78\\%$ or a confirmed cooling trend) is satisfied. See the cross-station spatial consistency check for the mitigation.
2. **Sub-millisecond Real-Time Processing**: Pipeline latency of **{avg_latency:.2f} ms** satisfies high-throughput edge and central gateway streaming constraints.
3. **Continuous Data Continuity**: Self-healing imputer delivers physically valid reconstructions with an average error of only **{mean_imputation_mae:.2f} °C**.
4. **Reproducibility**: This run used a fixed random seed ({seed}); results are deterministic and will reproduce exactly on re-run rather than varying between executions.
"""

    with open("benchmark/evaluation_report.md", "w") as f:
        f.write(report_content)

    print("\n✅ Benchmark evaluation report generated at benchmark/evaluation_report.md\n")
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "storm_far": storm_far,
        "avg_latency_ms": avg_latency,
        "imputation_mae": mean_imputation_mae
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SkyGuard AI benchmark evaluation")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducible results")
    args = parser.parse_args()
    run_comprehensive_benchmark(seed=args.seed)
