import { useQuery } from "@tanstack/react-query";

import {
  getMLRiskHealth,
  getMLRiskIncidents,
  getMLRiskObservations,
  getMLRiskSummary,
} from "./mlRisk.api";

export const mlRiskKeys = {
  all: ["ml-risk"] as const,
  summary: () => [...mlRiskKeys.all, "summary"] as const,
  observations: (limit: number) =>
    [...mlRiskKeys.all, "observations", limit] as const,
  incidents: (limit: number) =>
    [...mlRiskKeys.all, "incidents", limit] as const,
  health: () => [...mlRiskKeys.all, "health"] as const,
};

export function useMLRiskSummary() {
  return useQuery({
    queryKey: mlRiskKeys.summary(),
    queryFn: getMLRiskSummary,
    refetchInterval: 60_000,
  });
}

export function useMLRiskObservations(limit = 15) {
  return useQuery({
    queryKey: mlRiskKeys.observations(limit),
    queryFn: () => getMLRiskObservations(limit),
    refetchInterval: 60_000,
  });
}

export function useMLRiskIncidents(limit = 10) {
  return useQuery({
    queryKey: mlRiskKeys.incidents(limit),
    queryFn: () => getMLRiskIncidents(limit),
    refetchInterval: 60_000,
  });
}

export function useMLRiskHealth() {
  return useQuery({
    queryKey: mlRiskKeys.health(),
    queryFn: getMLRiskHealth,
    refetchInterval: 60_000,
  });
}
