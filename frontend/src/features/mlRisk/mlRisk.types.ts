export type RiskLevel = "minimal" | "low" | "medium" | "high";

export interface RiskDistribution {
  minimal: number;
  low: number;
  medium: number;
  high: number;
}

export interface RiskSection {
  rows?: number;
  mean_risk_score?: number;
  high_risk_count?: number;
  medium_risk_count?: number;
  low_risk_count?: number;
  minimal_risk_count?: number;
}

export interface TemporalDetection {
  incident_count?: number;
  incident_distribution?: Record<string, number>;
  incident_risk_distribution?: Record<string, number>;
  authentication_burst_window_seconds?: number;
  authentication_burst_min_failures?: number;
  error_burst_window_seconds?: number;
  error_burst_min_errors?: number;
  activity_burst_window_seconds?: number;
  activity_burst_min_requests?: number;
}

export interface MLRiskSummary {
  model_type: string;
  description: string;
  total_rows: number;
  http_rows: number;
  business_rows: number;
  risk_distribution: RiskDistribution;
  overall: RiskSection;
  http: RiskSection;
  business: RiskSection;
  temporal_detection: TemporalDetection;
}

export interface MLRiskObservation {
  id?: string;
  occurred_at?: string;
  action?: string;
  resource_type?: string;
  method?: string;
  endpoint_normalized?: string;
  endpoint?: string;
  status_code?: number;
  risk_score?: number;
  risk_level?: RiskLevel;
  risk_reasons?: string[];
  behavioral_anomaly_signal?: number;
  [key: string]: unknown;
}

export interface MLRiskIncident {
  incident_id: string;
  incident_type: string;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  event_count: number;
  risk_score: number;
  risk_level: RiskLevel;
  reason: string;
  endpoint?: string;
  failure_count?: number;
  error_count?: number;
}

export interface MLRiskObservationsResponse {
  items: MLRiskObservation[];
  count: number;
}

export interface MLRiskIncidentsResponse {
  items: MLRiskIncident[];
  count: number;
}

export interface MLRiskConfiguration {
  weights: Record<string, number>;
  risk_levels: Record<string, string>;
  behavioral_anomaly: Record<string, unknown>;
  temporal_detection: Record<string, unknown>;
}

export interface MLRiskHealth {
  available: boolean;
  report_path: string;
  message: string;
}
