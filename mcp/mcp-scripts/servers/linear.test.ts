/**
 * Integration tests for the Linear MCP server.
 * Tests tool registration and handler invocation with mocked dependencies.
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import * as queries from "../linear/queries";
import * as mutations from "../linear/mutations";

// Mock dependencies at the top level
vi.mock("../linear/queries");
vi.mock("../linear/mutations");

// Mock the MCP SDK — capture tool registrations
const registeredTools: Map<string, { description: string; handler: Function }> = new Map();

vi.mock("@modelcontextprotocol/sdk/server/mcp.js", () => ({
  McpServer: vi.fn().mockImplementation(() => ({
    tool: (name: string, description: string, _schema: unknown, handler: Function) => {
      registeredTools.set(name, { description, handler });
    },
    connect: vi.fn(),
  })),
}));

vi.mock("@modelcontextprotocol/sdk/server/stdio.js", () => ({
  StdioServerTransport: vi.fn(),
}));

// Import the server module — this triggers tool registration
beforeAll(async () => {
  await import("../servers/linear");
});

describe("Linear MCP server integration", () => {
  it("registers all 12 expected tools", () => {
    const expectedTools = [
      "linear_list_teams",
      "linear_list_issues",
      "linear_get_issue",
      "linear_list_projects",
      "linear_list_cycles",
      "linear_get_cycle_metrics",
      "linear_create_issue",
      "linear_create_issues_bulk",
      "linear_create_project",
      "linear_create_cycle",
      "linear_create_document",
      "linear_create_relation",
    ];

    for (const tool of expectedTools) {
      expect(registeredTools.has(tool), `Missing tool: ${tool}`).toBe(true);
    }
    expect(registeredTools.size).toBe(expectedTools.length);
  });

  it("linear_list_teams returns teams on success", async () => {
    vi.mocked(queries.listTeams).mockResolvedValue([
      { id: "t1", name: "Engineering", key: "ENG" },
    ]);

    const handler = registeredTools.get("linear_list_teams")!.handler;
    const result = await handler({});

    const data = JSON.parse(result.content[0].text);
    expect(data).toHaveLength(1);
    expect(data[0].name).toBe("Engineering");
  });

  it("linear_list_teams returns error on failure", async () => {
    vi.mocked(queries.listTeams).mockRejectedValue(new Error("LINEAR_API_KEY not set"));

    const handler = registeredTools.get("linear_list_teams")!.handler;
    const result = await handler({});

    expect(result.isError).toBe(true);
    const data = JSON.parse(result.content[0].text);
    expect(data.error).toContain("LINEAR_API_KEY");
  });

  it("linear_list_issues passes filter params", async () => {
    vi.mocked(queries.listIssues).mockResolvedValue([]);

    const handler = registeredTools.get("linear_list_issues")!.handler;
    await handler({ teamId: "t1", state: "In Progress", priority: 2 });

    expect(queries.listIssues).toHaveBeenCalledWith({
      teamId: "t1",
      filter: { state: "In Progress", assigneeId: undefined, labelName: undefined, projectId: undefined, cycleId: undefined, priority: 2 },
      first: undefined,
    });
  });

  it("linear_get_issue returns null as error", async () => {
    vi.mocked(queries.getIssue).mockResolvedValue(null);

    const handler = registeredTools.get("linear_get_issue")!.handler;
    const result = await handler({ issueId: "nonexistent" });

    expect(result.isError).toBe(true);
  });

  it("linear_create_issue passes input and returns result", async () => {
    vi.mocked(mutations.createIssue).mockResolvedValue({
      success: true,
      issue: { id: "i1", identifier: "ENG-1", title: "Test", url: "https://linear.app/issue/ENG-1" },
    });

    const handler = registeredTools.get("linear_create_issue")!.handler;
    const result = await handler({
      teamId: "t1",
      title: "Test issue",
      priority: 2,
      description: "Description here",
    });

    expect(result.isError).toBe(false);
    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(data.issue.identifier).toBe("ENG-1");
  });

  it("linear_create_issues_bulk parses JSON array", async () => {
    vi.mocked(mutations.createIssuesBulk).mockResolvedValue({
      created: [{ identifier: "ENG-1", title: "A", url: "u1" }],
      errors: [],
    });

    const handler = registeredTools.get("linear_create_issues_bulk")!.handler;
    const input = JSON.stringify([{ teamId: "t1", title: "A" }]);
    const result = await handler({ issues: input });

    const data = JSON.parse(result.content[0].text);
    expect(data.created).toHaveLength(1);
  });

  it("linear_create_issues_bulk returns error for invalid JSON", async () => {
    const handler = registeredTools.get("linear_create_issues_bulk")!.handler;
    const result = await handler({ issues: "not json" });

    expect(result.isError).toBe(true);
  });

  it("linear_get_cycle_metrics returns metrics data", async () => {
    vi.mocked(queries.getCycleMetrics).mockResolvedValue({
      cycleNumber: 5, cycleName: "Sprint 5",
      startDate: "2026-07-14", endDate: "2026-07-28",
      progress: 0.75,
      totalIssues: 20, completedIssues: 15, inProgressIssues: 3, backlogIssues: 2,
      totalEstimate: 45, completedEstimate: 33,
      byAssignee: {}, byLabel: {}, byPriority: {},
    });

    const handler = registeredTools.get("linear_get_cycle_metrics")!.handler;
    const result = await handler({ teamId: "t1" });

    const data = JSON.parse(result.content[0].text);
    expect(data.completedIssues).toBe(15);
    expect(data.progress).toBe(0.75);
  });

  it("linear_get_cycle_metrics returns error when no cycle", async () => {
    vi.mocked(queries.getCycleMetrics).mockResolvedValue(null);

    const handler = registeredTools.get("linear_get_cycle_metrics")!.handler;
    const result = await handler({ teamId: "t1" });

    expect(result.isError).toBe(true);
  });

  it("linear_create_project passes input", async () => {
    vi.mocked(mutations.createProject).mockResolvedValue({
      success: true,
      project: { id: "p1", name: "Auth Epic", url: "url" },
    });

    const handler = registeredTools.get("linear_create_project")!.handler;
    const result = await handler({ teamIds: ["t1"], name: "Auth Epic", description: "OAuth2" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
  });

  it("linear_create_document passes content", async () => {
    vi.mocked(mutations.createDocument).mockResolvedValue({
      success: true,
      document: { id: "d1", title: "Notes", url: "url" },
    });

    const handler = registeredTools.get("linear_create_document")!.handler;
    const result = await handler({ title: "Notes", content: "## Summary", projectId: "p1" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(data.document.title).toBe("Notes");
  });

  it("linear_create_relation passes type correctly", async () => {
    vi.mocked(mutations.createIssueRelation).mockResolvedValue({ success: true });

    const handler = registeredTools.get("linear_create_relation")!.handler;
    const result = await handler({ issueId: "i1", relatedIssueId: "i2", type: "blocks" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(mutations.createIssueRelation).toHaveBeenCalledWith({
      issueId: "i1", relatedIssueId: "i2", type: "blocks",
    });
  });
});
