#!/usr/bin/env node
/**
 * MCP Server: postgres
 * Tools: postgres_query, postgres_seed
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { execPython } from "../lib/exec-python.js";

const server = new McpServer({
  name: "postgres",
  version: "0.1.0",
});

server.tool(
  "postgres_query",
  "Execute a read-only parameterized SQL query against postgres",
  {
    sql: z.string().describe("SQL query to execute (read-only; write operations are blocked)"),
    database: z.string().optional().default("postgres").describe("Database name (default: postgres)"),
    params: z.string().optional().describe("JSON array of query parameters"),
  },
  async ({ sql, database, params }) => {
    const args = [sql, database];
    if (params) args.push(params);
    const result = await execPython("postgres/query.py", args);
    return {
      content: [{ type: "text", text: result.stdout || result.stderr }],
      isError: result.exitCode !== 0,
    };
  }
);

server.tool(
  "postgres_seed",
  "Run a .sql seed file against postgres in a transaction",
  {
    file: z.string().describe("Path to the .sql seed file"),
    database: z.string().optional().default("postgres").describe("Database name (default: postgres)"),
  },
  async ({ file, database }) => {
    const result = await execPython("postgres/seed.py", [file, database]);
    return {
      content: [{ type: "text", text: result.stdout || result.stderr }],
      isError: result.exitCode !== 0,
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("postgres MCP server failed to start:", err);
  process.exit(1);
});
