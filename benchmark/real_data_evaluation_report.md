# SkyGuard AI — Real Historical Data Benchmark Report

**Evaluation Date**: 2026-08-23 19:19:20
**Random Seed**: 42
**Data Source**: NOAA ISD-Lite (see data/real_stations/STATION_SOURCES.md)

Unlike `benchmark/run_benchmark.py` (fully synthetic diurnal generator), this run replays genuine historical hourly weather observations as the clean background signal and injects the same controlled fault sandbox on top. False positives measured here are against real, unmodeled atmospheric variability.

## Key Performance Indicators

| Metric | Measured Value |
| :--- | :--- |
| Detection Precision | 89.82% |
| Detection Recall | 63.29% |
| Overall F1-Score | 74.26% |
| False Positive Rate on real, un-injected weather | 1.35% |
| Average Inference Latency | 5.167 ms |

## Per-Station Results

| Station | Steps Scored | Accuracy | False Positive Rate (real weather) |
| :--- | :--- | :--- | :--- |
| AWS_ALPHA_MOUNTAIN | 1500 | 91.9% | 1.19% |
| AWS_BETA_COASTAL | 1500 | 92.6% | 2.38% |
| AWS_DELTA_DESERT | 1500 | 93.3% | 1.27% |
| AWS_GAMMA_URBAN | 1500 | 94.5% | 0.55% |

## Recall by Injected Fault Category (aggregated across all stations)

| Fault Type | Detected / Injected | Recall |
| :--- | :--- | :--- |
| drift | 1/240 | 0.4% |
| flatline | 204/240 | 85.0% |
| packet_loss | 133/180 | 73.9% |
| physics_violation | 180/180 | 100.0% |
| spike | 82/108 | 75.9% |
