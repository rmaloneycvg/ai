/**
 * Grafana mutation operations.
 *
 * Provides annotation creation, alert silencing, and dashboard management.
 */

import {
  grafanaFetch,
  type GrafanaConfig,
  type CreateAnnotationRequest,
} from "./client.js";

// ─── Annotations (Release Markers) ─────────────────────────────

export async function createDeploymentAnnotation(
  release: string,
  environment: string,
  dashboardUID?: string,
  config?: GrafanaConfig
): Promise<{ id: number; message: string }> {
  const annotation: CreateAnnotationRequest = {
    dashboardUID,
    time: Date.now(),
    text: `Deployed ${release} to ${environment}`,
    tags: ["deployment", `release:${release}`, `env:${environment}`],
  };
  return grafanaFetch<{ id: number; message: string }>(
    "/annotations",
    { method: "POST", body: annotation },
    config
  );
}

// ─── Alert Silencing ────────────────────────────────────────────

export interface CreateSilenceRequest {
  matchers: Array<{
    name: string;
    value: string;
    isRegex: boolean;
    isEqual: boolean;
  }>;
  startsAt: string;
  endsAt: string;
  createdBy: string;
  comment: string;
}

export async function createAlertSilence(
  request: CreateSilenceRequest,
  config?: GrafanaConfig
): Promise<{ silenceID: string }> {
  return grafanaFetch<{ silenceID: string }>(
    "/alertmanager/grafana/api/v2/silences",
    { method: "POST", body: request },
    config
  );
}

export async function deleteAlertSilence(
  silenceId: string,
  config?: GrafanaConfig
): Promise<void> {
  await grafanaFetch(
    `/alertmanager/grafana/api/v2/silence/${encodeURIComponent(silenceId)}`,
    { method: "DELETE" },
    config
  );
}
