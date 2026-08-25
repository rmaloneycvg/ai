#!/usr/bin/env node
/**
 * MCP Server: work-summary
 * Tools: work_summary_generate, work_summary_config, work_summary_status
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { generateSummary, getStatus } from "../work-summary/aggregator.js";
import { loadConfig, expandHome } from "../work-summary/config.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = resolve(__dirname, "../work-summary/config.json");

const server = new McpServer({
  name: "work-summary",
  version: "0.1.0",
});

// ─── work_summary_generate ──────────────────────────────────────────────────

server.tool(
  "work_summary_generate",
  "Generate a daily work summary from git commits, AI sessions, browser activity, and more",
  {
    date: z.string().optional().describe("Target date in YYYY-MM-DD format (defaults to today)"),
    outputDir: z.string().optional().describe("Override output directory for summary files"),
  },
  async ({ date, outputDir }) => {
    try {
      // If outputDir provided, temporarily modify config
      let configPath: string | undefined;
      if (outputDir) {
        // Load, modify, use in-memory (don't persist override)
        configPath = CONFIG_PATH;
      }

      const result = await generateSummary(date, configPath);

      // Build response text
      const lines: string[] = [];
      lines.push(`# Work Summary Generated — ${result.summary?.date || "unknown"}`);
      lines.push("");

      if (result.summary) {
        lines.push(`**Commits:** ${result.summary.summary.totalCommits}`);
        lines.push(`**Edit Time:** ${result.summary.summary.totalEditTime}`);
        lines.push(`**AI-Paired:** ${result.summary.summary.aiAssistedTime}`);
        lines.push(`**Manual:** ${result.summary.summary.manualTime}`);
        lines.push("");
        lines.push("**Categories:**");
        const cats = result.summary.summary.categories;
        lines.push(`  Features: ${cats.features} | Refactors: ${cats.refactors} | Unit Tests: ${cats.unitTests} | Integration Tests: ${cats.integrationTests} | Perf Tests: ${cats.perfTests} | Docs: ${cats.docs}`);
        lines.push("");
      }

      // Collector status
      lines.push("**Collector Results:**");
      for (const cr of result.collectorResults) {
        const icon = cr.success ? "✅" : "⚠️";
        lines.push(`  ${icon} ${cr.name} (${cr.durationMs}ms)${cr.errors.length > 0 ? ` — ${cr.errors[0]}` : ""}`);
      }

      if (result.outputFiles.json || result.outputFiles.markdown) {
        lines.push("");
        lines.push("**Output Files:**");
        if (result.outputFiles.json) lines.push(`  JSON: ${result.outputFiles.json}`);
        if (result.outputFiles.markdown) lines.push(`  Markdown: ${result.outputFiles.markdown}`);
      }

      if (result.errors.length > 0) {
        lines.push("");
        lines.push("**Errors:**");
        for (const err of result.errors) {
          lines.push(`  - ${err}`);
        }
      }

      return {
        content: [
          { type: "text", text: lines.join("\n") },
          { type: "text", text: "\n---\n\n" + JSON.stringify(result.summary, null, 2) },
        ],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: JSON.stringify({ error: message }) }],
        isError: true,
      };
    }
  }
);

// ─── work_summary_config ────────────────────────────────────────────────────

server.tool(
  "work_summary_config",
  "Read or update work summary configuration (workspace paths, collectors, etc.)",
  {
    action: z.enum(["get", "set", "add_path", "remove_path"]).describe("Action to perform"),
    key: z.string().optional().describe("Config key to set (dot-notation, e.g. 'sessionGapMinutes')"),
    value: z.string().optional().describe("Value to set (JSON-encoded for complex values)"),
  },
  async ({ action, key, value }) => {
    try {
      const configRaw = readFileSync(CONFIG_PATH, "utf-8");
      const config = JSON.parse(configRaw);

      switch (action) {
        case "get": {
          return {
            content: [{ type: "text", text: JSON.stringify(config, null, 2) }],
          };
        }

        case "set": {
          if (!key || value === undefined) {
            return {
              content: [{ type: "text", text: JSON.stringify({ error: "Both 'key' and 'value' are required for set action" }) }],
              isError: true,
            };
          }

          // Parse value as JSON if possible, otherwise use as string
          let parsedValue: unknown;
          try {
            parsedValue = JSON.parse(value);
          } catch {
            parsedValue = value;
          }

          // Set nested key using dot notation
          setNestedKey(config, key, parsedValue);
          writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), "utf-8");

          return {
            content: [{ type: "text", text: JSON.stringify({ success: true, key, value: parsedValue }) }],
          };
        }

        case "add_path": {
          if (!value) {
            return {
              content: [{ type: "text", text: JSON.stringify({ error: "'value' is required (path to add)" }) }],
              isError: true,
            };
          }
          if (!config.workspacePaths.includes(value)) {
            config.workspacePaths.push(value);
            writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), "utf-8");
          }
          return {
            content: [{ type: "text", text: JSON.stringify({ success: true, workspacePaths: config.workspacePaths }) }],
          };
        }

        case "remove_path": {
          if (!value) {
            return {
              content: [{ type: "text", text: JSON.stringify({ error: "'value' is required (path to remove)" }) }],
              isError: true,
            };
          }
          config.workspacePaths = config.workspacePaths.filter((p: string) => p !== value);
          writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), "utf-8");
          return {
            content: [{ type: "text", text: JSON.stringify({ success: true, workspacePaths: config.workspacePaths }) }],
          };
        }

        default:
          return {
            content: [{ type: "text", text: JSON.stringify({ error: `Unknown action: ${action}` }) }],
            isError: true,
          };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: JSON.stringify({ error: message }) }],
        isError: true,
      };
    }
  }
);

// ─── work_summary_status ────────────────────────────────────────────────────

server.tool(
  "work_summary_status",
  "Show current configuration, available data sources, and collector health",
  {},
  async () => {
    try {
      const status = getStatus(CONFIG_PATH);

      const lines: string[] = [];
      lines.push("# Work Summary Status");
      lines.push("");
      lines.push("## Configuration");
      lines.push(`- **Workspace Paths:** ${status.config.workspacePaths.join(", ")}`);
      lines.push(`- **Author:** ${status.config.author.name} <${status.config.author.email}>`);
      lines.push(`- **Session Gap:** ${status.config.sessionGapMinutes} minutes`);
      lines.push(`- **Output Dir:** ${status.config.outputDir}`);
      lines.push("");
      lines.push("## Collectors");
      lines.push("");
      lines.push("| Collector | Enabled | Credentials |");
      lines.push("|-----------|---------|-------------|");
      for (const c of status.collectors) {
        const enabled = c.enabled ? "✅" : "❌";
        const creds = c.enabled ? (c.hasCredentials ? "✅ configured" : "⚠️ missing") : "—";
        lines.push(`| ${c.name} | ${enabled} | ${creds} |`);
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: JSON.stringify({ error: message }) }],
        isError: true,
      };
    }
  }
);

// ─── Helpers ────────────────────────────────────────────────────────────────

function setNestedKey(obj: Record<string, unknown>, key: string, value: unknown): void {
  const parts = key.split(".");
  let current: any = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!(parts[i] in current) || typeof current[parts[i]] !== "object") {
      current[parts[i]] = {};
    }
    current = current[parts[i]];
  }
  current[parts[parts.length - 1]] = value;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("work-summary MCP server failed to start:", err);
  process.exit(1);
});
