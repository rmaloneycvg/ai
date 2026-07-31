#!/usr/bin/env node
/**
 * MCP Server: jaeger
 * Tools: jaeger_services, jaeger_operations, jaeger_search_traces,
 *        jaeger_get_trace, jaeger_dependencies, jaeger_analyze_bottlenecks,
 *        jaeger_kiro_slow_sessions, jaeger_kiro_by_command, jaeger_kiro_by_model,
 *        jaeger_kiro_security_traces, jaeger_kiro_session_trace
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import {
  listServices,
  listOperations,
  searchTraces,
  getTrace,
  getDependencies,
  summarizeTrace,
  analyzeBottlenecks,
  kiroSlowSessions,
  kiroSessionsByCommand,
  kiroSessionTrace,
  kiroTracesByModel,
  kiroSecurityTraces,
} from "../jaeger/queries.js";

const server = new McpServer({
  name: "jaeger",
  version: "0.1.0",
});

// ─── Service Discovery ──────────────────────────────────────────

server.tool(
  "jaeger_services",
  "List all services reporting traces to Jaeger. Use to discover what's instrumented.",
  {},
  async () => {
    try {
      const result = await listServices();
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_operations",
  "List all operations (endpoints/functions) for a given service.",
  {
    service: z.string().describe("Service name to list operations for"),
  },
  async ({ service }) => {
    try {
      const result = await listOperations(service);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Trace Search & Detail ──────────────────────────────────────

server.tool(
  "jaeger_search_traces",
  "Search for traces by service, operation, tags, and duration. Returns matching traces with span details.",
  {
    service: z.string().describe("Service name to search traces for"),
    operation: z.string().optional().describe("Filter by operation name"),
    tags: z.string().optional().describe("JSON object of tag key-value filters (e.g., '{\"http.status_code\":\"500\"}')"),
    min_duration: z.string().optional().describe("Minimum trace duration (e.g., '1s', '500ms')"),
    max_duration: z.string().optional().describe("Maximum trace duration"),
    limit: z.number().optional().default(20).describe("Maximum traces to return (default: 20)"),
  },
  async ({ service, operation, tags, min_duration, max_duration, limit }) => {
    try {
      const parsedTags = tags ? JSON.parse(tags) : undefined;
      const result = await searchTraces({
        service,
        operation,
        tags: parsedTags,
        minDuration: min_duration,
        maxDuration: max_duration,
        limit,
      });

      // Add summaries for each trace
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ total: result.total, summaries, raw: result }, null, 2),
        }],
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_get_trace",
  "Get full trace detail by trace ID. Shows all spans across services.",
  {
    trace_id: z.string().describe("Trace ID to retrieve"),
  },
  async ({ trace_id }) => {
    try {
      const result = await getTrace(trace_id);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ summaries, raw: result }, null, 2),
        }],
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Dependencies & Bottleneck Analysis ─────────────────────────

server.tool(
  "jaeger_dependencies",
  "Get service dependency graph. Shows which services call which, with call counts.",
  {
    lookback: z.string().optional().describe("Lookback period in ms (e.g., '3600000' for 1h). Defaults to last hour."),
  },
  async ({ lookback }) => {
    try {
      const endTs = String(Date.now() * 1000); // microseconds
      const result = await getDependencies(endTs, lookback);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_analyze_bottlenecks",
  "Analyze common bottlenecks across slow traces for a service. Returns top 10 slowest operations and services ranked by total time contribution.",
  {
    service: z.string().describe("Service to analyze"),
    min_duration: z.string().optional().default("1s").describe("Minimum duration threshold for 'slow' traces"),
    limit: z.number().optional().default(50).describe("Number of traces to sample for analysis"),
  },
  async ({ service, min_duration, limit }) => {
    try {
      const result = await searchTraces({ service, minDuration: min_duration, limit });
      if (!result.data?.length) {
        return { content: [{ type: "text", text: JSON.stringify({ message: "No slow traces found", params: { service, min_duration } }) }] };
      }
      const analysis = analyzeBottlenecks(result.data);
      return { content: [{ type: "text", text: JSON.stringify(analysis, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Kiro-Specific Trace Tools ──────────────────────────────────

server.tool(
  "jaeger_kiro_slow_sessions",
  "Find Kiro sessions that exceeded a duration threshold. Useful for performance regression detection.",
  {
    min_duration: z.string().optional().default("5s").describe("Minimum session duration (e.g., '5s', '10s')"),
    limit: z.number().optional().default(10).describe("Max results"),
  },
  async ({ min_duration, limit }) => {
    try {
      const result = await kiroSlowSessions(min_duration, limit);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return { content: [{ type: "text", text: JSON.stringify({ total: result.total, summaries }, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_kiro_by_command",
  "Find traces for a specific Kiro command type (e.g., 'execute_script', 'code_review').",
  {
    command_type: z.string().describe("Command type to search for"),
    limit: z.number().optional().default(20).describe("Max results"),
  },
  async ({ command_type, limit }) => {
    try {
      const result = await kiroSessionsByCommand(command_type, limit);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return { content: [{ type: "text", text: JSON.stringify({ total: result.total, summaries }, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_kiro_by_model",
  "Find traces tagged with a specific AI model. Track model-specific latency and errors.",
  {
    model: z.string().describe("Model name (e.g., 'claude-sonnet-5', 'claude-opus-4')"),
    limit: z.number().optional().default(20).describe("Max results"),
  },
  async ({ model, limit }) => {
    try {
      const result = await kiroTracesByModel(model, limit);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return { content: [{ type: "text", text: JSON.stringify({ total: result.total, summaries }, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_kiro_security_traces",
  "Find traces flagged with prompt security detections (injection attempts, secret leaks, PII exposure).",
  {
    limit: z.number().optional().default(20).describe("Max results"),
  },
  async ({ limit }) => {
    try {
      const result = await kiroSecurityTraces(limit);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return { content: [{ type: "text", text: JSON.stringify({ total: result.total, summaries }, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jaeger_kiro_session_trace",
  "Get the full trace for a specific Kiro session by session ID.",
  {
    session_id: z.string().describe("Kiro session ID"),
  },
  async ({ session_id }) => {
    try {
      const result = await kiroSessionTrace(session_id);
      const summaries = result.data?.map(summarizeTrace) ?? [];
      return { content: [{ type: "text", text: JSON.stringify({ summaries, raw: result }, null, 2) }] };
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
  console.error("jaeger MCP server failed to start:", err);
  process.exit(1);
});
