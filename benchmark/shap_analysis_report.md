# SkyGuard AI — Genuine SHAP Explainability Report

**Generated**: 2026-08-24 00:25:11
**Explainer**: `shap.KernelExplainer` over the Isolation Forest's `decision_function`
**Background**: 100 real NOAA ISD-Lite observations, reduced to 20 kmeans centroids
**Points explained**: 14

This is a REAL, computed SHAP analysis -- distinct from the fast additive-heuristic attribution shown live in the UI/API (backend/app/xai/explainer.py), which is not SHAP despite what earlier documentation called it. See this script's module docstring for why genuine SHAP runs offline rather than per-packet.

## Global Feature Importance (mean |SHAP value| across explained points)

| Rank | Feature | Mean \|SHAP value\| |
| :--- | :--- | :--- |
| 1 | delta_temp | 0.0174 |
| 2 | delta_pres | 0.0142 |
| 3 | delta_hum | 0.0137 |
| 4 | dew_point_depression | 0.0122 |
| 5 | temperature | 0.0093 |
| 6 | humidity | 0.0093 |
| 7 | vpd | 0.0088 |
| 8 | pressure | 0.0072 |

## Per-Point SHAP Attributions

| Point | temperature | pressure | humidity | delta_temp | delta_pres | delta_hum | vpd | dew_point_depression |
| :--- | --- | --- | --- | --- | --- | --- | --- | --- |
| real_sample_0 | +0.001 | +0.022 | +0.021 | +0.047 | +0.019 | +0.034 | -0.002 | +0.031 |
| real_sample_1 | -0.004 | -0.003 | -0.006 | +0.003 | +0.058 | +0.014 | +0.012 | +0.003 |
| real_sample_2 | +0.029 | +0.006 | +0.001 | -0.000 | -0.001 | -0.005 | -0.009 | -0.008 |
| real_sample_3 | -0.005 | +0.000 | -0.008 | +0.002 | +0.003 | -0.001 | +0.000 | -0.005 |
| real_sample_4 | -0.005 | +0.002 | -0.011 | -0.007 | -0.006 | -0.009 | -0.002 | +0.009 |
| real_sample_5 | -0.007 | -0.004 | +0.006 | -0.005 | -0.009 | -0.014 | +0.009 | +0.025 |
| real_sample_6 | -0.005 | -0.004 | -0.015 | +0.001 | -0.006 | -0.007 | +0.010 | +0.007 |
| real_sample_7 | -0.005 | -0.002 | -0.001 | -0.007 | -0.005 | -0.006 | -0.011 | -0.015 |
| real_sample_8 | -0.001 | -0.002 | +0.001 | +0.001 | +0.022 | +0.033 | -0.002 | -0.011 |
| real_sample_9 | +0.013 | +0.005 | -0.005 | -0.006 | -0.007 | +0.001 | -0.007 | -0.001 |
| synthetic_sensor_spike | +0.027 | -0.004 | -0.008 | +0.087 | -0.004 | -0.004 | +0.023 | +0.012 |
| synthetic_near_normal | -0.003 | -0.003 | -0.002 | -0.001 | +0.001 | -0.002 | +0.001 | -0.010 |
| synthetic_pressure_drop_event | -0.003 | +0.041 | +0.017 | -0.002 | +0.055 | -0.002 | +0.002 | -0.004 |
| synthetic_physics_violation | +0.021 | -0.001 | +0.029 | +0.074 | +0.003 | +0.060 | +0.035 | +0.030 |
