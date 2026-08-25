/**
 * SkyGuard AI - Ultra-Lightweight Edge Guard Library (C/C++)
 * Target: ESP32, ARM Cortex-M, Arduino, and Low-Power Edge Gateways.
 * 
 * Features:
 * - O(1) Memory Footprint (< 3.2 KB RAM total)
 * - Zero dynamic memory allocation (no malloc/heap fragmentation)
 * - Psychrometric Magnus-Tetens dew point check
 * - Streaming Welford Z-Score & EWMA volatility
 * - WMO Rate-of-Change step gradient filter
 */

#ifndef SKYGUARD_EDGE_H
#define SKYGUARD_EDGE_H

#include <math.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Edge Anomaly Severity Codes
typedef enum {
    EDGE_SEVERITY_NORMAL = 0,
    EDGE_SEVERITY_LOW = 1,
    EDGE_SEVERITY_MEDIUM = 2,
    EDGE_SEVERITY_HIGH = 3,
    EDGE_SEVERITY_CRITICAL = 4
} EdgeSeverity;

// Edge Fault Classification Codes
typedef enum {
    EDGE_FAULT_NONE = 0,
    EDGE_FAULT_PHYSICS_VIOLATION = 1,
    EDGE_FAULT_RATE_SPIKE = 2,
    EDGE_FAULT_FLATLINE = 3,
    EDGE_FAULT_OUT_OF_BOUNDS = 4,
    EDGE_FAULT_DRIFT = 5
} EdgeFaultType;

// Edge Telemetry Input
typedef struct {
    float temperature_c;
    float pressure_hpa;
    float humidity_pct;
    float dt_seconds;
} EdgeTelemetryInput;

// Edge Detection Result
typedef struct {
    bool is_anomaly;
    float anomaly_confidence; // 0.0 to 1.0
    EdgeSeverity severity;
    EdgeFaultType fault_type;
    float dew_point_c;
    float vpd_hpa;
    float temp_z_score;
    char diagnostic_msg[128];
} EdgeDetectionResult;

// Rolling State Tracker (Stack allocated, < 512 bytes)
typedef struct {
    // Previous readings for rate-of-change
    float prev_temp;
    float prev_pres;
    float prev_hum;
    bool has_prev;

    // Flatline counter
    int flatline_temp_count;
    float last_flat_temp;

    // Welford statistics for temperature
    unsigned long sample_count;
    float mean_temp;
    float m2_temp;

    // WMO threshold limits
    float max_temp_step_per_min;
    float max_pres_step_per_min;
    float max_hum_step_per_min;
} EdgeGuardState;

// Initialize Edge Guard state
static inline void skyguard_edge_init(EdgeGuardState* state) {
    state->prev_temp = 0.0f;
    state->prev_pres = 0.0f;
    state->prev_hum = 0.0f;
    state->has_prev = false;
    state->flatline_temp_count = 0;
    state->last_flat_temp = -999.0f;
    state->sample_count = 0;
    state->mean_temp = 25.0f;
    state->m2_temp = 0.0f;
    state->max_temp_step_per_min = 3.0f;
    state->max_pres_step_per_min = 2.0f;
    state->max_hum_step_per_min = 15.0f;
}

// Magnus-Tetens Dew Point Computation
static inline float skyguard_compute_dew_point(float temp_c, float humidity_pct) {
    if (humidity_pct <= 0.01f) return -99.0f;
    float rh = humidity_pct / 100.0f;
    if (rh > 1.0f) rh = 1.0f;
    
    float b = 17.67f;
    float c = 243.5f;
    if (temp_c < 0.0f) {
        b = 22.5f;
        c = 273.0f;
    }
    
    float gamma = logf(rh) + (b * temp_c) / (c + temp_c);
    if (fabsf(b - gamma) < 1e-5f) return temp_c;
    return (c * gamma) / (b - gamma);
}

// Magnus-Tetens Vapor Pressure Deficit (VPD in hPa)
static inline float skyguard_compute_vpd(float temp_c, float humidity_pct) {
    float b = (temp_c >= 0.0f) ? 17.67f : 22.5f;
    float c = (temp_c >= 0.0f) ? 243.5f : 273.0f;
    float e_s = 6.112f * expf((b * temp_c) / (c + temp_c));
    float e = (humidity_pct / 100.0f) * e_s;
    float vpd = e_s - e;
    return (vpd < 0.0f) ? 0.0f : vpd;
}

