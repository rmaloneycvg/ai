import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createIssue, createIssuesBulk, createIssueLink, transitionIssue, addComment } from "./mutations";
import * as client from "./client";

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
  vi.restoreAllMocks();
});

describe("Jira mutations", () => {
  describe("createIssue", () => {
    it("creates a story with correct fields", async () => {
      mockJiraFetch.mockResolvedValue({ id: "10001", key: "PROJ-42", self: "https://test.atlassian.net/rest/api/3/issue/10001" });

      const result = await createIssue({
        projectKey: "PROJ",
        issueType: "Story",
        summary: "Add user authentication",
        description: "Implement OAuth2 PKCE flow",
        priority: "High",
        labels: ["feature", "auth"],
      });

      expect(result.success).toBe(true);
      expect(result.issue?.key).toBe("PROJ-42");

      // Verify the API call
      expect(mockJiraFetch).toHaveBeenCalledWith("/issue", {
        method: "POST",
        body: {
          fields: expect.objectContaining({
            project: { key: "PROJ" },
            issuetype: { name: "Story" },
            summary: "Add user authentication",
            priority: { name: "High" },
            labels: ["feature", "auth"],
          }),
        },
      });
    });

    it("sets parent for sub-tasks", async () => {
      mockJiraFetch.mockResolvedValue({ id: "10002", key: "PROJ-43", self: "url" });

      await createIssue({
        projectKey: "PROJ",
        issueType: "Sub-task",
        summary: "Write unit tests",
        parentKey: "PROJ-42",
      });

      const body = mockJiraFetch.mock.calls[0][1]!.body as { fields: Record<string, unknown> };
      expect(body.fields.parent).toEqual({ key: "PROJ-42" });
    });

    it("sets epic link for stories", async () => {
      mockJiraFetch.mockResolvedValue({ id: "10003", key: "PROJ-44", self: "url" });

      await createIssue({
        projectKey: "PROJ",
        issueType: "Story",
        summary: "Implement login page",
        epicKey: "PROJ-10",
      });

      const body = mockJiraFetch.mock.calls[0][1]!.body as { fields: Record<string, unknown> };
      expect(body.fields.parent).toEqual({ key: "PROJ-10" });
    });

    it("converts hours estimate to seconds", async () => {
      mockJiraFetch.mockResolvedValue({ id: "10004", key: "PROJ-45", self: "url" });

      await createIssue({
        projectKey: "PROJ",
        issueType: "Task",
        summary: "Setup CI pipeline",
        originalEstimateHours: 4,
      });

      const body = mockJiraFetch.mock.calls[0][1]!.body as { fields: Record<string, unknown> };
      expect(body.fields.timeoriginalestimate).toBe(14400); // 4 * 3600
    });

    it("returns error on API failure", async () => {
      mockJiraFetch.mockRejectedValue(new Error("Jira API error 400: invalid fields"));

      const result = await createIssue({
        projectKey: "PROJ",
        issueType: "Story",
        summary: "Bad request",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("400");
    });

    it("converts description to ADF format", async () => {
      mockJiraFetch.mockResolvedValue({ id: "10005", key: "PROJ-46", self: "url" });

      await createIssue({
        projectKey: "PROJ",
        issueType: "Story",
        summary: "With description",
        description: "First paragraph\n\nSecond paragraph",
      });

      const body = mockJiraFetch.mock.calls[0][1]!.body as { fields: Record<string, unknown> };
      const desc = body.fields.description as { type: string; content: Array<{ type: string; content: Array<{ text: string }> }> };
      expect(desc.type).toBe("doc");
      expect(desc.content).toHaveLength(2);
      expect(desc.content[0].content[0].text).toBe("First paragraph");
      expect(desc.content[1].content[0].text).toBe("Second paragraph");
    });
  });

  describe("createIssuesBulk", () => {
    it("creates multiple issues and collects results", async () => {
      let callCount = 0;
      mockJiraFetch.mockImplementation(async () => {
        callCount++;
        return { id: `${callCount}`, key: `PROJ-${callCount}`, self: `url${callCount}` };
      });

      const result = await createIssuesBulk([
        { projectKey: "PROJ", issueType: "Story", summary: "Story 1" },
        { projectKey: "PROJ", issueType: "Bug", summary: "Bug 1" },
      ]);

      expect(result.created).toHaveLength(2);
      expect(result.errors).toHaveLength(0);
      expect(result.created[0].key).toBe("PROJ-1");
      expect(result.created[1].key).toBe("PROJ-2");
    });

    it("collects errors without stopping batch", async () => {
      let callCount = 0;
      mockJiraFetch.mockImplementation(async () => {
        callCount++;
        if (callCount === 2) throw new Error("Validation error");
        return { id: `${callCount}`, key: `PROJ-${callCount}`, self: `url` };
      });

      const result = await createIssuesBulk([
        { projectKey: "PROJ", issueType: "Story", summary: "Story 1" },
        { projectKey: "PROJ", issueType: "Story", summary: "Story 2" },
        { projectKey: "PROJ", issueType: "Story", summary: "Story 3" },
      ]);

      expect(result.created).toHaveLength(2);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].summary).toBe("Story 2");
    });
  });

  describe("createIssueLink", () => {
    it("creates a Blocks link", async () => {
      mockJiraFetch.mockResolvedValue(undefined); // 204

      const result = await createIssueLink({
        outwardIssueKey: "PROJ-1",
        inwardIssueKey: "PROJ-2",
        linkType: "Blocks",
      });

      expect(result.success).toBe(true);
      expect(mockJiraFetch).toHaveBeenCalledWith("/issueLink", {
        method: "POST",
        body: {
          type: { name: "Blocks" },
          inwardIssue: { key: "PROJ-2" },
          outwardIssue: { key: "PROJ-1" },
        },
      });
    });

    it("returns error on failure", async () => {
      mockJiraFetch.mockRejectedValue(new Error("Link type not found"));

      const result = await createIssueLink({
        outwardIssueKey: "PROJ-1",
        inwardIssueKey: "PROJ-2",
        linkType: "Blocks",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("Link type not found");
    });
  });

  describe("transitionIssue", () => {
    it("transitions to matching status", async () => {
      // First call: get transitions
      mockJiraFetch.mockResolvedValueOnce({
        transitions: [
          { id: "21", name: "In Progress" },
          { id: "31", name: "Done" },
        ],
      });
      // Second call: do transition
      mockJiraFetch.mockResolvedValueOnce(undefined);

      const result = await transitionIssue({
        issueKey: "PROJ-1",
        transitionName: "In Progress",
      });

      expect(result.success).toBe(true);
      expect(mockJiraFetch).toHaveBeenCalledTimes(2);
      expect(mockJiraFetch).toHaveBeenLastCalledWith("/issue/PROJ-1/transitions", {
        method: "POST",
        body: { transition: { id: "21" } },
      });
    });

    it("returns error when transition not found", async () => {
      mockJiraFetch.mockResolvedValueOnce({
        transitions: [
          { id: "21", name: "In Progress" },
          { id: "31", name: "Done" },
        ],
      });

      const result = await transitionIssue({
        issueKey: "PROJ-1",
        transitionName: "Invalid Status",
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain("not found");
      expect(result.error).toContain("In Progress, Done");
    });

    it("matches case-insensitively", async () => {
      mockJiraFetch.mockResolvedValueOnce({
        transitions: [{ id: "31", name: "Done" }],
      });
      mockJiraFetch.mockResolvedValueOnce(undefined);

      const result = await transitionIssue({
        issueKey: "PROJ-1",
        transitionName: "done",
      });

      expect(result.success).toBe(true);
    });
  });

  describe("addComment", () => {
    it("posts comment in ADF format", async () => {
      mockJiraFetch.mockResolvedValue({ id: "c1" });

      const result = await addComment("PROJ-1", "Decision: Use OAuth2 PKCE flow");

      expect(result.success).toBe(true);
      expect(mockJiraFetch).toHaveBeenCalledWith("/issue/PROJ-1/comment", {
        method: "POST",
        body: {
          body: expect.objectContaining({
            type: "doc",
            version: 1,
          }),
        },
      });
    });

    it("returns error on failure", async () => {
      mockJiraFetch.mockRejectedValue(new Error("Forbidden"));

      const result = await addComment("PROJ-1", "test");
      expect(result.success).toBe(false);
      expect(result.error).toContain("Forbidden");
    });
  });
});
