/**
 * Grafana query operations.
 *
 * Provides dashboard discovery, panel query execution, annotation management,
 * datasource listing, dashboard version history, and report generation.
 */

import {
  grafanaFetch,
  type GrafanaConfig,
  type GrafanaDashboard,
  type GrafanaDashboardDetail,
  type GrafanaAnnotation,
  type CreateAnnotationRequest,
  type GrafanaDatasource,
  type GrafanaDashboardVersion,
} from "./client.js";

// ─── Dashboard Discovery ────────────────────────────────────────

export async function searchDashboards(
  query?: string,
  tags?: string[],
  config?: GrafanaConfig
): Promise<GrafanaDashboard[]> {
  const params: Record<string, string> = { type: "dash-db" };
  if (query) params.query = query;
  if (tags?.length) params.tag = tags.join(",");
  return grafanaFetch<GrafanaDashboard[]>("/search", { params }, config);
}

export async function getDashboard(
  uid: string,
  config?: GrafanaConfig
): Promise<GrafanaDashboardDetail> {
  return grafanaFetch<GrafanaDashboardDetail>(`/dashboards/uid/${encodeURIComponent(uid)}`, undefined, config);
}

// ─── Dashboard Versions ─────────────────────────────────────────

export async function getDashboardVersions(
  dashboardId: number,
  limit: number = 10,
  config?: GrafanaConfig
): Promise<GrafanaDashboardVersion[]> {
  return grafanaFetch<GrafanaDashboardVersion[]>(
    `/dashboards/id/${dashboardId}/versions`,
    { params: { limit: String(limit) } },
    config
  );
}

export async function compareDashboardVersions(
  dashboardId: number,
  baseVersion: number,
  newVersion: number,
  config?: GrafanaConfig
): Promise<unknown> {
  return grafanaFetch(
    `/dashboards/id/${dashboardId}/versions/${baseVersion}/diff`,
    {
      method: "POST",
      body: { diffType: "json", version: newVersion },
    },
    config
  );
}

// ─── Panel Query (Datasource Proxy) ────────────────────────────

export interface QueryDataRequest {
  queries: Array<{
    refId: string;
    datasource: { type: string; uid: string };
    expr?: string; // PromQL
    queryType?: string;
    [key: string]: unknown;
  }>;
  from: string; // "now-1h"
  to: string; // "now"
}

export interface QueryDataResponse {
  results: Record<
    string,
    {
      frames: Array<{
        schema: { fields: Array<{ name: string; type: string }> };
        data: { values: unknown[][] };
      }>;
      error?: string;
    }
  >;
}

export async function queryDatasource(
  request: QueryDataRequest,
  config?: GrafanaConfig
): Promise<QueryDataResponse> {
  return grafanaFetch<QueryDataResponse>(
    "/ds/query",
    { method: "POST", body: request },
    config
  );
}

// ─── Annotations ────────────────────────────────────────────────

export async function getAnnotations(
  dashboardUID?: string,
  from?: number,
  to?: number,
  tags?: string[],
  limit?: number,
  config?: GrafanaConfig
): Promise<GrafanaAnnotation[]> {
  const params: Record<string, string> = {};
  if (dashboardUID) params.dashboardUID = dashboardUID;
  if (from) params.from = String(from);
  if (to) params.to = String(to);
  if (tags?.length) params.tags = tags.join(",");
  if (limit) params.limit = String(limit);
  return grafanaFetch<GrafanaAnnotation[]>("/annotations", { params }, config);
}

export async function createAnnotation(
  annotation: CreateAnnotationRequest,
  config?: GrafanaConfig
): Promise<{ id: number; message: string }> {
  return grafanaFetch<{ id: number; message: string }>(
    "/annotations",
    { method: "POST", body: annotation },
    config
  );
}

// ─── Datasources ────────────────────────────────────────────────

export async function listDatasources(
  config?: GrafanaConfig
): Promise<GrafanaDatasource[]> {
  return grafanaFetch<GrafanaDatasource[]>("/datasources", undefined, config);
}

export async function getDatasource(
  uid: string,
  config?: GrafanaConfig
): Promise<GrafanaDatasource> {
  return grafanaFetch<GrafanaDatasource>(`/datasources/uid/${encodeURIComponent(uid)}`, undefined, config);
}

// ─── Report Generation Helpers ──────────────────────────────────

/**
 * Generate a release comparison report by querying panels across versions.
 */
