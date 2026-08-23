"""
SkyGuard AI - Real-Data Benchmark Evaluation
Replays genuine historical NOAA ISD-Lite observations (see data/real_stations/) as the
"clean" atmospheric background signal -- instead of the synthetic diurnal generator used
by benchmark/run_benchmark.py -- and injects the same controlled/labeled anomaly sandbox
on top. Real archives have no hand-labeled sensor-fault ground truth, so injected faults
remain the source of truth for detection scoring; but the un-injected stretches are 100%
real historical weather, which makes the false-positive measurement on those stretches a
genuine test against real atmospheric variability rather than the author's own synthetic
curve. This closes the "closed loop" problem where the generator, the detector's training
data, and the evaluator were all authored by the same process.

Run:
    python benchmark/run_real_data_benchmark.py
"""

import sys
import csv
import time
import random
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

from backend.app.core.data_generator import VirtualAWSNetworkSimulator, AnomalyInjectionRequest
from backend.app.core.pipeline import SkyGuardPipeline

REAL_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "real_stations" / "processed"
DEFAULT_SEED = 42
WARMUP_STEPS = 30
MAX_STEPS_PER_STATION = 1500

# Cycle through: a clean real-weather block (pure false-positive test against genuine
# historical variability), then a block of each injected fault type, repeating.
INJECTION_CYCLE = [
    {"type": None, "steps": 80},
    {"type": "spike", "sensor": "temperature", "intensity": 1.2, "steps": 20},
    {"type": None, "steps": 60},
    {"type": "flatline", "sensor": "temperature", "intensity": 1.0, "steps": 20},
    {"type": None, "steps": 60},
    {"type": "drift", "sensor": "temperature", "intensity": 1.0, "steps": 20},
    {"type": None, "steps": 60},
    {"type": "physics_violation", "sensor": "all", "intensity": 1.0, "steps": 15},
    {"type": None, "steps": 60},
    {"type": "packet_loss", "sensor": "all", "intensity": 1.0, "steps": 15},
    {"type": None, "steps": 80},
]


