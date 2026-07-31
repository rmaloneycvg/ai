/**
 * Jaeger HTTP API client.
 *
 * Requires environment variables:
 *   JAEGER_URL — e.g., http://localhost:16686
 *   JAEGER_AUTH_TOKEN — (optional) Bearer token for authenticated instances
 *
 * Supports both Jaeger Query API and Jaeger OTLP/gRPC via HTTP JSON API.
 */

export interface JaegerConfig {
  baseUrl: string;
  authToken?: string;
}

export function getConfig(): JaegerConfig {
  const baseUrl = process.env.JAEGER_URL;
  if (!baseUrl) throw new Error("JAEGER_URL environment variable is required");

  return {
    baseUrl: baseUrl.replace(/\/$/, ""),
    authToken: process.env.JAEGER_AUTH_TOKEN,
  };
}

// ─── Trace Types ────────────────────────────────────────────────

export interface JaegerTrace {
  traceID: string;
  spans: JaegerSpan[];
  processes: Record<string, JaegerProcess>;
  warnings?: string[];
}

export interface JaegerSpan {
  traceID: string;
  spanID: string;
  parentSpanID?: string;
  operationName: string;
  references: JaegerReference[];
  startTime: number; // microseconds since epoch
  duration: number; // microseconds
  tags: JaegerTag[];
  logs: JaegerLog[];
  processID: string;
  warnings?: string[];
}

export interface JaegerReference {
  refType: "CHILD_OF" | "FOLLOWS_FROM";
  traceID: string;
  spanID: string;
}

export interface JaegerTag {
  key: string;
  type: "string" | "bool" | "int64" | "float64" | "binary";
  value: string | boolean | number;
}

export interface JaegerLog {
  timestamp: number;
  fields: JaegerTag[];
}

export interface JaegerProcess {
  serviceName: string;
  tags: JaegerTag[];
}

export interface JaegerSearchResult {
  data: JaegerTrace[];
  total: number;
  limit: number;
  offset: number;
  errors?: JaegerError[];
}

export interface JaegerError {
  code: number;
  msg: string;
  traceID?: string;
}

export interface JaegerService {
  data: string[];
  total: number;
  limit: number;
  offset: number;
  errors?: JaegerError[];
}

export interface JaegerOperation {
  data: string[];
  total: number;
  limit: number;
  offset: number;
  errors?: JaegerError[];
}

export interface JaegerDependencyLink {
  parent: string;
  child: string;
  callCount: number;
}

export interface JaegerDependencyResult {
  data: JaegerDependencyLink[];
  total: number;
  limit: number;
  offset: number;
  errors?: JaegerError[];
}

export async function jaegerFetch<T = unknown>(
  path: string,
  params?: Record<string, string | string[]>,
  config?: JaegerConfig
): Promise<T> {
  const { baseUrl, authToken } = config ?? getConfig();

  const url = new URL(`${baseUrl}/api${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else {
        url.searchParams.set(key, value);
      }
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
    throw new Error(`Jaeger API error ${response.status}: ${errorBody}`);
  }

  return response.json() as Promise<T>;
}
