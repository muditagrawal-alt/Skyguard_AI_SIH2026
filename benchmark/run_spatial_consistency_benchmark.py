"""
SkyGuard AI - Cross-Station Spatial Consistency Demonstration
Directly measures the effect of the spatial consistency check (pipeline.py
_get_spatial_context + root_cause.py's use of it) on the thunderstorm false-alarm
rate, by running the SAME thunderstorm injection twice through a SHARED pipeline
instance that concurrently tracks all 4 stations (a precondition for the spatial
check to have data -- see the docstring on _get_spatial_context):

  Scenario A (isolated):     storm hits AWS_ALPHA_MOUNTAIN only; the other 3
                              stations continue reporting normal baseline weather.
  Scenario B (corroborated): the SAME storm hits AWS_ALPHA_MOUNTAIN AND
                              AWS_BETA_COASTAL concurrently (a synoptic-scale system
                              reaching multiple stations).

Run:
    python benchmark/run_spatial_consistency_benchmark.py
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from backend.app.core.data_generator import VirtualAWSNetworkSimulator, AnomalyInjectionRequest
from backend.app.core.pipeline import SkyGuardPipeline

SEED = 42
STATIONS = ["AWS_ALPHA_MOUNTAIN", "AWS_BETA_COASTAL", "AWS_GAMMA_URBAN", "AWS_DELTA_DESERT"]
WARMUP_STEPS = 25
STORM_STEPS = 80


def run_scenario(storm_stations):
    random.seed(SEED)
    np.random.seed(SEED)

    sim = VirtualAWSNetworkSimulator()
    pipe = SkyGuardPipeline()

    # Warm up all 4 stations concurrently so every station has buffer history
    # before the storm starts (a precondition for the spatial check to fire).
    for _ in range(WARMUP_STEPS):
        for sid in STATIONS:
            raw = sim.generate_next_reading(sid, dt_seconds=1.0)
            pipe.process_reading(raw, dt_seconds=1.0)

    for sid in storm_stations:
        sim.inject_anomaly(AnomalyInjectionRequest(
            station_id=sid, anomaly_type="thunderstorm", sensor="all",
            intensity=1.0, duration_steps=STORM_STEPS
        ))

    false_alarms = {sid: 0 for sid in storm_stations}
    for _ in range(STORM_STEPS):
        for sid in STATIONS:
            raw = sim.generate_next_reading(sid, dt_seconds=1.0)
            res = pipe.process_reading(raw, dt_seconds=1.0)
            if sid in storm_stations:
                is_fault_flagged = res["ensemble"]["is_anomaly"] and not res["root_cause"]["is_genuine_weather"]
                if is_fault_flagged:
                    false_alarms[sid] += 1

    return {sid: (false_alarms[sid] / STORM_STEPS) * 100.0 for sid in storm_stations}


def main():
    print("=" * 70)
    print("🛰️  SKYGUARD AI — CROSS-STATION SPATIAL CONSISTENCY DEMONSTRATION")
    print("=" * 70)

    print("\nScenario A: ISOLATED storm at AWS_ALPHA_MOUNTAIN only "
          "(3 other stations stay normal, concurrently tracked)")
    far_isolated = run_scenario(["AWS_ALPHA_MOUNTAIN"])
    for sid, far in far_isolated.items():
        print(f"  {sid}: false alarm rate = {far:.2f}%")

    print("\nScenario B: CORROBORATED storm hitting AWS_ALPHA_MOUNTAIN AND "
          "AWS_BETA_COASTAL concurrently")
    far_corroborated = run_scenario(["AWS_ALPHA_MOUNTAIN", "AWS_BETA_COASTAL"])
    for sid, far in far_corroborated.items():
        print(f"  {sid}: false alarm rate = {far:.2f}%")

    print("\n" + "=" * 70)
    delta = far_isolated["AWS_ALPHA_MOUNTAIN"] - far_corroborated["AWS_ALPHA_MOUNTAIN"]
    print(f"Effect of spatial corroboration on AWS_ALPHA_MOUNTAIN false alarm rate: "
          f"{far_isolated['AWS_ALPHA_MOUNTAIN']:.2f}% (isolated) -> "
          f"{far_corroborated['AWS_ALPHA_MOUNTAIN']:.2f}% (corroborated) "
          f"[{'-' if delta >= 0 else '+'}{abs(delta):.2f}pp]")
    print("=" * 70)


if __name__ == "__main__":
    main()