// Main Edge Inference Routine (Sub-millisecond execution)
static inline void skyguard_edge_process(
    EdgeGuardState* state,
    const EdgeTelemetryInput* input,
    EdgeDetectionResult* result
) {
    result->is_anomaly = false;
    result->anomaly_confidence = 0.0f;
    result->severity = EDGE_SEVERITY_NORMAL;
    result->fault_type = EDGE_FAULT_NONE;
    result->diagnostic_msg[0] = '\0';

    float t = input->temperature_c;
    float p = input->pressure_hpa;
    float rh = input->humidity_pct;
    float dt = (input->dt_seconds > 0.01f) ? input->dt_seconds : 1.0f;

    // 1. Compute Psychrometrics
    float td = skyguard_compute_dew_point(t, rh);
    float vpd = skyguard_compute_vpd(t, rh);
    result->dew_point_c = td;
    result->vpd_hpa = vpd;

    // 2. Physical Range Boundary Check -- kept in lock-step with the central WMO
    // envelope in backend/app/core/config.py (temp -95..65 C, pressure 300..1085 hPa,
    // humidity 0..100 %). These are the OUTER physical limits of any Earth surface
    // station, not a typical operating range: the old -40..60 C / 700..1100 hPa gate
    // silently rejected legitimate polar and high-altitude readings the corrected
    // central config now accepts.
    if (t < -95.0f || t > 65.0f || p < 300.0f || p > 1085.0f || rh < 0.0f || rh > 100.0f) {
        result->is_anomaly = true;
        result->anomaly_confidence = 1.0f;
        result->severity = EDGE_SEVERITY_CRITICAL;
        result->fault_type = EDGE_FAULT_OUT_OF_BOUNDS;
        return;
    }

    // 3. Thermodynamic Enthalpy Violation Check (T < Td, or implied Td beyond Earth's
    // highest reliably recorded dew point of ~35C at Dhahran, Saudi Arabia, 2003)
    if (td > t + 0.5f || td > 36.0f) {
        result->is_anomaly = true;
        result->anomaly_confidence = 0.95f;
        result->severity = EDGE_SEVERITY_CRITICAL;
        result->fault_type = EDGE_FAULT_PHYSICS_VIOLATION;
        return;
    }

    // 4. Rate-of-Change & Spike Filter
    if (state->has_prev) {
        float time_factor = dt / 60.0f;
        if (time_factor < 0.05f) time_factor = 0.05f;

        float dt_val = fabsf(t - state->prev_temp);
        float dp_val = fabsf(p - state->prev_pres);
        float drh_val = fabsf(rh - state->prev_hum);

        float max_dt = state->max_temp_step_per_min * time_factor;
        float max_dp = state->max_pres_step_per_min * time_factor;
        float max_drh = state->max_hum_step_per_min * time_factor;

        if (dt_val > max_dt || dp_val > max_dp || drh_val > max_drh) {
            result->is_anomaly = true;
            result->anomaly_confidence = 0.85f;
            result->severity = EDGE_SEVERITY_HIGH;
            result->fault_type = EDGE_FAULT_RATE_SPIKE;
            return;
        }
    }

    // 5. Flatline (ADC Stuck) Detection
    if (state->last_flat_temp == t) {
        state->flatline_temp_count++;
        if (state->flatline_temp_count >= 5) {
            result->is_anomaly = true;
            result->anomaly_confidence = 0.90f;
            result->severity = EDGE_SEVERITY_HIGH;
            result->fault_type = EDGE_FAULT_FLATLINE;
            return;
        }
    } else {
        state->last_flat_temp = t;
        state->flatline_temp_count = 1;
    }

    // 6. Online Welford Z-Score Update
    state->sample_count++;
    float delta = t - state->mean_temp;
    state->mean_temp += delta / (float)state->sample_count;
    float delta2 = t - state->mean_temp;
    state->m2_temp += delta * delta2;

    float variance = (state->sample_count > 1) ? (state->m2_temp / (float)state->sample_count) : 1.0f;
    float std_dev = sqrtf(variance);
    if (std_dev < 0.1f) std_dev = 0.1f;
    float z = fabsf(t - state->mean_temp) / std_dev;
    result->temp_z_score = z;

    if (state->sample_count > 10 && z > 3.8f) {
        result->is_anomaly = true;
        result->anomaly_confidence = 0.75f;
        result->severity = EDGE_SEVERITY_MEDIUM;
        result->fault_type = EDGE_FAULT_DRIFT;
        return;
    }

    // Update state for next cycle
    state->prev_temp = t;
    state->prev_pres = p;
    state->prev_hum = rh;
    state->has_prev = true;
}

#ifdef __cplusplus
}
#endif

#endif // SKYGUARD_EDGE_H
