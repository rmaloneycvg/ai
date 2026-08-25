/**
 * Integration tests for the Work Summary MCP server.
 * Tests tool registration and handler invocation with mocked dependencies.
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import * as aggregator from "../work-summary/aggregator";

// Mock the aggregator
vi.mock("../work-summary/aggregator", () => ({
  generateSummary: vi.fn(),
  getStatus: vi.fn(),
}));

// Mock config module
vi.mock("../work-summary/config.js", () => ({
  loadConfig: vi.fn(() => ({
    workspacePaths: ["~/workspace"],
    author: { name: "Test User", email: "test@example.com" },
    sessionGapMinutes: 30,
    outputDir: "~/output",
    collectors: { git: { enabled: true } },
  })),
  expandHome: vi.fn((p: string) => p),
}));

// Mock fs for config read/write
vi.mock("node:fs", async () => {
  const actual = await vi.importActual("node:fs");
  return {
    ...actual,
    readFileSync: vi.fn(() => JSON.stringify({
      workspacePaths: ["~/workspace"],
      author: { name: "Test User", email: "test@example.com" },
      sessionGapMinutes: 30,
      outputDir: "~/output",
      collectors: { git: { enabled: true }, kiro: { enabled: true }, chrome: { enabled: false } },
    })),
    writeFileSync: vi.fn(),
  };
});

// Mock the MCP SDK — capture tool registrations
const registeredTools: Map<string, { description: string; handler: Function }> = new Map();

vi.mock("@modelcontextprotocol/sdk/server/mcp.js", () => ({
  McpServer: class {
    tool(name: string, description: string, _schema: unknown, handler: Function) {
      registeredTools.set(name, { description, handler });
    }
    connect() {}
  },
}));

vi.mock("@modelcontextprotocol/sdk/server/stdio.js", () => ({
  StdioServerTransport: class {},
}));

// Import the server module — triggers tool registration
beforeAll(async () => {
  await import("./work-summary");
});

describe("Work Summary MCP server", () => {
  it("registers all 3 expected tools", () => {
    expect(registeredTools.has("work_summary_generate")).toBe(true);
    expect(registeredTools.has("work_summary_config")).toBe(true);
    expect(registeredTools.has("work_summary_status")).toBe(true);
    expect(registeredTools.size).toBe(3);
  });

  describe("work_summary_generate", () => {
    it("calls generateSummary and returns formatted result", async () => {
      vi.mocked(aggregator.generateSummary).mockResolvedValue({
        success: true,
        summary: {
          date: "2026-08-24",
          author: "Test User",
          summary: {
            totalCommits: 5,
            totalEditTime: "2h 30m",
            aiAssistedTime: "1h 45m",
            manualTime: "45m",
            categories: { features: 3, refactors: 1, unitTests: 1, integrationTests: 0, perfTests: 0, docs: 0 },
          },
          timeline: [],
          filesChanged: [],
          aiSessions: { count: 2, totalDuration: "1h 45m", toolUsage: {} },
          browserActivity: { searches: [], devToolsSessions: 0 },
          communications: { teams: null, googleMeet: null, zoom: null, slack: null, outlook: null },
          timeBreakdown: { coding: "2h 30m", meetings: "0m", aiPaired: "1h 45m", manual: "45m" },
        },
        markdown: "# Daily Work Summary",
        outputFiles: { json: "/output/2026-08-24.json", markdown: "/output/2026-08-24.md" },
        collectorResults: [
          { name: "git", success: true, durationMs: 120, errors: [] },
          { name: "kiro", success: true, durationMs: 80, errors: [] },
        ],
        errors: [],
      });

      const handler = registeredTools.get("work_summary_generate")!.handler;
      const result = await handler({ date: "2026-08-24" });

      expect(result.content[0].text).toContain("Work Summary Generated");
      expect(result.content[0].text).toContain("Commits:** 5");
      expect(result.content[0].text).toContain("2h 30m");
      expect(result.content[0].text).toContain("✅ git");
    });

    it("returns error on failure", async () => {
      vi.mocked(aggregator.generateSummary).mockRejectedValue(new Error("something broke"));

      const handler = registeredTools.get("work_summary_generate")!.handler;
      const result = await handler({});

      expect(result.isError).toBe(true);
      expect(result.content[0].text).toContain("something broke");
    });

    it("defaults to today when no date provided", async () => {
      vi.mocked(aggregator.generateSummary).mockResolvedValue({
        success: true,
        summary: {
          date: new Date().toISOString().split("T")[0],
          author: "Test",
          summary: { totalCommits: 0, totalEditTime: "0m", aiAssistedTime: "0m", manualTime: "0m", categories: { features: 0, refactors: 0, unitTests: 0, integrationTests: 0, perfTests: 0, docs: 0 } },
          timeline: [],
          filesChanged: [],
          aiSessions: { count: 0, totalDuration: "0m", toolUsage: {} },
          browserActivity: { searches: [], devToolsSessions: 0 },
          communications: { teams: null, googleMeet: null, zoom: null, slack: null, outlook: null },
          timeBreakdown: { coding: "0m", meetings: "0m", aiPaired: "0m", manual: "0m" },
        },
        markdown: "",
        outputFiles: {},
        collectorResults: [],
        errors: [],
      });

      const handler = registeredTools.get("work_summary_generate")!.handler;
      const result = await handler({});

      expect(aggregator.generateSummary).toHaveBeenCalled();
    });
  });

  describe("work_summary_config", () => {
    it("returns config on get action", async () => {
      const handler = registeredTools.get("work_summary_config")!.handler;
      const result = await handler({ action: "get" });

      const data = JSON.parse(result.content[0].text);
      expect(data.workspacePaths).toContain("~/workspace");
      expect(data.author.name).toBe("Test User");
    });

    it("adds a workspace path", async () => {
      const handler = registeredTools.get("work_summary_config")!.handler;
      const result = await handler({ action: "add_path", value: "~/projects" });

      const data = JSON.parse(result.content[0].text);
      expect(data.success).toBe(true);
      expect(data.workspacePaths).toContain("~/projects");
    });

    it("removes a workspace path", async () => {
      const handler = registeredTools.get("work_summary_config")!.handler;
      const result = await handler({ action: "remove_path", value: "~/workspace" });

      const data = JSON.parse(result.content[0].text);
      expect(data.success).toBe(true);
    });

    it("sets a config key", async () => {
      const handler = registeredTools.get("work_summary_config")!.handler;
      const result = await handler({ action: "set", key: "sessionGapMinutes", value: "45" });

      const data = JSON.parse(result.content[0].text);
      expect(data.success).toBe(true);
      expect(data.value).toBe(45);
    });

    it("returns error when set is missing key/value", async () => {
      const handler = registeredTools.get("work_summary_config")!.handler;
      const result = await handler({ action: "set" });

      expect(result.isError).toBe(true);
    });
  });

  describe("work_summary_status", () => {
    it("returns status with config and collector info", async () => {
      vi.mocked(aggregator.getStatus).mockReturnValue({
        config: {
          workspacePaths: ["~/workspace"],
          author: { name: "Test User", email: "test@example.com" },
          sessionGapMinutes: 30,
          outputDir: "~/output",
          collectors: { git: { enabled: true }, kiro: { enabled: true } },
        },
        collectors: [
          { name: "git", enabled: true, hasCredentials: false },
          { name: "kiro", enabled: true, hasCredentials: false },
          { name: "teams", enabled: false, hasCredentials: false },
        ],
      });

      const handler = registeredTools.get("work_summary_status")!.handler;
      const result = await handler({});

      expect(result.content[0].text).toContain("Work Summary Status");
      expect(result.content[0].text).toContain("~/workspace");
      expect(result.content[0].text).toContain("git");
      expect(result.content[0].text).toContain("✅");
    });
  });
});
