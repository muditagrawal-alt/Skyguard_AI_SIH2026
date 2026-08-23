# SkyGuard AI — Genuine SHAP Explainability Report

**Generated**: 2026-08-23 18:50:07
**Explainer**: `shap.KernelExplainer` over the Isolation Forest's `decision_function`
**Background**: 100 real NOAA ISD-Lite observations, reduced to 20 kmeans centroids
**Points explained**: 14

This is a REAL, computed SHAP analysis -- distinct from the fast additive-heuristic attribution shown live in the UI/API (backend/app/xai/explainer.py), which is not SHAP despite what earlier documentation called it. See this script's module docstring for why genuine SHAP runs offline rather than per-packet.

## Global Feature Importance (mean |SHAP value| across explained points)

| Rank | Feature | Mean \|SHAP value\| |
| :--- | :--- | :--- |
| 1 | delta_temp | 0.0163 |
| 2 | delta_hum | 0.0113 |
| 3 | humidity | 0.0084 |
| 4 | dew_point_depression | 0.0080 |
| 5 | delta_pres | 0.0073 |
| 6 | vpd | 0.0072 |
| 7 | temperature | 0.0065 |
| 8 | pressure | 0.0050 |

## Per-Point SHAP Attributions

| Point | temperature | pressure | humidity | delta_temp | delta_pres | delta_hum | vpd | dew_point_depression |
| :--- | --- | --- | --- | --- | --- | --- | --- | --- |
| real_sample_0 | -0.001 | +0.003 | -0.011 | -0.006 | -0.002 | -0.011 | -0.005 | -0.003 |
| real_sample_1 | -0.008 | +0.000 | -0.001 | +0.042 | -0.004 | +0.009 | -0.007 | -0.011 |
| real_sample_2 | -0.003 | +0.002 | +0.004 | -0.005 | -0.006 | -0.009 | +0.008 | +0.021 |
| real_sample_3 | +0.000 | +0.008 | -0.004 | -0.001 | -0.004 | -0.009 | +0.007 | -0.001 |
| real_sample_4 | -0.000 | -0.001 | -0.009 | -0.005 | -0.002 | -0.010 | -0.004 | -0.000 |
| real_sample_5 | +0.002 | +0.004 | +0.011 | -0.003 | -0.005 | -0.013 | -0.005 | -0.005 |
| real_sample_6 | -0.008 | -0.000 | +0.015 | -0.001 | -0.003 | -0.009 | +0.000 | -0.002 |
| real_sample_7 | -0.004 | -0.002 | +0.011 | -0.004 | +0.004 | -0.006 | -0.007 | -0.007 |
| real_sample_8 | -0.007 | +0.002 | -0.004 | -0.006 | +0.010 | -0.010 | -0.004 | -0.010 |
| real_sample_9 | -0.007 | -0.002 | -0.006 | -0.002 | -0.005 | -0.008 | -0.000 | -0.001 |
| synthetic_sensor_spike | +0.029 | -0.003 | -0.002 | +0.080 | -0.000 | -0.007 | +0.016 | +0.009 |
| synthetic_near_normal | -0.003 | -0.002 | -0.007 | +0.003 | -0.002 | -0.001 | -0.002 | -0.008 |
| synthetic_pressure_drop_event | -0.003 | +0.042 | +0.011 | +0.000 | +0.049 | -0.006 | +0.004 | -0.006 |
| synthetic_physics_violation | +0.016 | -0.001 | +0.021 | +0.068 | +0.005 | +0.048 | +0.031 | +0.029 |
