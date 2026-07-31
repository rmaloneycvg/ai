import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getConfig, graphql } from "./client";

describe("Linear client", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  describe("getConfig", () => {
    it("returns config when LINEAR_API_KEY is set", () => {
      process.env.LINEAR_API_KEY = "lin_api_test123";
      const config = getConfig();
      expect(config.apiKey).toBe("lin_api_test123");
    });

    it("throws when LINEAR_API_KEY is missing", () => {
      delete process.env.LINEAR_API_KEY;
      expect(() => getConfig()).toThrow("LINEAR_API_KEY");
    });
  });

  describe("graphql", () => {
    it("sends correct headers and body", async () => {
      const mockResponse = { data: { teams: { nodes: [] } } };
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockResponse), { status: 200 })
      );

      const config = { apiKey: "lin_api_test" };
      const query = "query { teams { nodes { id } } }";
      const result = await graphql(query, undefined, config);

      expect(fetchSpy).toHaveBeenCalledWith("https://api.linear.app/graphql", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "lin_api_test",
        },
        body: JSON.stringify({ query, variables: undefined }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("sends variables when provided", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ data: {} }), { status: 200 })
      );

      const config = { apiKey: "lin_api_test" };
      await graphql("query($id: String!) { issue(id: $id) { id } }", { id: "abc" }, config);

      const call = vi.mocked(fetch).mock.calls[0];
      const body = JSON.parse(call[1]!.body as string);
      expect(body.variables).toEqual({ id: "abc" });
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Unauthorized", { status: 401, statusText: "Unauthorized" })
      );

      const config = { apiKey: "bad_key" };
      await expect(graphql("query { teams { nodes { id } } }", undefined, config))
        .rejects.toThrow("Linear API error: 401 Unauthorized");
    });
  });
});
