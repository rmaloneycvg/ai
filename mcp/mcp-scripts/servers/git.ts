#!/usr/bin/env node
/**
 * MCP Server: git
 * Tools: git_status
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { getStatus } from "../git/status.js";

const server = new McpServer({
  name: "git",
  version: "0.1.0",
});

server.tool(
  "git_status",
  "Get parsed git status showing staged, unstaged, and untracked files",
  { cwd: z.string().optional().describe("Working directory (defaults to cwd)") },
  async ({ cwd }) => {
    try {
      const status = getStatus(cwd);
      return { content: [{ type: "text", text: JSON.stringify(status, null, 2) }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: "text", text: JSON.stringify({ error: message }) }], isError: true };
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("git MCP server failed to start:", err);
  process.exit(1);
});
