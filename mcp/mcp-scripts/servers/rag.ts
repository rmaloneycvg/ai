#!/usr/bin/env node
/**
 * MCP Server: rag
 * Tools: rag_search, rag_status
 *
 * Triple-vector semantic search over steering documents stored in pgvector.
 * Vectors: folder (domain), hierarchy (heading tree), content (section text).
 * Weighting: 0.3 folder + 0.3 hierarchy + 0.4 content.
 * Session-aware: tracks returned chunks, avoids repeating within a conversation.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { execFile } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RAG_DIR = resolve(__dirname, "..", "..", "..", "rag");

interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

function execRagPython(scriptName: string, args: string[] = []): Promise<ExecResult> {
  const python = resolve(RAG_DIR, ".venv", "bin", "python");
  const script = resolve(RAG_DIR, scriptName);

  return new Promise((res) => {
    execFile(python, [script, ...args], { cwd: RAG_DIR, timeout: 30_000 }, (error, stdout, stderr) => {
      const exitCode = error && "code" in error ? (error.code as number) ?? 1 : error ? 1 : 0;
      res({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode });
    });
  });
}

const server = new McpServer({
  name: "rag",
  version: "0.2.0",
});

server.tool(
  "rag_search",
  "Search steering documentation using triple-vector semantic similarity (folder domain + heading hierarchy + content). Returns top-K relevant chunks formatted as steering context. Weighted: folder path 30%, hierarchy 30%, content 40%. Automatically deduplicates across multiple calls in the same session — safe to call repeatedly for different topics without getting repeated content.",
  {
    query: z.string().describe("Natural language query describing what you need to know (e.g., 'EF Core N+1 detection and fix patterns', 'CQRS command handler structure', 'SQL Server index type decision')"),
    top_k: z.number().min(1).max(10).optional().default(5).describe("Number of results to return (default: 5, max: 10)"),
    source_filter: z.string().optional().describe("Filter results to a specific folder/domain (e.g., 'csharp', 'mssql', 'nextjs')"),
    depth_max: z.number().min(0).max(4).optional().describe("Maximum heading depth to return (0=document root, 1=#, 2=##, 3=###, 4=####). Omit for all depths."),
  },
  async ({ query, top_k, source_filter, depth_max }) => {
    const args = [
      query,
      String(top_k ?? 5),
      source_filter ?? "None",
      depth_max !== undefined ? String(depth_max) : "None",
    ];

    const result = await execRagPython("search_cli.py", args);

    if (result.exitCode !== 0) {
      return {
        content: [{ type: "text", text: `RAG search error: ${result.stderr || result.stdout}` }],
        isError: true,
      };
    }

    return {
      content: [{ type: "text", text: result.stdout }],
    };
  }
);

server.tool(
  "rag_status",
  "Check RAG system status: Ollama connectivity, database stats (per-folder chunk counts), and session deduplication state.",
  {},
  async () => {
    const result = await execRagPython("search_cli.py", ["--status"]);

    if (result.exitCode !== 0) {
      return {
        content: [{ type: "text", text: `RAG status error: ${result.stderr || result.stdout}` }],
        isError: true,
      };
    }

    return {
      content: [{ type: "text", text: result.stdout }],
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("rag MCP server failed to start:", err);
  process.exit(1);
});
