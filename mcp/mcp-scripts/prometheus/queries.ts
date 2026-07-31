/**
 * Prometheus query operations.
 *
 * Provides instant queries, range queries, metric exploration,
 * alert status, and Kiro-specific telemetry helpers.
 */

import {
  promFetch,
  type PrometheusConfig,
  type PrometheusResult,
  type PrometheusSeriesResult,
  type PrometheusLabelResult,
  type PrometheusAlertResult,
  type PrometheusRuleResult,
} from "./client.js";

// ─── Instant Query ──────────────────────────────────────────────

export async function instantQuery(
  query: string,
  time?: string,
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const params: Record<string, string> = { query };
  if (time) params.time = time;
  return promFetch<PrometheusResult>("/query", params, config);
}

// ─── Range Query ────────────────────────────────────────────────

export async function rangeQuery(
  query: string,
  start: string,
  end: string,
  step: string,
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  return promFetch<PrometheusResult>(
    "/query_range",
    { query, start, end, step },
    config
  );
}

// ─── Metric Discovery ───────────────────────────────────────────

export async function listMetrics(
  match?: string,
  config?: PrometheusConfig
): Promise<PrometheusLabelResult> {
  const params: Record<string, string> = {};
  if (match) params["match[]"] = match;
  return promFetch<PrometheusLabelResult>("/label/__name__/values", params, config);
}

export async function listSeries(
  match: string[],
  start?: string,
  end?: string,
  config?: PrometheusConfig
): Promise<PrometheusSeriesResult> {
  const params: Record<string, string> = {};
  // Prometheus expects match[] repeated — we encode it manually
  const url = new URL("placeholder://unused");
  match.forEach((m) => url.searchParams.append("match[]", m));
  if (start) url.searchParams.set("start", start);
  if (end) url.searchParams.set("end", end);

  // Override with direct path construction since promFetch uses set()
  const { baseUrl, authToken } = (await import("./client.js")).getConfig();
  const finalUrl = `${baseUrl}/api/v1/series?${url.searchParams.toString()}`;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const response = await fetch(finalUrl, { headers });
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Prometheus API error ${response.status}: ${errorBody}`);
  }
  return response.json() as Promise<PrometheusSeriesResult>;
}

export async function listLabelValues(
  label: string,
  config?: PrometheusConfig
): Promise<PrometheusLabelResult> {
  return promFetch<PrometheusLabelResult>(`/label/${encodeURIComponent(label)}/values`, undefined, config);
}

// ─── Alerts ─────────────────────────────────────────────────────

export async function getAlerts(
  config?: PrometheusConfig
): Promise<PrometheusAlertResult> {
  return promFetch<PrometheusAlertResult>("/alerts", undefined, config);
}

export async function getRules(
  config?: PrometheusConfig
): Promise<PrometheusRuleResult> {
  return promFetch<PrometheusRuleResult>("/rules", undefined, config);
}

// ─── Kiro-Specific Queries ──────────────────────────────────────

/**
 * Get feature invocation rates for Kiro-tracked features.
 * Queries: rate(kiro_feature_invocations_total{feature=~"$pattern"}[$window])
 */
export async function kiroFeatureUsage(
  featurePattern: string,
  window: string = "5m",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const query = `rate(kiro_feature_invocations_total{feature=~"${featurePattern}"}[${window}])`;
  return instantQuery(query, undefined, config);
}

/**
 * Get session duration percentiles.
 * Queries: histogram_quantile($quantile, rate(kiro_session_duration_seconds_bucket[$window]))
 */
export async function kiroSessionPerformance(
  quantile: number = 0.95,
  window: string = "5m",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const query = `histogram_quantile(${quantile}, rate(kiro_session_duration_seconds_bucket[${window}]))`;
  return instantQuery(query, undefined, config);
}

/**
 * Get model usage breakdown.
 * Queries: sum by (model) (rate(kiro_model_requests_total[$window]))
 */
export async function kiroModelUsage(
  window: string = "1h",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const query = `sum by (model) (rate(kiro_model_requests_total[${window}]))`;
  return instantQuery(query, undefined, config);
}

/**
 * Get context size distribution.
 * Queries: histogram_quantile($quantile, rate(kiro_context_tokens_bucket[$window]))
 */
export async function kiroContextSize(
  quantile: number = 0.95,
  window: string = "1h",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const query = `histogram_quantile(${quantile}, rate(kiro_context_tokens_bucket[${window}]))`;
  return instantQuery(query, undefined, config);
}

/**
 * Get error rates by service.
 * Queries: sum by (service) (rate(http_requests_total{status=~"5.."}[$window])) / sum by (service) (rate(http_requests_total[$window]))
 */
export async function serviceErrorRates(
  service?: string,
  window: string = "5m",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const serviceFilter = service ? `service="${service}",` : "";
  const query = `sum by (service) (rate(http_requests_total{${serviceFilter}status=~"5.."}[${window}])) / sum by (service) (rate(http_requests_total{${serviceFilter}}[${window}]))`;
  return instantQuery(query, undefined, config);
}

/**
 * Get prompt security alert metrics.
 * Queries: sum by (detection_type) (rate(kiro_prompt_security_detections_total[$window]))
 */
export async function kiroPromptSecurityDetections(
  window: string = "1h",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const query = `sum by (detection_type) (rate(kiro_prompt_security_detections_total[${window}]))`;
  return instantQuery(query, undefined, config);
}

/**
 * Compare metrics across releases.
 * Queries: rate(metric{release=~"$releases"}[$window])
 */
export async function compareReleases(
  metric: string,
  releases: string[],
  window: string = "1h",
  config?: PrometheusConfig
): Promise<PrometheusResult> {
  const releasePattern = releases.join("|");
  const query = `${metric}{release=~"${releasePattern}"}`;
  return rangeQuery(
    query,
    `now-${window}`,
    "now",
    "1m",
    config
  );
}