export async function generateReleaseReport(
  dashboardUid: string,
  currentRelease: string,
  previousRelease: string,
  timeRange: { from: string; to: string },
  config?: GrafanaConfig
): Promise<ReleaseReport> {
  const dashboard = await getDashboard(dashboardUid, config);
  const datasources = await listDatasources(config);

  // Find Prometheus datasource
  const promDs = datasources.find((ds) => ds.type === "prometheus");
  if (!promDs) throw new Error("No Prometheus datasource found in Grafana");

  // Extract PromQL from panels and execute for each release
  const panels = dashboard.dashboard.panels ?? [];
  const panelResults: PanelComparisonResult[] = [];

  for (const panel of panels) {
    if (!panel.targets?.length) continue;

    for (const target of panel.targets) {
      if (!target.expr) continue;

      // Query for current release
      const currentExpr = target.expr.replace(/release="[^"]*"/, `release="${currentRelease}"`);
      const previousExpr = target.expr.replace(/release="[^"]*"/, `release="${previousRelease}"`);

      try {
        const [currentResult, previousResult] = await Promise.all([
          queryDatasource(
            {
              queries: [{ refId: "A", datasource: { type: "prometheus", uid: promDs.uid }, expr: currentExpr }],
              from: timeRange.from,
              to: timeRange.to,
            },
            config
          ),
          queryDatasource(
            {
              queries: [{ refId: "A", datasource: { type: "prometheus", uid: promDs.uid }, expr: previousExpr }],
              from: timeRange.from,
              to: timeRange.to,
            },
            config
          ),
        ]);

        panelResults.push({
          panelTitle: panel.title,
          query: target.expr,
          currentRelease: { release: currentRelease, data: currentResult.results },
          previousRelease: { release: previousRelease, data: previousResult.results },
        });
      } catch {
        panelResults.push({
          panelTitle: panel.title,
          query: target.expr,
          error: "Query execution failed",
        });
      }
    }
  }

  return {
    dashboardTitle: dashboard.dashboard.title,
    dashboardUrl: dashboard.meta.url,
    timeRange,
    currentRelease,
    previousRelease,
    panels: panelResults,
    generatedAt: new Date().toISOString(),
  };
}

export interface ReleaseReport {
  dashboardTitle: string;
  dashboardUrl: string;
  timeRange: { from: string; to: string };
  currentRelease: string;
  previousRelease: string;
  panels: PanelComparisonResult[];
  generatedAt: string;
}

export interface PanelComparisonResult {
  panelTitle: string;
  query: string;
  currentRelease?: { release: string; data: unknown };
  previousRelease?: { release: string; data: unknown };
  error?: string;
}

/**
 * Generate a Kiro telemetry summary report.
 */
export async function generateKiroTelemetryReport(
  timeRange: { from: string; to: string },
  config?: GrafanaConfig
): Promise<KiroTelemetryReport> {
  const datasources = await listDatasources(config);
  const promDs = datasources.find((ds) => ds.type === "prometheus");
  if (!promDs) throw new Error("No Prometheus datasource found in Grafana");

  const queries = [
    { name: "featureUsage", expr: 'topk(10, sum by (feature) (rate(kiro_feature_invocations_total[1h])))' },
    { name: "modelUsage", expr: 'sum by (model) (rate(kiro_model_requests_total[1h]))' },
    { name: "contextSizeP95", expr: 'histogram_quantile(0.95, rate(kiro_context_tokens_bucket[1h]))' },
    { name: "sessionDurationP95", expr: 'histogram_quantile(0.95, rate(kiro_session_duration_seconds_bucket[1h]))' },
    { name: "securityDetections", expr: 'sum by (detection_type) (rate(kiro_prompt_security_detections_total[1h]))' },
    { name: "errorRate", expr: 'sum(rate(kiro_session_errors_total[1h])) / sum(rate(kiro_session_duration_seconds_count[1h]))' },
  ];

  const results: Record<string, unknown> = {};

  for (const q of queries) {
    try {
      const result = await queryDatasource(
        {
          queries: [{ refId: "A", datasource: { type: "prometheus", uid: promDs.uid }, expr: q.expr }],
          from: timeRange.from,
          to: timeRange.to,
        },
        config
      );
      results[q.name] = result.results;
    } catch {
      results[q.name] = { error: "Query failed" };
    }
  }

  return {
    timeRange,
    metrics: results,
    generatedAt: new Date().toISOString(),
  };
}

export interface KiroTelemetryReport {
  timeRange: { from: string; to: string };
  metrics: Record<string, unknown>;
  generatedAt: string;
}
