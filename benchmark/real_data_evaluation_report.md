# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 18:50:03
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 97.22% |
| Detection Recall | 59.07% |
| Overall F1-Score | 73.49% |
| False Positive Rate on real, un-injected weather | 0.32% |
| Average Inference Latency | 5.000 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 92.3% | 0.4% |
| AWS_BETA_COASTAL | 1500 | 94.0% | 0.55% |
| AWS_DELTA_DESERT | 1500 | 93.1% | 0.24% |
| AWS_GAMMA_URBAN | 1500 | 93.7% | 0.08% |
