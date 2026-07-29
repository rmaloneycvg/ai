#!/usr/bin/env node
/**
 * MCP Server: io
 * Tools: read_json, write_json
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { readJson } from "../io/read-json.js";
import { writeJson } from "../io/write-json.js";

const server = new McpServer({
  name: "io",
  version: "0.1.0",
});

server.tool(
  "read_json",
  "Read and parse a JSON file with validation",
  { path: z.string().describe("Path to the JSON file to read") },
  async ({ path }) => {
    const result = readJson(path);
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      isError: !result.success,
    };
  }
);

server.tool(
  "write_json",
  "Write JSON to a file with configurable formatting",
  {
    path: z.string().describe("Path to write the JSON file"),
    data: z.string().describe("JSON string to write (will be parsed to validate)"),
    indent: z.number().optional().default(2).describe("Indentation spaces (default: 2)"),
  },
  async ({ path, data, indent }) => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(data);
    } catch {
      return {
        content: [{ type: "text", text: JSON.stringify({ success: false, error: "Invalid JSON data" }) }],
        isError: true,
      };
    }
    const result = writeJson(path, parsed, { indent });
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      isError: !result.success,
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("io MCP server failed to start:", err);
  process.exit(1);
});
