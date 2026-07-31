import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getConfig, jiraFetch } from "./client";

describe("Jira client", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  describe("getConfig", () => {
    it("returns config when all env vars are set", () => {
      process.env.JIRA_BASE_URL = "https://test.atlassian.net";
      process.env.JIRA_EMAIL = "user@test.com";
      process.env.JIRA_API_TOKEN = "token123";

      const config = getConfig();
      expect(config.baseUrl).toBe("https://test.atlassian.net");
      expect(config.email).toBe("user@test.com");
      expect(config.apiToken).toBe("token123");
    });

    it("strips trailing slash from baseUrl", () => {
      process.env.JIRA_BASE_URL = "https://test.atlassian.net/";
      process.env.JIRA_EMAIL = "user@test.com";
      process.env.JIRA_API_TOKEN = "token123";

      const config = getConfig();
      expect(config.baseUrl).toBe("https://test.atlassian.net");
    });

    it("throws when JIRA_BASE_URL is missing", () => {
      delete process.env.JIRA_BASE_URL;
      process.env.JIRA_EMAIL = "user@test.com";
      process.env.JIRA_API_TOKEN = "token123";

      expect(() => getConfig()).toThrow("JIRA_BASE_URL");
    });

    it("throws when JIRA_EMAIL is missing", () => {
      process.env.JIRA_BASE_URL = "https://test.atlassian.net";
      delete process.env.JIRA_EMAIL;
      process.env.JIRA_API_TOKEN = "token123";

      expect(() => getConfig()).toThrow("JIRA_EMAIL");
    });

    it("throws when JIRA_API_TOKEN is missing", () => {
      process.env.JIRA_BASE_URL = "https://test.atlassian.net";
      process.env.JIRA_EMAIL = "user@test.com";
      delete process.env.JIRA_API_TOKEN;

      expect(() => getConfig()).toThrow("JIRA_API_TOKEN");
    });
  });

  describe("jiraFetch", () => {
    const config = {
      baseUrl: "https://test.atlassian.net",
      email: "user@test.com",
      apiToken: "token123",
    };

    it("sends correct auth headers", async () => {
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ values: [] }), { status: 200 })
      );

      await jiraFetch("/project/search", {}, config);

      const expectedAuth = Buffer.from("user@test.com:token123").toString("base64");
      expect(fetchSpy).toHaveBeenCalledWith(
        "https://test.atlassian.net/rest/api/3/project/search",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Authorization: `Basic ${expectedAuth}`,
            "Content-Type": "application/json",
          }),
        })
      );
    });

    it("sends POST with body", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ id: "123", key: "PROJ-1" }), { status: 201 })
      );

      const body = { fields: { summary: "Test" } };
      await jiraFetch("/issue", { method: "POST", body }, config);

      const call = vi.mocked(fetch).mock.calls[0];
      expect(call[1]!.method).toBe("POST");
      expect(call[1]!.body).toBe(JSON.stringify(body));
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response('{"errorMessages":["Not found"]}', { status: 404 })
      );

      await expect(jiraFetch("/issue/FAKE-1", {}, config)).rejects.toThrow("Jira API error 404");
    });

    it("returns undefined for 204 responses", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(null, { status: 204 })
      );

      const result = await jiraFetch("/issueLink", { method: "POST", body: {} }, config);
      expect(result).toBeUndefined();
    });
  });
});
