import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getConfig, grafanaFetch } from "./client.js";

describe("grafana/client", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  describe("getConfig", () => {
    it("returns config from environment variables", () => {
      process.env.GRAFANA_URL = "http://grafana:3000";
      process.env.GRAFANA_API_KEY = "glsa_token123";
      process.env.GRAFANA_ORG_ID = "1";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://grafana:3000");
      expect(config.apiKey).toBe("glsa_token123");
      expect(config.orgId).toBe("1");
    });

    it("strips trailing slash from URL", () => {
      process.env.GRAFANA_URL = "http://grafana:3000/";
      process.env.GRAFANA_API_KEY = "key";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://grafana:3000");
    });

    it("throws if GRAFANA_URL is not set", () => {
      delete process.env.GRAFANA_URL;
      process.env.GRAFANA_API_KEY = "key";

      expect(() => getConfig()).toThrow("GRAFANA_URL environment variable is required");
    });

    it("throws if GRAFANA_API_KEY is not set", () => {
      process.env.GRAFANA_URL = "http://grafana:3000";
      delete process.env.GRAFANA_API_KEY;

      expect(() => getConfig()).toThrow("GRAFANA_API_KEY environment variable is required");
    });

    it("allows missing org ID", () => {
      process.env.GRAFANA_URL = "http://grafana:3000";
      process.env.GRAFANA_API_KEY = "key";
      delete process.env.GRAFANA_ORG_ID;

      const config = getConfig();

      expect(config.orgId).toBeUndefined();
    });
  });

  describe("grafanaFetch", () => {
    it("makes GET request with Bearer auth", async () => {
      const mockData = [{ id: 1, uid: "abc", title: "Test Dashboard" }];
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockData), { status: 200 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "test-key", orgId: undefined };
      const result = await grafanaFetch("/search", undefined, config);

      const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
      expect(calledUrl).toBe("http://grafana:3000/api/search");

      const headers = vi.mocked(fetch).mock.calls[0][1]?.headers as Record<string, string>;
      expect(headers.Authorization).toBe("Bearer test-key");
      expect(result).toEqual(mockData);
    });

    it("includes org ID header when set", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({}), { status: 200 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "key", orgId: "5" };
      await grafanaFetch("/search", undefined, config);

      const headers = vi.mocked(fetch).mock.calls[0][1]?.headers as Record<string, string>;
      expect(headers["X-Grafana-Org-Id"]).toBe("5");
    });

    it("sends POST with body", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ id: 1 }), { status: 200 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "key", orgId: undefined };
      await grafanaFetch("/annotations", { method: "POST", body: { text: "deploy" } }, config);

      const call = vi.mocked(fetch).mock.calls[0];
      expect(call[1]?.method).toBe("POST");
      expect(call[1]?.body).toBe(JSON.stringify({ text: "deploy" }));
    });

    it("appends query params", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify([]), { status: 200 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "key", orgId: undefined };
      await grafanaFetch("/search", { params: { query: "kiro", type: "dash-db" } }, config);

      const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
      expect(calledUrl).toContain("query=kiro");
      expect(calledUrl).toContain("type=dash-db");
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("Unauthorized", { status: 401 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "bad-key", orgId: undefined };
      await expect(grafanaFetch("/search", undefined, config)).rejects.toThrow(
        "Grafana API error 401: Unauthorized"
      );
    });

    it("handles 204 No Content", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(null, { status: 204 })
      );

      const config = { baseUrl: "http://grafana:3000", apiKey: "key", orgId: undefined };
      const result = await grafanaFetch("/some-endpoint", { method: "DELETE" }, config);

      expect(result).toBeUndefined();
    });
  });
});
