# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 23:47:18
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 96.09% |
| Detection Recall | 88.08% |
| Overall F1-Score | 91.91% |
| False Positive Rate on real, un-injected weather | 0.67% |
| Average Inference Latency | 5.331 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 94.8% | 1.98% |
| AWS_BETA_COASTAL | 1500 | 98.5% | 0.63% |
| AWS_DELTA_DESERT | 1500 | 98.3% | 0.08% |
| AWS_GAMMA_URBAN | 1500 | 98.6% | 0.0% |

## Recall by Injected Fault Category (aggregated across all stations)

| Fault Type | Detected / Injected | Recall |
| :--- | :--- | :--- |
| drift | 204/240 | 85.0% |
| flatline | 216/240 | 90.0% |
| packet_loss | 150/180 | 83.3% |
| physics_violation | 180/180 | 100.0% |
| spike | 85/108 | 78.7% |