def load_station_csv(path: Path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_dt"] = datetime.fromisoformat(r["timestamp"])
    return rows


def run_real_data_benchmark(seed: int = DEFAULT_SEED):
    random.seed(seed)
    np.random.seed(seed)

    print("=" * 70)
    print("🌍 SKYGUARD AI — REAL HISTORICAL DATA BENCHMARK (NOAA ISD-Lite)")
    print(f"   (seed={seed}, deterministic and reproducible)")
    print("=" * 70)

    if not REAL_DATA_DIR.is_dir() or not any(REAL_DATA_DIR.glob("*.csv")):
        print(f"\n[ERROR] No real station data found at {REAL_DATA_DIR}.")
        print("Run: python data/real_stations/fetch_and_process.py")
        return None

    y_true_all, y_pred_all = [], []
    latencies_ms = []
    per_station_results = []

    for csv_path in sorted(REAL_DATA_DIR.glob("*.csv")):
        station_id = csv_path.stem
        rows = load_station_csv(csv_path)
        if len(rows) < WARMUP_STEPS + 50:
            print(f"[SKIP] {station_id}: only {len(rows)} real observations, too short")
            continue

        rows = rows[:WARMUP_STEPS + MAX_STEPS_PER_STATION]
        print(f"\nReplaying {station_id}: {len(rows)} real observations "
              f"({rows[0]['timestamp']} -> {rows[-1]['timestamp']})")

        sim = VirtualAWSNetworkSimulator()
        pipe = SkyGuardPipeline()

        # Warm up on clean real readings before any injection or scoring
        prev_dt = None
        for r in rows[:WARMUP_STEPS]:
            dt_seconds = (r["_dt"] - prev_dt).total_seconds() if prev_dt else 3600.0
            dt_seconds = max(60.0, dt_seconds)
            raw = sim.generate_next_reading_from_real(
                station_id, float(r["temperature_c"]), float(r["pressure_hpa"]),
                float(r["humidity_pct"]), r["timestamp"], dt_seconds=dt_seconds
            )
            pipe.process_reading(raw, dt_seconds=dt_seconds)
            prev_dt = r["_dt"]

        remaining = rows[WARMUP_STEPS:]
        y_true_station, y_pred_station = [], []
        false_positives_on_real_weather = 0
        clean_real_steps = 0
        cursor = 0
        cycle_i = 0

        while cursor < len(remaining):
            block = INJECTION_CYCLE[cycle_i % len(INJECTION_CYCLE)]
            cycle_i += 1
            block_steps = min(block["steps"], len(remaining) - cursor)
            if block_steps <= 0:
                break

            if block["type"] is not None:
                sim.inject_anomaly(AnomalyInjectionRequest(
                    station_id=station_id, anomaly_type=block["type"],
                    sensor=block.get("sensor", "temperature"),
                    intensity=block.get("intensity", 1.0), duration_steps=block_steps
                ))

            for _ in range(block_steps):
                r = remaining[cursor]
                dt_seconds = max(60.0, (r["_dt"] - prev_dt).total_seconds())
                t0 = time.perf_counter()
                raw = sim.generate_next_reading_from_real(
                    station_id, float(r["temperature_c"]), float(r["pressure_hpa"]),
                    float(r["humidity_pct"]), r["timestamp"], dt_seconds=dt_seconds
                )
                res = pipe.process_reading(raw, dt_seconds=dt_seconds)
                latencies_ms.append((time.perf_counter() - t0) * 1000.0)

                is_fault_flagged = res["ensemble"]["is_anomaly"] and not res["root_cause"]["is_genuine_weather"]
                pred_bin = 1 if is_fault_flagged else 0

                effective = raw.get("injected_anomalies_effective", [])
                true_bin = 1 if (block["type"] is not None and block["type"] in effective) else 0

                y_true_station.append(true_bin)
                y_pred_station.append(pred_bin)
                y_true_all.append(true_bin)
                y_pred_all.append(pred_bin)

                if true_bin == 0:
                    clean_real_steps += 1
                    if pred_bin == 1:
                        false_positives_on_real_weather += 1

                prev_dt = r["_dt"]
                cursor += 1

        acc = float(np.mean(np.array(y_true_station) == np.array(y_pred_station)) * 100.0)
        fp_rate = (false_positives_on_real_weather / max(1, clean_real_steps)) * 100.0
        per_station_results.append({
            "station": station_id,
            "steps": len(y_true_station),
            "accuracy_pct": round(acc, 1),
            "false_positive_rate_on_real_weather_pct": round(fp_rate, 2),
        })
        print(f"  -> {len(y_true_station)} scored steps | accuracy {acc:.1f}% | "
              f"false-positive rate on real (un-injected) weather: {fp_rate:.2f}%")

    if not y_true_all:
        print("\n[ERROR] No stations produced scoreable data.")
        return None

    precision = precision_score(y_true_all, y_pred_all, zero_division=0)
    recall = recall_score(y_true_all, y_pred_all, zero_division=0)
    f1 = f1_score(y_true_all, y_pred_all, zero_division=0)
    avg_latency = float(np.mean(latencies_ms))
    overall_fp_rate = np.mean([r["false_positive_rate_on_real_weather_pct"] for r in per_station_results])

    print("\n" + "=" * 70)
    print("📊 REAL-DATA BENCHMARK RESULTS")
    print("=" * 70)
    print(f"• Total Real-Replayed Observations Scored: {len(y_true_all)}")
    print(f"• Overall Detection Precision:  {precision * 100:.2f}%")
    print(f"• Overall Detection Recall:     {recall * 100:.2f}%")
    print(f"• Overall Anomaly F1-Score:     {f1 * 100:.2f}%")
    print(f"• False Positive Rate on real, un-injected historical weather: {overall_fp_rate:.2f}%")
    print(f"• Average Inference Latency:    {avg_latency:.3f} ms / reading")
    print("=" * 70)

    report_lines = [
        "# SkyGuard AI — Real Historical Data Benchmark Report",
        "",
        f"**Evaluation Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Random Seed**: {seed}",
        f"**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)",
        "",
        "Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run "
        "replays genuine historical hourly weather observations as the clean background "
        "signal and injects the same controlled fault sandbox on top. False positives "
        "measured here are against real, unmodeled atmospheric variability.",
        "",
        "## Key Performance Indicators",
        "",
        "| Metric | Measured Value |",
        "| :--- | :--- |",
        f"| Detection Precision | {precision * 100:.2f}% |",
        f"| Detection Recall | {recall * 100:.2f}% |",
        f"| Overall F1-Score | {f1 * 100:.2f}% |",
        f"| False Positive Rate on real, un-injected weather | {overall_fp_rate:.2f}% |",
        f"| Average Inference Latency | {avg_latency:.3f} ms |",
        "",
        "## Per-Station Results",
        "",
        "| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for r in per_station_results:
        report_lines.append(
            f"| {r['station']} | {r['steps']} | {r['accuracy_pct']}% | "
            f"{r['false_positive_rate_on_real_weather_pct']}% |"
        )
    report_content = "\n".join(report_lines) + "\n"

    out_path = Path(__file__).resolve().parent / "real_data_evaluation_report.md"
    with open(out_path, "w") as f:
        f.write(report_content)
    print(f"\n✅ Real-data benchmark report generated at {out_path.relative_to(Path(__file__).resolve().parent.parent)}\n")

    return {
        "precision": precision, "recall": recall, "f1": f1,
        "false_positive_rate_pct": overall_fp_rate, "avg_latency_ms": avg_latency,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SkyGuard AI real-data benchmark evaluation")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducible results")
    args = parser.parse_args()
    run_real_data_benchmark(seed=args.seed)
