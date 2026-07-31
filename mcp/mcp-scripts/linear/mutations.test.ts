import { describe, it, expect, vi, beforeEach } from "vitest";
import { createIssue, createIssuesBulk, createProject, createCycle, createDocument, createIssueRelation } from "./mutations";
import * as client from "./client";

vi.mock("./client", async (importOriginal) => {
  const orig = await importOriginal<typeof client>();
  return { ...orig, graphql: vi.fn(), getConfig: vi.fn(() => ({ apiKey: "test" })) };
});

const mockGraphql = vi.mocked(client.graphql);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Linear mutations", () => {
  describe("createIssue", () => {
    it("returns success with issue data", async () => {
      mockGraphql.mockResolvedValue({
        data: {
          issueCreate: {
            success: true,
            issue: { id: "i1", identifier: "ENG-42", title: "New feature", url: "https://linear.app/eng/issue/ENG-42" },
          },
        },
      });

      const result = await createIssue({
        teamId: "t1",
        title: "New feature",
        priority: 2,
        estimate: 3,
      });

      expect(result.success).toBe(true);
      expect(result.issue?.identifier).toBe("ENG-42");
    });

    it("returns error on GraphQL errors", async () => {
      mockGraphql.mockResolvedValue({
        errors: [{ message: "Team not found" }],
      });

      const result = await createIssue({ teamId: "bad", title: "Test" });
      expect(result.success).toBe(false);
      expect(result.error).toContain("Team not found");
    });

    it("returns error on failed mutation", async () => {
      mockGraphql.mockResolvedValue({
        data: { issueCreate: { success: false, issue: null } },
      });

      const result = await createIssue({ teamId: "t1", title: "Test" });
      expect(result.success).toBe(false);
      expect(result.error).toContain("failed");
    });
  });

  describe("createIssuesBulk", () => {
    it("creates multiple issues and returns results", async () => {
      let callCount = 0;
      mockGraphql.mockImplementation(async () => {
        callCount++;
        return {
          data: {
            issueCreate: {
              success: true,
              issue: { id: `i${callCount}`, identifier: `ENG-${callCount}`, title: `Issue ${callCount}`, url: `https://linear.app/issue/ENG-${callCount}` },
            },
          },
        };
      });

      const result = await createIssuesBulk([
        { teamId: "t1", title: "Issue 1" },
        { teamId: "t1", title: "Issue 2" },
        { teamId: "t1", title: "Issue 3" },
      ]);

      expect(result.created).toHaveLength(3);
      expect(result.errors).toHaveLength(0);
      expect(result.created[0].identifier).toBe("ENG-1");
    });

    it("collects errors without stopping", async () => {
      let callCount = 0;
      mockGraphql.mockImplementation(async () => {
        callCount++;
        if (callCount === 2) {
          return { errors: [{ message: "Validation failed" }] };
        }
        return {
          data: {
            issueCreate: {
              success: true,
              issue: { id: `i${callCount}`, identifier: `ENG-${callCount}`, title: `Issue ${callCount}`, url: `url${callCount}` },
            },
          },
        };
      });

      const result = await createIssuesBulk([
        { teamId: "t1", title: "Issue 1" },
        { teamId: "t1", title: "Issue 2" },
        { teamId: "t1", title: "Issue 3" },
      ]);

      expect(result.created).toHaveLength(2);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].title).toBe("Issue 2");
    });
  });

  describe("createProject", () => {
    it("returns success with project data", async () => {
      mockGraphql.mockResolvedValue({
        data: {
          projectCreate: {
            success: true,
            project: { id: "p1", name: "Auth Epic", url: "https://linear.app/project/p1" },
          },
        },
      });

      const result = await createProject({
        teamIds: ["t1"],
        name: "Auth Epic",
        description: "OAuth2 implementation",
      });

      expect(result.success).toBe(true);
      expect(result.project?.name).toBe("Auth Epic");
    });
  });

  describe("createCycle", () => {
    it("returns success with cycle data", async () => {
      mockGraphql.mockResolvedValue({
        data: {
          cycleCreate: {
            success: true,
            cycle: { id: "c1", number: 6, startsAt: "2026-07-28T00:00:00Z", endsAt: "2026-08-11T00:00:00Z" },
          },
        },
      });

      const result = await createCycle({
        teamId: "t1",
        name: "Sprint 6",
        startsAt: "2026-07-28T00:00:00Z",
        endsAt: "2026-08-11T00:00:00Z",
      });

      expect(result.success).toBe(true);
      expect(result.cycle?.number).toBe(6);
    });
  });

  describe("createDocument", () => {
    it("returns success with document data", async () => {
      mockGraphql.mockResolvedValue({
        data: {
          documentCreate: {
            success: true,
            document: { id: "d1", title: "Sprint 5 Report", url: "https://linear.app/doc/d1" },
          },
        },
      });

      const result = await createDocument({
        title: "Sprint 5 Report",
        content: "## Summary\n\nCompleted 80% of planned work.",
        projectId: "p1",
      });

      expect(result.success).toBe(true);
      expect(result.document?.title).toBe("Sprint 5 Report");
    });
  });

  describe("createIssueRelation", () => {
    it("returns success for blocks relation", async () => {
      mockGraphql.mockResolvedValue({
        data: { issueRelationCreate: { success: true } },
      });

      const result = await createIssueRelation({
        issueId: "i1",
        relatedIssueId: "i2",
        type: "blocks",
      });

      expect(result.success).toBe(true);
    });

    it("returns error on failure", async () => {
      mockGraphql.mockResolvedValue({
        errors: [{ message: "Issue not found" }],
      });

      const result = await createIssueRelation({
        issueId: "bad",
        relatedIssueId: "i2",
        type: "blocks",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Issue not found");
    });
  });
});
