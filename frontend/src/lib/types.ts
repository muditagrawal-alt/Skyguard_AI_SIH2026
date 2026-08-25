// Types mirroring the SkyGuard backend's processed telemetry packet
// (backend/app/core/pipeline.py -> process_reading) and station metadata
// (backend/app/main.py -> GET /api/stations). These are the wire shapes the
// live dashboard consumes; the mock objects in components/data.ts remain the
// offline fallback and share the UI-level `Status` type from there.

export type Triple = {
  temperature: number | null;
  pressure: number | null;
  humidity: number | null;
};

export type PhysicsResult = {
  dew_point_c: number | null;
  sat_vapor_pressure_hpa: number | null;
  actual_vapor_pressure_hpa: number | null;
  vpd_hpa: number | null;
  dew_point_depression_c: number | null;
  is_physics_violation: boolean;
  physics_anomaly_score: number;
  violations: string[];
};

export type StatisticalResult = {
  z_scores: Record<string, number>;
  cusum_scores: Record<string, number>;
  is_flatline: boolean;
  flatline_flags: string[];
  stat_anomaly_score: number;
  drift_flags: string[];
};

export type IsolationForestResult = {
  isolation_score: number;
  isolation_anomaly_prob: number;
  is_multivariate_outlier: boolean;
};

export type AutoencoderResult = {
  reconstruction_error?: number;
  autoencoder_anomaly_score?: number;
  is_sequence_anomaly?: boolean;
  [key: string]: unknown;
};

export type Severity = "NORMAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type EnsembleResult = {
  is_anomaly: boolean;
  confidence_score: number;
  severity: Severity;
  component_scores: {
    physics: number;
    autoencoder: number;
    isolation_forest: number;
    statistical: number;
  };
};

export type RootCauseResult = {
  fault_type: string;
  fault_category: string;
  confidence: number;
  is_genuine_weather: boolean;
};

export type SpatialResult = {
  other_stations_reporting: number;
  other_stations_anomalous: number;
  is_isolated_event: boolean | null;
  is_corroborated_event: boolean;
};

// xai.attributions is a normalized map (values sum to ~1) over these 8 features.
export type Attributions = {
  temperature: number;
  pressure: number;
  humidity: number;
  delta_temp: number;
  delta_pres: number;
  delta_hum: number;
  vpd: number;
  dew_point_depression: number;
};

export type XaiResult = {
  attributions: Attributions;
  explanation: string;
};

export type ImputedResult = Triple & {
  is_imputed: boolean;
  imputation_reason: string;
};

export type SensorHealthResult = {
  overall_health_score: number;
  sensor_scores: {
    temperature: number;
    pressure: number;
    humidity: number;
  };
  maintenance_status: string;
  advisory: string;
  estimated_rul_days: number;
  fault_rate_pct: number;
  flatline_count: number;
  total_observations: number;
};

export type ProcessedPacket = {
  station_id: string;
  station_name: string;
  station_type: string;
  timestamp: string;
  simulated_hour: number;
  raw: Triple;
  clean_ground_truth: Triple;
  physics: PhysicsResult;
  statistical: StatisticalResult;
  isolation_forest: IsolationForestResult;
  autoencoder: AutoencoderResult;
  ensemble: EnsembleResult;
  root_cause: RootCauseResult;
  spatial: SpatialResult;
  xai: XaiResult;
  imputed: ImputedResult;
  sensor_health: SensorHealthResult;
  injected_anomalies: string[];
  data_source?: string;
};

// GET /api/stations entry (StationProfile + has_real_data flag).
export type StationMeta = {
  station_id: string;
  name: string;
  station_type: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  base_temp_c: number;
  temp_diurnal_range_c: number;
  base_pressure_hpa: number;
  base_humidity_pct: number;
  humidity_diurnal_range_pct: number;
  has_real_data: boolean;
};

export type DataSource = "synthetic" | "real";

export type AnomalyType =
  | "spike"
  | "flatline"
  | "drift"
  | "physics_violation"
  | "packet_loss"
  | "thunderstorm";

export type SensorTarget = "temperature" | "pressure" | "humidity" | "all";
