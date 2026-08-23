"""
SkyGuard AI - Interactive Streamlit Testing & Demonstration UI
Real-time Physics-Informed Anomaly Detection, Self-Healing, XAI, and Sensor Health Radar.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from backend.app.core.config import config
from backend.app.core.data_generator import simulator, AnomalyInjectionRequest
from backend.app.core.pipeline import pipeline

# Page configuration
st.set_page_config(
    page_title="SkyGuard AI - AWS Anomaly Detection Platform",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark aesthetic & styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 12px;
    }
    .status-badge-normal {
        background-color: #059669; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;
    }
    .status-badge-anomaly {
        background-color: #dc2626; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;
    }
    .status-badge-weather {
        background-color: #2563eb; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;
    }
    .diagnostic-box {
        background: rgba(15, 23, 42, 0.85);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "selected_station" not in st.session_state:
    st.session_state.selected_station = "AWS_ALPHA_MOUNTAIN"
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []


# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/radar.png", width=70)
    st.title("SkyGuard AI")
    st.caption("Intelligent Real-Time Anomaly Detection for AWS")
    st.markdown("---")

    # Station Selection
    st.subheader("📍 Weather Station")
    station_names = {s_id: p.name for s_id, p in config.stations.items()}
    chosen_station = st.selectbox(
        "Select Active Station",
        options=list(station_names.keys()),
        format_func=lambda x: station_names[x]
    )
    if chosen_station != st.session_state.selected_station:
        st.session_state.selected_station = chosen_station
        st.session_state.history = []  # Clear history on station switch

    profile = config.stations[st.session_state.selected_station]
    st.info(f"**Type**: {profile.station_type} | **Elevation**: {profile.elevation_m}m\n\n"
            f"**Baseline**: {profile.base_temp_c}°C, {profile.base_pressure_hpa} hPa, {profile.base_humidity_pct}% RH")

    st.markdown("---")
    st.subheader("⚙️ Stream Simulation Control")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ Start Stream", use_container_width=True):
            st.session_state.is_running = True
    with col_btn2:
        if st.button("⏹️ Stop Stream", use_container_width=True):
            st.session_state.is_running = False

    sim_speed = st.slider("Simulation Speed (Delay)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, format="%.1fs")

    if st.button("🗑️ Clear Buffer", use_container_width=True):
        st.session_state.history = []
        st.session_state.audit_log = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 WMO QC Standard")
    st.caption("• Max ΔT: 3.0°C / min\n• Max ΔP: 2.0 hPa / min\n• Max ΔRH: 15.0% / min\n• Clausius-Clapeyron: T ≥ Td")


# Main Dashboard Header
st.title("🌦️ SkyGuard AI — Real-Time Control Center")
st.markdown(f"**Active Stream**: `{profile.name}` ({profile.station_type} Station at {profile.latitude}°N, {profile.longitude}°E)")


# Anomaly Injection Sandbox Panel
st.subheader("🧪 Dynamic Anomaly Injection Sandbox")
st.caption("Click any action to inject simulated hardware glitches, telemetry errors, or a genuine severe convective storm into the live stream:")

inj_col1, inj_col2, inj_col3, inj_col4, inj_col5, inj_col6 = st.columns(6)

with inj_col1:
    if st.button("⚡ Temp Spike\n(+15°C)", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="spike", sensor="temperature", intensity=1.0, duration_steps=3
        ))
        st.toast("⚡ Injected Temperature Spike (+15°C)!")

with inj_col2:
    if st.button("❄️ Sensor Freeze\n(Flatline)", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="flatline", sensor="temperature", intensity=1.0, duration_steps=8
        ))
        st.toast("❄️ Injected Sensor Flatlining (Stuck ADC)!")

with inj_col3:
    if st.button("📈 Calibration Drift\n(+0.25°C/step)", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="drift", sensor="temperature", intensity=1.0, duration_steps=12
        ))
        st.toast("📈 Injected Progressive Calibration Drift!")

with inj_col4:
    if st.button("⚠️ Physics Fault\n(54°C & 96% RH)", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="physics_violation", sensor="all", intensity=1.0, duration_steps=5
        ))
        st.toast("⚠️ Injected Thermodynamic Enthalpy Violation!")

with inj_col5:
    if st.button("📶 Packet Loss\n& Dropouts", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="packet_loss", sensor="all", intensity=1.0, duration_steps=6
        ))
        st.toast("📶 Injected Telemetry Packet Loss & Outliers!")

with inj_col6:
    if st.button("⛈️ Thunderstorm\n(0% False Alarm)", use_container_width=True):
        simulator.inject_anomaly(AnomalyInjectionRequest(
            station_id=st.session_state.selected_station,
            anomaly_type="thunderstorm", sensor="all", intensity=1.0, duration_steps=15
        ))
        st.toast("⛈️ Simulated Severe Convective Thunderstorm!")


# Processing Step: If running or empty, step the simulation
if st.session_state.is_running or len(st.session_state.history) == 0:
    raw_packet = simulator.generate_next_reading(st.session_state.selected_station, dt_seconds=sim_speed)
    processed = pipeline.process_reading(raw_packet, dt_seconds=sim_speed)
    st.session_state.history.append(processed)
    
    # Keep buffer length manageable
    if len(st.session_state.history) > 60:
        st.session_state.history.pop(0)

    # Log to audit log if anomalous or extreme weather
    if processed["ensemble"]["is_anomaly"] or processed["root_cause"]["is_genuine_weather"] and processed["root_cause"]["fault_type"] != "NORMAL":
        st.session_state.audit_log.append({
            "timestamp": processed["timestamp"],
            "station": processed["station_id"],
            "fault_type": processed["root_cause"]["fault_type"],
            "category": processed["root_cause"]["fault_category"],
            "severity": processed["ensemble"]["severity"],
            "confidence": f"{processed['ensemble']['confidence_score'] * 100:.1f}%",
            "raw_t": processed["raw"]["temperature"],
            "imputed_t": processed["imputed"]["temperature"],
            "explanation": processed["xai"]["explanation"]
        })


# Extract Latest Packet
latest = st.session_state.history[-1] if st.session_state.history else None

if latest:
    # Metric Summary Row
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
    
    t_val = latest["raw"]["temperature"]
    p_val = latest["raw"]["pressure"]
    rh_val = latest["raw"]["humidity"]
    
    m_col1.metric("🌡️ Temperature", f"{t_val:.1f} °C" if t_val is not None else "LOST (NaN)")
    m_col2.metric("📊 Pressure", f"{p_val:.1f} hPa" if p_val is not None else "LOST (NaN)")
    m_col3.metric("💧 Humidity", f"{rh_val:.1f} %" if rh_val is not None else "LOST (NaN)")
    
    td_val = latest["physics"].get("dew_point_c")
    vpd_val = latest["physics"].get("vpd_hpa")
    m_col4.metric("🌫️ Dew Point (Td)", f"{td_val:.1f} °C" if td_val is not None else "N/A")
    m_col5.metric("💨 Vapor Deficit (VPD)", f"{vpd_val:.1f} hPa" if vpd_val is not None else "N/A")

    # Status Badge
    is_anom = latest["ensemble"]["is_anomaly"]
    fault_type = latest["root_cause"]["fault_type"]
    severity = latest["ensemble"]["severity"]
    
    if not is_anom:
        status_html = "<span class='status-badge-normal'>✅ NORMAL STREAM</span>"
    elif fault_type == "GENUINE_EXTREME_WEATHER":
        status_html = "<span class='status-badge-weather'>⛈️ GENUINE WEATHER EVENT</span>"
    else:
        status_html = f"<span class='status-badge-anomaly'>⚠️ {severity} FAULT ({fault_type})</span>"

    with m_col6:
        st.markdown(f"**Anomaly State**")
        st.markdown(status_html, unsafe_allow_html=True)


# Telemetry Time-Series Visualizer
st.markdown("---")
st.subheader("📈 Real-Time Multi-Parameter Sensor Telemetry")

if len(st.session_state.history) > 0:
    df_hist = []
    for idx, item in enumerate(st.session_state.history):
        raw = item["raw"]
        clean = item["clean_ground_truth"]
        imputed = item["imputed"]
        ensemble = item["ensemble"]
        root_cause = item["root_cause"]
        physics = item["physics"]

        df_hist.append({
            "step": idx,
            "sim_hour": item.get("simulated_hour", idx),
            "temp_raw": raw.get("temperature"),
            "temp_clean": clean.get("temperature"),
            "temp_imputed": imputed.get("temperature"),
            "pres_raw": raw.get("pressure"),
            "pres_clean": clean.get("pressure"),
            "pres_imputed": imputed.get("pressure"),
            "hum_raw": raw.get("humidity"),
            "hum_clean": clean.get("humidity"),
            "hum_imputed": imputed.get("humidity"),
            "dew_point": physics.get("dew_point_c"),
            "is_anomaly": ensemble.get("is_anomaly", False),
            "is_weather": root_cause.get("is_genuine_weather", True),
            "fault_type": root_cause.get("fault_type", "NORMAL"),
            "confidence": ensemble.get("confidence_score", 0.0)
        })

    df = pd.DataFrame(df_hist)

    # Create 3-row synchronized subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        subplot_titles=(
            "Temperature (°C) — Raw vs. Self-Healed Imputed Stream",
            "Atmospheric Pressure (hPa)",
            "Relative Humidity (%) & Dew Point (°C)"
        )
    )

    # 1. Temperature Plot
    fig.add_trace(go.Scatter(
        x=df["step"], y=df["temp_clean"],
        mode="lines", name="Ground Truth (Clean)",
        line=dict(color="rgba(148, 163, 184, 0.4)", width=1.5, dash="dot")
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["temp_raw"],
        mode="lines+markers", name="Raw Sensor Telemetry",
        line=dict(color="#f97316", width=2),
        marker=dict(size=4)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["temp_imputed"],
        mode="lines", name="Self-Healed Imputed",
        line=dict(color="#10b981", width=2.5, dash="dash")
    ), row=1, col=1)

    # Anomaly Markers on Temperature
    anom_df = df[df["is_anomaly"] & (~df["is_weather"])]
    if not anom_df.empty:
        fig.add_trace(go.Scatter(
            x=anom_df["step"], y=anom_df["temp_raw"].fillna(anom_df["temp_imputed"]),
            mode="markers", name="Flagged Sensor Anomaly",
            marker=dict(color="#ef4444", size=11, symbol="x", line=dict(width=2, color="white"))
        ), row=1, col=1)

    # 2. Pressure Plot
    fig.add_trace(go.Scatter(
        x=df["step"], y=df["pres_raw"],
        mode="lines+markers", name="Raw Pressure (hPa)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=4)
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["pres_imputed"],
        mode="lines", name="Imputed Pressure",
        line=dict(color="#10b981", width=2, dash="dash"),
        showlegend=False
    ), row=2, col=1)

    # 3. Humidity Plot
    fig.add_trace(go.Scatter(
        x=df["step"], y=df["hum_raw"],
        mode="lines+markers", name="Raw Humidity (%)",
        line=dict(color="#8b5cf6", width=2),
        marker=dict(size=4)
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["hum_imputed"],
        mode="lines", name="Imputed Humidity",
        line=dict(color="#10b981", width=2, dash="dash"),
        showlegend=False
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=df["step"], y=df["dew_point"],
        mode="lines", name="Dew Point (Td °C)",
        line=dict(color="#ec4899", width=1.5, dash="dashdot")
    ), row=3, col=1)

    fig.update_layout(
        height=580,
        margin=dict(l=40, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)


# Bottom Row: Explainable AI & Sensor Health Radar
st.markdown("---")
col_xai, col_health = st.columns([3, 2])

with col_xai:
    st.subheader("🧠 Explainable AI (XAI) & Root Cause Reasoning")
    if latest:
        xai_info = latest["xai"]
        st.markdown(f"""
        <div class="diagnostic-box">
            <b>Diagnostic Report:</b><br>{xai_info['explanation']}
        </div>
        """, unsafe_allow_html=True)

        # Feature Attribution Bar Chart
        attributions = xai_info["attributions"]
        attrib_df = pd.DataFrame([
            {"Feature": k.replace("_", " ").title(), "Attribution (%)": round(v * 100, 1)}
            for k, v in attributions.items()
        ]).sort_values(by="Attribution (%)", ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=attrib_df["Attribution (%)"],
            y=attrib_df["Feature"],
            orientation='h',
            marker=dict(
                color=attrib_df["Attribution (%)"],
                colorscale="Viridis"
            )
        ))
        fig_bar.update_layout(
            title="Feature Attribution Importance (%) — fast heuristic, not SHAP (see benchmark/run_shap_analysis.py for real SHAP)",
            height=280,
            margin=dict(l=20, r=20, t=35, b=20),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col_health:
    st.subheader("🛡️ Predictive Sensor Health Radar")
    if latest:
        health = latest["sensor_health"]
        h_score = health["overall_health_score"]
        rul_days = health["estimated_rul_days"]
        status = health["maintenance_status"]

        # Gauge Chart for Overall Health
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=h_score,
            title={'text': f"Health Index: {status}"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#10b981" if h_score > 75 else ("#f59e0b" if h_score > 50 else "#ef4444")},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.2)"},
                    {'range': [50, 75], 'color': "rgba(245, 158, 11, 0.2)"},
                    {'range': [75, 100], 'color': "rgba(16, 185, 129, 0.2)"}
                ]
            }
        ))
        fig_gauge.update_layout(
            height=220,
            margin=dict(l=20, r=20, t=30, b=10),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.4)"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(f"**Estimated Remaining Useful Life (RUL)**: `{rul_days} Days`")
        st.caption(f"Advisory: {health['advisory']}")

        # Sub-sensor health bars
        sub_scores = health["sensor_scores"]
        st.progress(int(sub_scores["temperature"]), text=f"Temperature Sensor: {sub_scores['temperature']}%")
        st.progress(int(sub_scores["pressure"]), text=f"Barometer Sensor: {sub_scores['pressure']}%")
        st.progress(int(sub_scores["humidity"]), text=f"Hygrometer Sensor: {sub_scores['humidity']}%")


# Anomaly Audit Log & CSV Export
st.markdown("---")
st.subheader("📑 Flagged Anomaly Audit Log")

if st.session_state.audit_log:
    audit_df = pd.DataFrame(st.session_state.audit_log)
    st.dataframe(audit_df, use_container_width=True)
    
    csv_data = audit_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Audit Log (CSV)",
        data=csv_data,
        file_name="skyguard_anomaly_audit_log.csv",
        mime="text/csv"
    )
else:
    st.info("No anomalies flagged yet in this session. Use the Dynamic Anomaly Injection Sandbox above to test!")


# Auto-refresh if live streaming is active
if st.session_state.is_running:
    time.sleep(sim_speed)
    st.rerun()
