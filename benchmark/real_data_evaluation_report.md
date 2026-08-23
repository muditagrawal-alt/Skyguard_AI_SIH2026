# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 18:30:07
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 71.91% |
| Detection Recall | 62.66% |
| Overall F1-Score | 66.97% |
| False Positive Rate on real, un-injected weather | 4.59% |
| Average Inference Latency | 5.074 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 83.4% | 12.98% |
| AWS_BETA_COASTAL | 1500 | 92.2% | 2.77% |
| AWS_DELTA_DESERT | 1500 | 92.5% | 1.5% |
| AWS_GAMMA_URBAN | 1500 | 92.8% | 1.11% |
