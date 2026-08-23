# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 21:08:37
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 91.22% |
| Detection Recall | 88.82% |
| Overall F1-Score | 90.01% |
| False Positive Rate on real, un-injected weather | 1.60% |
| Average Inference Latency | 5.285 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 93.5% | 3.72% |
| AWS_BETA_COASTAL | 1500 | 98.0% | 1.19% |
| AWS_DELTA_DESERT | 1500 | 98.0% | 0.87% |
| AWS_GAMMA_URBAN | 1500 | 98.1% | 0.63% |

## Recall by Injected Fault Category (aggregated across all stations)

| Fault Type | Detected / Injected | Recall |
| :--- | :--- | :--- |
| drift | 206/240 | 85.8% |
| flatline | 216/240 | 90.0% |
| packet_loss | 153/180 | 85.0% |
| physics_violation | 180/180 | 100.0% |
| spike | 87/108 | 80.6% |
