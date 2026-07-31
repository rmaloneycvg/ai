import { describe, it, expect, vi, beforeEach } from "vitest";
import { listTeams, listIssues, getIssue, listCycles, getCycleMetrics } from "./queries";
import * as client from "./client";

vi.mock("./client", async (importOriginal) => {
  const orig = await importOriginal<typeof client>();
  return { ...orig, graphql: vi.fn(), getConfig: vi.fn(() => ({ apiKey: "test" })) };
});

const mockGraphql = vi.mocked(client.graphql);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Linear queries", () => {
  describe("listTeams", () => {
    it("returns teams from response", async () => {
      const teams = [
        { id: "t1", name: "Engineering", key: "ENG" },
        { id: "t2", name: "Design", key: "DES" },
      ];
      mockGraphql.mockResolvedValue({ data: { teams: { nodes: teams } } });

      const result = await listTeams();
      expect(result).toEqual(teams);
    });

    it("returns empty array on null data", async () => {
      mockGraphql.mockResolvedValue({ data: undefined });
      const result = await listTeams();
      expect(result).toEqual([]);
    });
  });

  describe("listIssues", () => {
    it("passes teamId filter", async () => {
      mockGraphql.mockResolvedValue({ data: { issues: { nodes: [] } } });

      await listIssues({ teamId: "t1" });

      expect(mockGraphql).toHaveBeenCalledOnce();
      const query = mockGraphql.mock.calls[0][0];
      expect(query).toContain('team: { id: { eq: "t1" } }');
    });

    it("includes state filter when provided", async () => {
      mockGraphql.mockResolvedValue({ data: { issues: { nodes: [] } } });

      await listIssues({ teamId: "t1", filter: { state: "In Progress" } });

      const query = mockGraphql.mock.calls[0][0];
      expect(query).toContain('state: { name: { eq: "In Progress" } }');
    });

    it("includes priority filter when provided", async () => {
      mockGraphql.mockResolvedValue({ data: { issues: { nodes: [] } } });

      await listIssues({ teamId: "t1", filter: { priority: 1 } });

      const query = mockGraphql.mock.calls[0][0];
      expect(query).toContain("priority: { eq: 1 }");
    });

    it("returns issues from response", async () => {
      const issues = [{ id: "i1", identifier: "ENG-1", title: "Test" }];
      mockGraphql.mockResolvedValue({ data: { issues: { nodes: issues } } });

      const result = await listIssues({ teamId: "t1" });
      expect(result).toEqual(issues);
    });
  });

  describe("getIssue", () => {
    it("returns issue by ID", async () => {
      const issue = { id: "i1", identifier: "ENG-1", title: "Test Issue" };
      mockGraphql.mockResolvedValue({ data: { issue } });

      const result = await getIssue("i1");
      expect(result).toEqual(issue);
    });

    it("returns null when not found", async () => {
      mockGraphql.mockResolvedValue({ data: { issue: null } });

      const result = await getIssue("nonexistent");
      expect(result).toBeNull();
    });
  });

  describe("getCycleMetrics", () => {
    const makeCycle = (issues: Partial<client.LinearIssue>[]) => ({
      id: "c1",
      number: 5,
      name: "Sprint 5",
      startsAt: "2026-07-14T00:00:00Z",
      endsAt: "2026-07-28T00:00:00Z",
      progress: 0.6,
      issues: { nodes: issues as client.LinearIssue[] },
    });

    it("computes metrics for active cycle", async () => {
      const issues = [
        {
          id: "i1", identifier: "ENG-1", title: "Done task",
          state: { name: "Done" }, priority: 2, estimate: 3,
          assignee: { name: "Alice", email: "alice@test.com" },
          labels: { nodes: [{ name: "feature" }] },
          completedAt: "2026-07-20T00:00:00Z",
          createdAt: "2026-07-14T00:00:00Z", updatedAt: "2026-07-20T00:00:00Z",
        },
        {
          id: "i2", identifier: "ENG-2", title: "In progress",
          state: { name: "In Progress" }, priority: 3, estimate: 5,
          assignee: { name: "Bob", email: "bob@test.com" },
          labels: { nodes: [{ name: "bug" }] },
          completedAt: undefined,
          createdAt: "2026-07-14T00:00:00Z", updatedAt: "2026-07-22T00:00:00Z",
        },
        {
          id: "i3", identifier: "ENG-3", title: "Backlog item",
          state: { name: "Backlog" }, priority: 4, estimate: 2,
          assignee: null,
          labels: { nodes: [] },
          completedAt: undefined,
          createdAt: "2026-07-14T00:00:00Z", updatedAt: "2026-07-14T00:00:00Z",
        },
      ];

      // Mock listCycles (called internally via getActiveCycle)
      mockGraphql.mockResolvedValue({
        data: { team: { cycles: { nodes: [makeCycle(issues)] } } },
      });

      const metrics = await getCycleMetrics("t1");

      expect(metrics).not.toBeNull();
      expect(metrics!.cycleNumber).toBe(5);
      expect(metrics!.totalIssues).toBe(3);
      expect(metrics!.completedIssues).toBe(1);
      expect(metrics!.inProgressIssues).toBe(1);
      expect(metrics!.backlogIssues).toBe(1);
      expect(metrics!.totalEstimate).toBe(10); // 3 + 5 + 2
      expect(metrics!.completedEstimate).toBe(3);
      expect(metrics!.byAssignee["Alice"].completed).toBe(1);
      expect(metrics!.byAssignee["Bob"].total).toBe(1);
      expect(metrics!.byAssignee["Unassigned"].total).toBe(1);
      expect(metrics!.byLabel["feature"]).toBe(1);
      expect(metrics!.byLabel["bug"]).toBe(1);
      expect(metrics!.byPriority[2]).toBe(1); // high
      expect(metrics!.byPriority[3]).toBe(1); // medium
    });

    it("returns null when no active cycle", async () => {
      mockGraphql.mockResolvedValue({
        data: { team: { cycles: { nodes: [] } } },
      });

      const metrics = await getCycleMetrics("t1");
      expect(metrics).toBeNull();
    });
  });
});
