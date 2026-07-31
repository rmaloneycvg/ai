/**
 * Integration tests for the Jira MCP server.
 * Tests tool registration and handler invocation with mocked dependencies.
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import * as queries from "../jira/queries";
import * as mutations from "../jira/mutations";

// Mock dependencies at the top level
vi.mock("../jira/queries");
vi.mock("../jira/mutations");

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

// Import the server module — triggers tool registration
beforeAll(async () => {
  await import("../servers/jira");
});

describe("Jira MCP server integration", () => {
  it("registers all 11 expected tools", () => {
    const expectedTools = [
      "jira_list_projects",
      "jira_search_issues",
      "jira_get_issue",
      "jira_list_sprints",
      "jira_get_sprint_metrics",
      "jira_create_issue",
      "jira_create_issues_bulk",
      "jira_create_sprint",
      "jira_create_link",
      "jira_transition_issue",
      "jira_add_comment",
    ];

    for (const tool of expectedTools) {
      expect(registeredTools.has(tool), `Missing tool: ${tool}`).toBe(true);
    }
    expect(registeredTools.size).toBe(expectedTools.length);
  });

  it("jira_list_projects returns projects", async () => {
    vi.mocked(queries.listProjects).mockResolvedValue([
      { id: "1", key: "PROJ", name: "My Project", projectTypeKey: "software" },
    ]);

    const handler = registeredTools.get("jira_list_projects")!.handler;
    const result = await handler({});

    const data = JSON.parse(result.content[0].text);
    expect(data).toHaveLength(1);
    expect(data[0].key).toBe("PROJ");
  });

  it("jira_list_projects returns error on failure", async () => {
    vi.mocked(queries.listProjects).mockRejectedValue(new Error("JIRA_BASE_URL not set"));

    const handler = registeredTools.get("jira_list_projects")!.handler;
    const result = await handler({});

    expect(result.isError).toBe(true);
    const data = JSON.parse(result.content[0].text);
    expect(data.error).toContain("JIRA_BASE_URL");
  });

  it("jira_search_issues returns concise issue summaries", async () => {
    vi.mocked(queries.searchIssues).mockResolvedValue([
      {
        id: "1", key: "PROJ-1", self: "url",
        fields: {
          summary: "Auth feature",
          status: { name: "In Progress", statusCategory: { name: "In Progress" } },
          issuetype: { name: "Story" },
          priority: { name: "High" },
          assignee: { displayName: "Alice", emailAddress: "a@t.com" },
          labels: ["feature"],
          components: [],
          parent: { key: "PROJ-10", fields: { summary: "Epic" } },
          timeoriginalestimate: 14400,
          timespent: 7200,
          created: "2026-07-14", updated: "2026-07-20",
        },
      } as any,
    ]);

    const handler = registeredTools.get("jira_search_issues")!.handler;
    const result = await handler({ jql: "project = PROJ" });

    const data = JSON.parse(result.content[0].text);
    expect(data[0].key).toBe("PROJ-1");
    expect(data[0].assignee).toBe("Alice");
    expect(data[0].estimateHours).toBe(4);
    expect(data[0].parent).toBe("PROJ-10");
  });

  it("jira_get_sprint_metrics returns computed data", async () => {
    vi.mocked(queries.getSprintMetrics).mockResolvedValue({
      sprintId: 42,
      sprintName: "Sprint 5",
      state: "active",
      startDate: "2026-07-14",
      endDate: "2026-07-28",
      totalIssues: 15,
      completedIssues: 10,
      inProgressIssues: 3,
      todoIssues: 2,
      totalEstimateHours: 60,
      completedEstimateHours: 40,
      timeSpentHours: 45,
      byAssignee: { Alice: { total: 8, completed: 6, estimateHours: 32, spentHours: 28 } },
      byIssueType: { Story: 10, Bug: 3, Task: 2 },
      byPriority: { High: 5, Medium: 7, Low: 3 },
      carryOver: 5,
    });

    const handler = registeredTools.get("jira_get_sprint_metrics")!.handler;
    const result = await handler({ sprintId: 42 });

    const data = JSON.parse(result.content[0].text);
    expect(data.completedIssues).toBe(10);
    expect(data.carryOver).toBe(5);
  });

  it("jira_create_issue passes fields and returns result", async () => {
    vi.mocked(mutations.createIssue).mockResolvedValue({
      success: true,
      issue: { id: "10001", key: "PROJ-42", self: "url" },
    });

    const handler = registeredTools.get("jira_create_issue")!.handler;
    const result = await handler({
      projectKey: "PROJ",
      issueType: "Story",
      summary: "New feature",
      priority: "High",
      labels: ["feature"],
      epicKey: "PROJ-10",
    });

    expect(result.isError).toBe(false);
    const data = JSON.parse(result.content[0].text);
    expect(data.issue.key).toBe("PROJ-42");

    expect(mutations.createIssue).toHaveBeenCalledWith(expect.objectContaining({
      projectKey: "PROJ",
      issueType: "Story",
      summary: "New feature",
    }));
  });

  it("jira_create_issues_bulk parses JSON and returns batch results", async () => {
    vi.mocked(mutations.createIssuesBulk).mockResolvedValue({
      created: [{ key: "PROJ-1", summary: "Story 1" }, { key: "PROJ-2", summary: "Story 2" }],
      errors: [],
    });

    const handler = registeredTools.get("jira_create_issues_bulk")!.handler;
    const issues = JSON.stringify([
      { projectKey: "PROJ", issueType: "Story", summary: "Story 1" },
      { projectKey: "PROJ", issueType: "Story", summary: "Story 2" },
    ]);
    const result = await handler({ issues });

    const data = JSON.parse(result.content[0].text);
    expect(data.created).toHaveLength(2);
  });

  it("jira_create_issues_bulk returns error for invalid JSON", async () => {
    const handler = registeredTools.get("jira_create_issues_bulk")!.handler;
    const result = await handler({ issues: "not valid json" });

    expect(result.isError).toBe(true);
  });

  it("jira_create_sprint finds board and creates sprint", async () => {
    vi.mocked(queries.listBoards).mockResolvedValue([
      { id: 1, name: "Board", type: "scrum", location: { projectKey: "PROJ" } },
    ]);
    vi.mocked(mutations.createSprint).mockResolvedValue({
      success: true,
      sprint: { id: 43, name: "Sprint 6", state: "future" },
    });

    const handler = registeredTools.get("jira_create_sprint")!.handler;
    const result = await handler({ projectKey: "PROJ", name: "Sprint 6", startDate: "2026-07-28" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(data.sprint.name).toBe("Sprint 6");
  });

  it("jira_create_sprint returns error when no board found", async () => {
    vi.mocked(queries.listBoards).mockResolvedValue([]);

    const handler = registeredTools.get("jira_create_sprint")!.handler;
    const result = await handler({ projectKey: "NOPE", name: "Sprint" });

    expect(result.isError).toBe(true);
  });

  it("jira_transition_issue calls transitionIssue", async () => {
    vi.mocked(mutations.transitionIssue).mockResolvedValue({ success: true });

    const handler = registeredTools.get("jira_transition_issue")!.handler;
    const result = await handler({ issueKey: "PROJ-1", transitionName: "Done" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(mutations.transitionIssue).toHaveBeenCalledWith({
      issueKey: "PROJ-1", transitionName: "Done",
    });
  });

  it("jira_add_comment calls addComment", async () => {
    vi.mocked(mutations.addComment).mockResolvedValue({ success: true });

    const handler = registeredTools.get("jira_add_comment")!.handler;
    const result = await handler({ issueKey: "PROJ-1", body: "Decision: approved" });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(mutations.addComment).toHaveBeenCalledWith("PROJ-1", "Decision: approved");
  });

  it("jira_create_link creates dependency", async () => {
    vi.mocked(mutations.createIssueLink).mockResolvedValue({ success: true });

    const handler = registeredTools.get("jira_create_link")!.handler;
    const result = await handler({
      outwardIssueKey: "PROJ-1",
      inwardIssueKey: "PROJ-2",
      linkType: "Blocks",
    });

    const data = JSON.parse(result.content[0].text);
    expect(data.success).toBe(true);
    expect(mutations.createIssueLink).toHaveBeenCalledWith({
      outwardIssueKey: "PROJ-1",
      inwardIssueKey: "PROJ-2",
      linkType: "Blocks",
    });
  });

  it("jira_list_sprints finds board then lists sprints", async () => {
    vi.mocked(queries.listBoards).mockResolvedValue([
      { id: 1, name: "Board", type: "scrum", location: { projectKey: "PROJ" } },
    ]);
    vi.mocked(queries.listSprints).mockResolvedValue([
      { id: 42, name: "Sprint 5", state: "active", startDate: "2026-07-14", endDate: "2026-07-28" },
    ]);

    const handler = registeredTools.get("jira_list_sprints")!.handler;
    const result = await handler({ projectKey: "PROJ", state: "active" });

    const data = JSON.parse(result.content[0].text);
    expect(data).toHaveLength(1);
    expect(data[0].name).toBe("Sprint 5");
  });

  it("jira_list_sprints returns error when no board", async () => {
    vi.mocked(queries.listBoards).mockResolvedValue([]);

    const handler = registeredTools.get("jira_list_sprints")!.handler;
    const result = await handler({ projectKey: "NOPE" });

    expect(result.isError).toBe(true);
    const data = JSON.parse(result.content[0].text);
    expect(data.error).toContain("No boards found");
  });
});
