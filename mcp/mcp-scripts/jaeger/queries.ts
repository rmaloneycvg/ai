/**
 * Jaeger query operations.
 *
 * Provides trace search, span analysis, service dependency graphs,
 * and Kiro-specific trace analysis helpers.
 */

import {
  jaegerFetch,
  type JaegerConfig,
  type JaegerSearchResult,
  type JaegerService,
  type JaegerOperation,
  type JaegerDependencyResult,
  type JaegerTrace,
  type JaegerSpan,
} from "./client.js";

// ─── Service Discovery ──────────────────────────────────────────

export async function listServices(
  config?: JaegerConfig
): Promise<JaegerService> {
  return jaegerFetch<JaegerService>("/services", undefined, config);
}

export async function listOperations(
  service: string,
  config?: JaegerConfig
): Promise<JaegerOperation> {
  return jaegerFetch<JaegerOperation>(
    `/services/${encodeURIComponent(service)}/operations`,
    undefined,
    config
  );
}

// ─── Trace Search ───────────────────────────────────────────────

export interface TraceSearchParams {
  service: string;
  operation?: string;
  tags?: Record<string, string>;
  minDuration?: string; // e.g., "1s", "500ms"
  maxDuration?: string;
  start?: string; // microseconds since epoch
  end?: string;
  limit?: number;
}

export async function searchTraces(
  params: TraceSearchParams,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  const queryParams: Record<string, string> = {
    service: params.service,
    limit: String(params.limit ?? 20),
  };

  if (params.operation) queryParams.operation = params.operation;
  if (params.minDuration) queryParams.minDuration = params.minDuration;
  if (params.maxDuration) queryParams.maxDuration = params.maxDuration;
  if (params.start) queryParams.start = params.start;
  if (params.end) queryParams.end = params.end;

  if (params.tags) {
    // Jaeger expects tags as JSON: {"key": "value"}
    queryParams.tags = JSON.stringify(params.tags);
  }

  return jaegerFetch<JaegerSearchResult>("/traces", queryParams, config);
}

// ─── Trace Detail ───────────────────────────────────────────────

export async function getTrace(
  traceId: string,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return jaegerFetch<JaegerSearchResult>(
    `/traces/${encodeURIComponent(traceId)}`,
    undefined,
    config
  );
}

// ─── Service Dependencies ───────────────────────────────────────

export async function getDependencies(
  endTs?: string,
  lookback?: string,
  config?: JaegerConfig
): Promise<JaegerDependencyResult> {
  const params: Record<string, string> = {};
  if (endTs) params.endTs = endTs;
  if (lookback) params.lookback = lookback;
  return jaegerFetch<JaegerDependencyResult>("/dependencies", params, config);
}

// ─── Trace Analysis Helpers ─────────────────────────────────────

/**
 * Extract a flat summary of spans from a trace, useful for bottleneck analysis.
 */
export function summarizeTrace(trace: JaegerTrace): TraceSummary {
  const spans = trace.spans.sort((a, b) => a.startTime - b.startTime);
  const totalDuration = spans.length > 0
    ? Math.max(...spans.map((s) => s.startTime + s.duration)) - spans[0].startTime
    : 0;

  const serviceBreakdown: Record<string, { count: number; totalDuration: number }> = {};
  const slowSpans: SpanSummary[] = [];

  for (const span of spans) {
    const service = trace.processes[span.processID]?.serviceName ?? "unknown";

    if (!serviceBreakdown[service]) {
      serviceBreakdown[service] = { count: 0, totalDuration: 0 };
    }
    serviceBreakdown[service].count++;
    serviceBreakdown[service].totalDuration += span.duration;

    // Track spans > 10% of total duration as "slow"
    if (span.duration > totalDuration * 0.1) {
      slowSpans.push({
        operationName: span.operationName,
        service,
        durationMs: span.duration / 1000,
        tags: Object.fromEntries(span.tags.map((t) => [t.key, String(t.value)])),
      });
    }
  }

  return {
    traceId: trace.traceID,
    totalDurationMs: totalDuration / 1000,
    spanCount: spans.length,
    serviceBreakdown,
    slowSpans: slowSpans.sort((a, b) => b.durationMs - a.durationMs),
    errors: spans.filter((s) => s.tags.some((t) => t.key === "error" && t.value === true)),
  };
}

