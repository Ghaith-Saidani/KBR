import api from "../../services/api";

import type {
  MLRiskConfiguration,
  MLRiskHealth,
  MLRiskIncidentsResponse,
  MLRiskObservationsResponse,
  MLRiskSummary,
} from "./mlRisk.types";

export async function getMLRiskSummary(): Promise<MLRiskSummary> {
  const response = await api.get<MLRiskSummary>("/admin/ml/risk/summary");
  return response.data;
}

export async function getMLRiskObservations(
  limit = 15,
): Promise<MLRiskObservationsResponse> {
  const response = await api.get<MLRiskObservationsResponse>(
    "/admin/ml/risk/observations",
    { params: { limit } },
  );
  return response.data;
}

export async function getMLRiskIncidents(
  limit = 10,
): Promise<MLRiskIncidentsResponse> {
  const response = await api.get<MLRiskIncidentsResponse>(
    "/admin/ml/risk/incidents",
    { params: { limit } },
  );
  return response.data;
}

export async function getMLRiskConfiguration(): Promise<MLRiskConfiguration> {
  const response = await api.get<MLRiskConfiguration>(
    "/admin/ml/risk/configuration",
  );
  return response.data;
}

export async function getMLRiskHealth(): Promise<MLRiskHealth> {
  const response = await api.get<MLRiskHealth>("/admin/ml/risk/health");
  return response.data;
}
