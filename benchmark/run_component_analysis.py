"""
SkyGuard AI - Per-Component Detection Analysis
Breaks the ensemble apart: measures each of the four detection components (physics
engine, temporal autoencoder, isolation forest, statistical/CUSUM filter) as a
STANDALONE detector -- "if we only used this one signal, thresholded at the
ensemble's own thresh_low (0.35), how would it do alone?" -- against the same
ground-truth labels used by run_benchmark.py and run_real_data_benchmark.py, on
both the synthetic and real-data test harnesses.

This exists to answer "which model is actually doing the work" directly, rather
than only reporting the combined ensemble's precision/recall/F1 (which mixes all
four signals together and doesn't say how much any single one is contributing).

Run:
    python benchmark/run_component_analysis.py
"""

import sys
import csv
import random
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

from backend.app.core.config import config
from backend.app.core.data_generator import VirtualAWSNetworkSimulator, AnomalyInjectionRequest
from backend.app.core.pipeline import SkyGuardPipeline

DEFAULT_SEED = 42
THRESH = config.thresh_low  # 0.35 -- the same cutoff the ensemble itself uses for "is_anomaly"

COMPONENTS = {
    "physics": lambda res: res["physics"]["physics_anomaly_score"],
    "autoencoder": lambda res: res["autoencoder"]["ae_anomaly_prob"],
    "isolation_forest": lambda res: res["isolation_forest"]["isolation_anomaly_prob"],
    "statistical": lambda res: res["statistical"]["stat_anomaly_score"],
    "ensemble (all 4 combined)": lambda res: res["ensemble"]["confidence_score"],
}


def score_all(y_true, component_scores):
    results = {}
    for name, scores in component_scores.items():
        y_pred = [1 if s >= THRESH else 0 for s in scores]
        results[name] = {
            "precision": precision_score(y_true, y_pred, zero_division=0) * 100,
            "recall": recall_score(y_true, y_pred, zero_division=0) * 100,
            "f1": f1_score(y_true, y_pred, zero_division=0) * 100,
        }
    return results


