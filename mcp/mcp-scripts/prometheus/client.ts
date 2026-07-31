/**
 * Prometheus HTTP API client.
 *
 * Requires environment variables:
 *   PROMETHEUS_URL — e.g., http://localhost:9090
 *   PROMETHEUS_AUTH_TOKEN — (optional) Bearer token for authenticated instances
 */

export interface PrometheusConfig {
  baseUrl: string;
  authToken?: string;
}

export function getConfig(): PrometheusConfig {
  const baseUrl = process.env.PROMETHEUS_URL;
  if (!baseUrl) throw new Error("PROMETHEUS_URL environment variable is required");

  return {
    baseUrl: baseUrl.replace(/\/$/, ""),
    authToken: process.env.PROMETHEUS_AUTH_TOKEN,
  };
}

export interface PrometheusResult {
  status: "success" | "error";
  data?: {
    resultType: "matrix" | "vector" | "scalar" | "string";
    result: PrometheusMetricResult[];
  };
  error?: string;
  errorType?: string;
  warnings?: string[];
}

export interface PrometheusMetricResult {
  metric: Record<string, string>;
  value?: [number, string]; // [timestamp, value] for instant queries
  values?: Array<[number, string]>; // for range queries
}

export interface PrometheusSeriesResult {
  status: "success" | "error";
  data?: Array<Record<string, string>>;
  error?: string;
}

export interface PrometheusLabelResult {
  status: "success" | "error";
  data?: string[];
  error?: string;
}

export interface PrometheusAlertResult {
  status: "success" | "error";
  data?: {
    alerts: PrometheusAlert[];
  };
  error?: string;
}

export interface PrometheusAlert {
  labels: Record<string, string>;
  annotations: Record<string, string>;
  state: "firing" | "pending" | "inactive";
  activeAt: string;
  value: string;
}

export interface PrometheusRuleResult {
  status: "success" | "error";
  data?: {
    groups: PrometheusRuleGroup[];
  };
  error?: string;
}

export interface PrometheusRuleGroup {
  name: string;
  file: string;
  rules: PrometheusRule[];
}

export interface PrometheusRule {
  name: string;
  query: string;
  type: "alerting" | "recording";
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
  state?: "firing" | "pending" | "inactive";
  health: "ok" | "err" | "unknown";
  lastError?: string;
}

export async function promFetch<T = unknown>(
  path: string,
  params?: Record<string, string>,
  config?: PrometheusConfig
): Promise<T> {
  const { baseUrl, authToken } = config ?? getConfig();

  const url = new URL(`${baseUrl}/api/v1${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(url.toString(), { headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Prometheus API error ${response.status}: ${errorBody}`);
  }

  return response.json() as Promise<T>;
}
