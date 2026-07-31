import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { searchIssues, getIssue, getSprintMetrics } from "./queries";
import * as client from "./client";

// Mock the client module
vi.mock("./client", async (importOriginal) => {
  const orig = await importOriginal<typeof client>();
  return {
    ...orig,
    jiraFetch: vi.fn(),
    getConfig: vi.fn(() => ({
      baseUrl: "https://test.atlassian.net",
      email: "user@test.com",
      apiToken: "token123",
    })),
  };
});

const mockJiraFetch = vi.mocked(client.jiraFetch);

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Jira queries", () => {
  describe("searchIssues", () => {
    it("calls search endpoint with JQL", async () => {
      mockJiraFetch.mockResolvedValue({ issues: [] });

      await searchIssues({ jql: 'project = PROJ AND status = "In Progress"' });

      expect(mockJiraFetch).toHaveBeenCalledWith(
        expect.stringContaining("/search?jql=")
      );
      const url = mockJiraFetch.mock.calls[0][0];
      expect(url).toContain(encodeURIComponent('project = PROJ AND status = "In Progress"'));
    });

    it("respects maxResults parameter", async () => {
      mockJiraFetch.mockResolvedValue({ issues: [] });

      await searchIssues({ jql: "project = PROJ", maxResults: 10 });

      const url = mockJiraFetch.mock.calls[0][0];
      expect(url).toContain("maxResults=10");
    });

    it("returns issues from response", async () => {
      const issues = [
        { id: "1", key: "PROJ-1", fields: { summary: "Test issue", status: { name: "Open" } } },
      ];
      mockJiraFetch.mockResolvedValue({ issues });

      const result = await searchIssues({ jql: "project = PROJ" });
      expect(result).toEqual(issues);
    });
  });

  describe("getIssue", () => {
    it("fetches issue by key", async () => {
      const issue = { id: "1", key: "PROJ-1", fields: { summary: "Test" } };
      mockJiraFetch.mockResolvedValue(issue);

      const result = await getIssue("PROJ-1");
      expect(result).toEqual(issue);
      expect(mockJiraFetch).toHaveBeenCalledWith("/issue/PROJ-1");
    });
  });

  describe("getSprintMetrics", () => {
    it("computes metrics from sprint issues", async () => {
      // Mock fetch for sprint details + sprint issues
      const mockFetch = vi.spyOn(globalThis, "fetch");

      // First call: sprint details
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          id: 42,
          name: "Sprint 5",
          state: "active",
          startDate: "2026-07-14T00:00:00Z",
          endDate: "2026-07-28T00:00:00Z",
        }), { status: 200 })
      );

      // Second call: sprint issues
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({
          issues: [
            {
              id: "1", key: "PROJ-1",
              fields: {
                summary: "Done task",
                status: { name: "Done", statusCategory: { name: "Done" } },
                issuetype: { name: "Story" },
                priority: { name: "High" },
                assignee: { displayName: "Alice", emailAddress: "alice@test.com" },
                labels: ["feature"],
                components: [],
                timeoriginalestimate: 14400, // 4 hours
                timespent: 18000, // 5 hours
                created: "2026-07-14T00:00:00Z",
                updated: "2026-07-20T00:00:00Z",
                resolutiondate: "2026-07-20T00:00:00Z",
              },
            },
            {
              id: "2", key: "PROJ-2",
              fields: {
                summary: "In progress task",
                status: { name: "In Progress", statusCategory: { name: "In Progress" } },
                issuetype: { name: "Bug" },
                priority: { name: "Medium" },
                assignee: { displayName: "Bob", emailAddress: "bob@test.com" },
                labels: ["bug"],
                components: [],
                timeoriginalestimate: 7200, // 2 hours
                timespent: 3600, // 1 hour
                created: "2026-07-15T00:00:00Z",
                updated: "2026-07-22T00:00:00Z",
                resolutiondate: null,
              },
            },
            {
              id: "3", key: "PROJ-3",
              fields: {
                summary: "Todo task",
                status: { name: "Backlog", statusCategory: { name: "To Do" } },
                issuetype: { name: "Task" },
                priority: { name: "Low" },
                assignee: null,
                labels: [],
                components: [],
                timeoriginalestimate: null,
                timespent: null,
                created: "2026-07-14T00:00:00Z",
                updated: "2026-07-14T00:00:00Z",
                resolutiondate: null,
              },
            },
          ],
        }), { status: 200 })
      );

      const metrics = await getSprintMetrics(42);

      expect(metrics.sprintId).toBe(42);
      expect(metrics.sprintName).toBe("Sprint 5");
      expect(metrics.state).toBe("active");
      expect(metrics.totalIssues).toBe(3);
      expect(metrics.completedIssues).toBe(1);
      expect(metrics.inProgressIssues).toBe(1);
      expect(metrics.todoIssues).toBe(1);
      expect(metrics.totalEstimateHours).toBeCloseTo(6); // 4 + 2 + 0
      expect(metrics.completedEstimateHours).toBeCloseTo(4);
      expect(metrics.timeSpentHours).toBeCloseTo(6); // 5 + 1
      expect(metrics.carryOver).toBe(2);

      // By assignee
      expect(metrics.byAssignee["Alice"].total).toBe(1);
      expect(metrics.byAssignee["Alice"].completed).toBe(1);
      expect(metrics.byAssignee["Bob"].total).toBe(1);
      expect(metrics.byAssignee["Bob"].completed).toBe(0);
      expect(metrics.byAssignee["Unassigned"].total).toBe(1);

      // By type
      expect(metrics.byIssueType["Story"]).toBe(1);
      expect(metrics.byIssueType["Bug"]).toBe(1);
      expect(metrics.byIssueType["Task"]).toBe(1);

      // By priority
      expect(metrics.byPriority["High"]).toBe(1);
      expect(metrics.byPriority["Medium"]).toBe(1);
      expect(metrics.byPriority["Low"]).toBe(1);
    });
  });
});