def print_table(title, results):
    print(f"\n{title}")
    print(f"{'Component':<28} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 60)
    for name, m in results.items():
        marker = " <-- combined" if "ensemble" in name else ""
        print(f"{name:<28} {m['precision']:>9.1f}% {m['recall']:>9.1f}% {m['f1']:>9.1f}%{marker}")


def run_synthetic(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    station_id = "AWS_ALPHA_MOUNTAIN"
    test_cases = [
        {"type": None, "steps": 250, "label": 0},
        {"type": "spike", "sensor": "temperature", "intensity": 1.2, "steps": 60, "label": 1},
        {"type": "flatline", "sensor": "temperature", "intensity": 1.0, "steps": 60, "label": 1},
        {"type": "drift", "sensor": "temperature", "intensity": 1.0, "steps": 60, "label": 1},
        {"type": "physics_violation", "sensor": "all", "intensity": 1.0, "steps": 60, "label": 1},
        {"type": "packet_loss", "sensor": "all", "intensity": 1.0, "steps": 40, "label": 1},
        {"type": "thunderstorm", "sensor": "all", "intensity": 1.0, "steps": 80, "label": 0},
    ]

    y_true = []
    component_scores = {name: [] for name in COMPONENTS}

    for tc in test_cases:
        sim = VirtualAWSNetworkSimulator()
        pipe = SkyGuardPipeline()
        for _ in range(20):
            w = sim.generate_next_reading(station_id, dt_seconds=1.0)
            pipe.process_reading(w, dt_seconds=1.0)
        if tc["type"] is not None:
            sim.inject_anomaly(AnomalyInjectionRequest(
                station_id=station_id, anomaly_type=tc["type"], sensor=tc.get("sensor", "temperature"),
                intensity=tc.get("intensity", 1.0), duration_steps=tc["steps"]
            ))
        for _ in range(tc["steps"]):
            raw = sim.generate_next_reading(station_id, dt_seconds=1.0)
            res = pipe.process_reading(raw, dt_seconds=1.0)
            effective = raw.get("injected_anomalies_effective", [])
            label = 1 if (tc["type"] is not None and tc["type"] in effective) else (
                0 if tc["label"] == 0 else 0
            )
            y_true.append(label)
            for name, fn in COMPONENTS.items():
                component_scores[name].append(fn(res))

    return score_all(y_true, component_scores), len(y_true)


def run_real_data(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    real_dir = Path(__file__).resolve().parent.parent / "data" / "real_stations" / "processed"
    if not real_dir.is_dir() or not any(real_dir.glob("*.csv")):
        print("[SKIP] No real station data found -- run data/real_stations/fetch_and_process.py")
        return None, 0

    injection_cycle = [
        {"type": None, "steps": 80},
        {"type": "spike", "sensor": "temperature", "intensity": 2.5, "steps": 20},
        {"type": None, "steps": 60},
        {"type": "flatline", "sensor": "temperature", "intensity": 1.0, "steps": 20},
        {"type": None, "steps": 60},
        {"type": "drift", "sensor": "temperature", "intensity": 25.0, "steps": 20},
        {"type": None, "steps": 60},
        {"type": "physics_violation", "sensor": "all", "intensity": 1.0, "steps": 15},
        {"type": None, "steps": 60},
        {"type": "packet_loss", "sensor": "all", "intensity": 1.0, "steps": 15},
        {"type": None, "steps": 80},
    ]

    y_true = []
    component_scores = {name: [] for name in COMPONENTS}

    for csv_path in sorted(real_dir.glob("*.csv")):
        station_id = csv_path.stem
        with open(csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) < 1530:
            continue
        for r in rows:
            r["_dt"] = datetime.fromisoformat(r["timestamp"])
        rows = rows[:1530]

        sim = VirtualAWSNetworkSimulator()
        pipe = SkyGuardPipeline()
        prev_dt = None
        for r in rows[:30]:
            dt = max(60.0, (r["_dt"] - prev_dt).total_seconds()) if prev_dt else 3600.0
            raw = sim.generate_next_reading_from_real(
                station_id, float(r["temperature_c"]), float(r["pressure_hpa"]),
                float(r["humidity_pct"]), r["timestamp"], dt_seconds=dt
            )
            pipe.process_reading(raw, dt_seconds=dt)
            prev_dt = r["_dt"]

        remaining = rows[30:]
        cursor, cycle_i = 0, 0
        while cursor < len(remaining):
            block = injection_cycle[cycle_i % len(injection_cycle)]
            cycle_i += 1
            n = min(block["steps"], len(remaining) - cursor)
            if n <= 0:
                break
            if block["type"] is not None:
                sim.inject_anomaly(AnomalyInjectionRequest(
                    station_id=station_id, anomaly_type=block["type"],
                    sensor=block.get("sensor", "temperature"), intensity=block.get("intensity", 1.0),
                    duration_steps=n
                ))
            for _ in range(n):
                r = remaining[cursor]
                dt = max(60.0, (r["_dt"] - prev_dt).total_seconds())
                raw = sim.generate_next_reading_from_real(
                    station_id, float(r["temperature_c"]), float(r["pressure_hpa"]),
                    float(r["humidity_pct"]), r["timestamp"], dt_seconds=dt
                )
                res = pipe.process_reading(raw, dt_seconds=dt)
                effective = raw.get("injected_anomalies_effective", [])
                label = 1 if (block["type"] is not None and block["type"] in effective) else 0
                y_true.append(label)
                for name, fn in COMPONENTS.items():
                    component_scores[name].append(fn(res))
                prev_dt = r["_dt"]
                cursor += 1

    return score_all(y_true, component_scores), len(y_true)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SkyGuard AI per-component detection analysis")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    print("=" * 70)
    print("🔬 SKYGUARD AI — PER-COMPONENT DETECTION ANALYSIS")
    print(f"   (threshold={THRESH}, seed={args.seed})")
    print("=" * 70)

    synth_results, synth_n = run_synthetic(args.seed)
    print_table(f"Synthetic generator ({synth_n} observations)", synth_results)

    real_results, real_n = run_real_data(args.seed)
    if real_results:
        print_table(f"\nReal NOAA history ({real_n} observations)", real_results)
