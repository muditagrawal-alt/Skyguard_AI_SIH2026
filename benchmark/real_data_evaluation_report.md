# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 20:02:08
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 93.00% |
| Detection Recall | 63.08% |
| Overall F1-Score | 75.17% |
| False Positive Rate on real, un-injected weather | 0.89% |
| Average Inference Latency | 5.196 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 92.2% | 0.63% |
| AWS_BETA_COASTAL | 1500 | 93.3% | 1.58% |
| AWS_DELTA_DESERT | 1500 | 93.7% | 0.71% |
| AWS_GAMMA_URBAN | 1500 | 94.5% | 0.63% |

## Recall by Injected Fault Category (aggregated across all stations)

| Fault Type | Detected / Injected | Recall |
| :--- | :--- | :--- |
| drift | 1/240 | 0.4% |
| flatline | 204/240 | 85.0% |
| packet_loss | 133/180 | 73.9% |
| physics_violation | 180/180 | 100.0% |
| spike | 80/108 | 74.1% |
