"""
SkyGuard AI - Central Configuration & Meteorological Standards
Includes World Meteorological Organization (WMO No. 8) Quality Control limits,
Thermodynamic psychrometric constants, and AWS Station Profiles.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SensorLimits(BaseModel):
    min_val: float
    max_val: float
    max_step_1min: float  # Maximum physical rate of change per minute
    max_step_5min: float  # Maximum physical rate of change per 5 minutes


class StationProfile(BaseModel):
    station_id: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    elevation_m: float
    base_temp_c: float
    temp_diurnal_range_c: float
    base_pressure_hpa: float
    base_humidity_pct: float
    humidity_diurnal_range_pct: float


class SystemConfig(BaseModel):
    # Streaming parameters
    sampling_interval_sec: float = 1.0
    sliding_window_size: int = 60  # 60 timesteps in temporal memory
    
    # Thermodynamic Magnus-Tetens coefficients for water vapor (above 0°C)
    # e_s(T) = a * exp((b * T) / (c + T))
    magnus_a_hpa: float = 6.112
    magnus_b: float = 17.67
    magnus_c: float = 243.5
    
    # Sub-zero ice Magnus coefficients (below 0°C)
    magnus_ice_b: float = 22.5
    magnus_ice_c: float = 273.0

    # WMO Physical Limit Quality Control Boundaries
    limits: Dict[str, SensorLimits] = {
        "temperature": SensorLimits(
            min_val=-40.0,
            max_val=60.0,
            max_step_1min=3.0,   # WMO: >3°C/min is extreme/unphysical in standard conditions
            max_step_5min=6.0
        ),
        "pressure": SensorLimits(
            min_val=750.0,       # Mountainous/High-altitude baseline to deep low
            max_val=1080.0,      # Extreme Siberian high
            max_step_1min=2.0,   # Rapid barometric pressure jump (hPa/min)
            max_step_5min=4.0
        ),
        "humidity": SensorLimits(
            min_val=0.0,
            max_val=100.0,
            max_step_1min=15.0,  # % per minute
            max_step_5min=30.0
        )
    }

    # Station Metadata Directory
    stations: Dict[str, StationProfile] = {
        "AWS_ALPHA_MOUNTAIN": StationProfile(
            station_id="AWS_ALPHA_MOUNTAIN",
            name="Alpha Ridge (Highland Station)",
            station_type="Mountain",
            latitude=34.125,
            longitude=-117.850,
            elevation_m=2150.0,
            base_temp_c=12.0,
            temp_diurnal_range_c=16.0,
            base_pressure_hpa=785.0,
            base_humidity_pct=45.0,
            humidity_diurnal_range_pct=30.0
        ),
        "AWS_BETA_COASTAL": StationProfile(
            station_id="AWS_BETA_COASTAL",
            name="Beta Coastline (Marine Station)",
            station_type="Coastal",
            latitude=18.922,
            longitude=72.834,
            elevation_m=10.0,
            base_temp_c=27.0,
            temp_diurnal_range_c=7.0,
            base_pressure_hpa=1012.0,
            base_humidity_pct=82.0,
            humidity_diurnal_range_pct=15.0
        ),
        "AWS_GAMMA_URBAN": StationProfile(
            station_id="AWS_GAMMA_URBAN",
            name="Gamma Metropole (Urban Station)",
            station_type="Urban",
            latitude=28.613,
            longitude=77.209,
            elevation_m=216.0,
            base_temp_c=25.0,
            temp_diurnal_range_c=14.0,
            base_pressure_hpa=990.0,
            base_humidity_pct=60.0,
            humidity_diurnal_range_pct=28.0
        ),
        "AWS_DELTA_DESERT": StationProfile(
            station_id="AWS_DELTA_DESERT",
            name="Delta Dunes (Arid Desert Station)",
            station_type="Desert",
            latitude=26.915,
            longitude=70.908,
            elevation_m=220.0,
            base_temp_c=34.0,
            temp_diurnal_range_c=22.0,
            base_pressure_hpa=995.0,
            base_humidity_pct=22.0,
            humidity_diurnal_range_pct=16.0
        )
    }

    # Anomaly Ensemble Weights
    weight_physics: float = 0.35
    weight_autoencoder: float = 0.25
    weight_isolation_forest: float = 0.20
    weight_statistical_zscore: float = 0.20

    # Severity Thresholds (Confidence Score 0.0 to 1.0)
    thresh_low: float = 0.35
    thresh_medium: float = 0.60
    thresh_high: float = 0.80
    thresh_critical: float = 0.90


config = SystemConfig()
