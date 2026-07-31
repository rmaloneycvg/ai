#!/usr/bin/env node
/**
 * MCP Server: prometheus
 * Tools: prometheus_query, prometheus_range_query, prometheus_metrics,
 *        prometheus_alerts, prometheus_kiro_usage, prometheus_kiro_performance,
 *        prometheus_kiro_models, prometheus_kiro_context, prometheus_kiro_security,
 *        prometheus_error_rates, prometheus_release_compare
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import {
  instantQuery,
  rangeQuery,
  listMetrics,
  listLabelValues,
  getAlerts,
  getRules,
  kiroFeatureUsage,
  kiroSessionPerformance,
  kiroModelUsage,
  kiroContextSize,
  serviceErrorRates,
  kiroPromptSecurityDetections,
  compareReleases,
} from "../prometheus/queries.js";

const server = new McpServer({
  name: "prometheus",
  version: "0.1.0",
});

// ─── Core Query Tools ───────────────────────────────────────────

server.tool(
  "prometheus_query",
  "Execute an instant PromQL query against Prometheus. Returns current metric values.",
  {
    query: z.string().describe("PromQL expression to evaluate"),
    time: z.string().optional().describe("Evaluation timestamp (RFC3339 or Unix). Defaults to current time."),
  },
  async ({ query, time }) => {
    try {
      const result = await instantQuery(query, time);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_range_query",
  "Execute a range PromQL query. Returns time-series data over a period.",
  {
    query: z.string().describe("PromQL expression"),
    start: z.string().describe("Start time (RFC3339 or Unix timestamp)"),
    end: z.string().describe("End time (RFC3339 or Unix timestamp)"),
    step: z.string().describe("Query resolution step (e.g., '15s', '1m', '5m')"),
  },
  async ({ query, start, end, step }) => {
    try {
      const result = await rangeQuery(query, start, end, step);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_metrics",
  "List available metric names, optionally filtered by a match pattern. Useful for discovering what's being tracked.",
  {
    match: z.string().optional().describe("PromQL series selector to filter (e.g., '{job=\"kiro\"}')"),
  },
  async ({ match }) => {
    try {
      const result = await listMetrics(match);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_label_values",
  "List all values for a given label name. Useful for discovering services, features, models.",
  {
    label: z.string().describe("Label name (e.g., 'service', 'feature', 'model', 'release')"),
  },
  async ({ label }) => {
    try {
      const result = await listLabelValues(label);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_alerts",
  "Get all active and pending alerts from Prometheus Alertmanager.",
  {},
  async () => {
    try {
      const result = await getAlerts();
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_rules",
  "Get all alerting and recording rules, including their health status.",
  {},
  async () => {
    try {
      const result = await getRules();
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Kiro-Specific Tools ────────────────────────────────────────

server.tool(
  "prometheus_kiro_usage",
  "Get Kiro feature invocation rates. Shows which features are being used and how frequently.",
  {
    feature_pattern: z.string().optional().default(".*").describe("Regex pattern to match feature names (e.g., 'command_.*')"),
    window: z.string().optional().default("5m").describe("Rate window (e.g., '5m', '1h')"),
  },
  async ({ feature_pattern, window }) => {
    try {
      const result = await kiroFeatureUsage(feature_pattern, window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_kiro_performance",
  "Get Kiro session duration percentiles. Track if sessions meet SLO targets.",
  {
    quantile: z.number().optional().default(0.95).describe("Percentile to calculate (0.5, 0.95, 0.99)"),
    window: z.string().optional().default("5m").describe("Rate window"),
  },
  async ({ quantile, window }) => {
    try {
      const result = await kiroSessionPerformance(quantile, window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_kiro_models",
  "Get AI model usage breakdown. Shows request rates per model (claude-sonnet, claude-opus, etc).",
  {
    window: z.string().optional().default("1h").describe("Rate window"),
  },
  async ({ window }) => {
    try {
      const result = await kiroModelUsage(window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_kiro_context",
  "Get context token size distribution. Track context window utilization across sessions.",
  {
    quantile: z.number().optional().default(0.95).describe("Percentile (0.5, 0.95, 0.99)"),
    window: z.string().optional().default("1h").describe("Rate window"),
  },
  async ({ quantile, window }) => {
    try {
      const result = await kiroContextSize(quantile, window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_kiro_security",
  "Get prompt security detection rates. Tracks injection attempts, leaked secrets, PII exposure in prompts.",
  {
    window: z.string().optional().default("1h").describe("Rate window"),
  },
  async ({ window }) => {
    try {
      const result = await kiroPromptSecurityDetections(window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_error_rates",
  "Get HTTP error rates (5xx) by service. Useful for detecting degraded services.",
  {
    service: z.string().optional().describe("Filter to specific service. Omit for all services."),
    window: z.string().optional().default("5m").describe("Rate window"),
  },
  async ({ service, window }) => {
    try {
      const result = await serviceErrorRates(service, window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "prometheus_release_compare",
  "Compare a metric across different releases. Useful for detecting regressions after deployments.",
  {
    metric: z.string().describe("Metric name with optional labels (e.g., 'kiro_session_duration_seconds_count')"),
    releases: z.array(z.string()).describe("Release versions to compare (e.g., ['v1.2.0', 'v1.3.0'])"),
    window: z.string().optional().default("1h").describe("Lookback window"),
  },
  async ({ metric, releases, window }) => {
    try {
      const result = await compareReleases(metric, releases, window);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("prometheus MCP server failed to start:", err);
  process.exit(1);
});