export interface TraceSummary {
  traceId: string;
  totalDurationMs: number;
  spanCount: number;
  serviceBreakdown: Record<string, { count: number; totalDuration: number }>;
  slowSpans: SpanSummary[];
  errors: JaegerSpan[];
}

export interface SpanSummary {
  operationName: string;
  service: string;
  durationMs: number;
  tags: Record<string, string>;
}

// ─── Kiro-Specific Queries ──────────────────────────────────────

/**
 * Find Kiro sessions that exceeded a duration threshold.
 */
export async function kiroSlowSessions(
  minDuration: string = "5s",
  limit: number = 10,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return searchTraces(
    {
      service: "kiro-session-handler",
      minDuration,
      limit,
      tags: { "kiro.session.type": "command" },
    },
    config
  );
}

/**
 * Find Kiro sessions by command type.
 */
export async function kiroSessionsByCommand(
  commandType: string,
  limit: number = 20,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return searchTraces(
    {
      service: "kiro-session-handler",
      limit,
      tags: { "kiro.command.type": commandType },
    },
    config
  );
}

/**
 * Find traces by Kiro session ID.
 */
export async function kiroSessionTrace(
  sessionId: string,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return searchTraces(
    {
      service: "kiro-session-handler",
      limit: 1,
      tags: { "kiro.session.id": sessionId },
    },
    config
  );
}

/**
 * Find traces tagged with a specific model.
 */
export async function kiroTracesByModel(
  model: string,
  limit: number = 20,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return searchTraces(
    {
      service: "kiro-session-handler",
      limit,
      tags: { "kiro.model.name": model },
    },
    config
  );
}

/**
 * Find traces with prompt security detections.
 */
export async function kiroSecurityTraces(
  limit: number = 20,
  config?: JaegerConfig
): Promise<JaegerSearchResult> {
  return searchTraces(
    {
      service: "kiro-session-handler",
      limit,
      tags: { "kiro.security.flagged": "true" },
    },
    config
  );
}

/**
 * Analyze common bottlenecks across multiple slow traces.
 */
export function analyzeBottlenecks(traces: JaegerTrace[]): BottleneckAnalysis {
  const operationStats: Record<string, { count: number; totalMs: number; maxMs: number }> = {};
  const serviceStats: Record<string, { count: number; totalMs: number }> = {};

  for (const trace of traces) {
    for (const span of trace.spans) {
      const service = trace.processes[span.processID]?.serviceName ?? "unknown";
      const op = `${service}::${span.operationName}`;
      const durationMs = span.duration / 1000;

      if (!operationStats[op]) {
        operationStats[op] = { count: 0, totalMs: 0, maxMs: 0 };
      }
      operationStats[op].count++;
      operationStats[op].totalMs += durationMs;
      operationStats[op].maxMs = Math.max(operationStats[op].maxMs, durationMs);

      if (!serviceStats[service]) {
        serviceStats[service] = { count: 0, totalMs: 0 };
      }
      serviceStats[service].count++;
      serviceStats[service].totalMs += durationMs;
    }
  }

  // Sort by total time contribution
  const topOperations = Object.entries(operationStats)
    .map(([name, stats]) => ({ name, avgMs: stats.totalMs / stats.count, ...stats }))
    .sort((a, b) => b.totalMs - a.totalMs)
    .slice(0, 10);

  const topServices = Object.entries(serviceStats)
    .map(([name, stats]) => ({ name, avgMs: stats.totalMs / stats.count, ...stats }))
    .sort((a, b) => b.totalMs - a.totalMs);

  return { topOperations, topServices, traceCount: traces.length };
}

export interface BottleneckAnalysis {
  topOperations: Array<{
    name: string;
    count: number;
    totalMs: number;
    avgMs: number;
    maxMs: number;
  }>;
  topServices: Array<{
    name: string;
    count: number;
    totalMs: number;
    avgMs: number;
  }>;
  traceCount: number;
}
