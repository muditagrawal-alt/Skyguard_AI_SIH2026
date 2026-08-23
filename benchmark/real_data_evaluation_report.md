# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-24 00:23:41
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 96.43% |
| Detection Recall | 88.29% |
| Overall F1-Score | 92.18% |
| False Positive Rate on real, un-injected weather | 0.61% |
| Average Inference Latency | 5.291 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 95.0% | 1.74% |
| AWS_BETA_COASTAL | 1500 | 98.5% | 0.63% |
| AWS_DELTA_DESERT | 1500 | 98.5% | 0.08% |
| AWS_GAMMA_URBAN | 1500 | 98.6% | 0.0% |

## Recall by Injected Fault Category (aggregated across all stations)

| Fault Type | Detected / Injected | Recall |
| :--- | :--- | :--- |
| drift | 205/240 | 85.4% |
| flatline | 216/240 | 90.0% |
| packet_loss | 151/180 | 83.9% |
| physics_violation | 180/180 | 100.0% |
| spike | 85/108 | 78.7% |
