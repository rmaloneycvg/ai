import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getConfig, jaegerFetch } from "./client.js";

describe("jaeger/client", () => {
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
      process.env.JAEGER_URL = "http://jaeger:16686";
      process.env.JAEGER_AUTH_TOKEN = "jaeger-token";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://jaeger:16686");
      expect(config.authToken).toBe("jaeger-token");
    });

    it("strips trailing slash from URL", () => {
      process.env.JAEGER_URL = "http://jaeger:16686/";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://jaeger:16686");
    });

    it("throws if JAEGER_URL is not set", () => {
      delete process.env.JAEGER_URL;

      expect(() => getConfig()).toThrow("JAEGER_URL environment variable is required");
    });

    it("allows missing auth token", () => {
      process.env.JAEGER_URL = "http://jaeger:16686";
      delete process.env.JAEGER_AUTH_TOKEN;

      const config = getConfig();

      expect(config.authToken).toBeUndefined();
    });
  });

  describe("jaegerFetch", () => {
    it("makes GET request with params", async () => {
      const mockData = { data: ["service-a", "service-b"], total: 2, limit: 0, offset: 0 };
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockData), { status: 200 })
      );

      const config = { baseUrl: "http://jaeger:16686", authToken: undefined };
      const result = await jaegerFetch("/services", undefined, config);

      expect(vi.mocked(fetch).mock.calls[0][0]).toContain("/api/services");
      expect(result).toEqual(mockData);
    });

    it("handles array params (repeated keys)", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ data: [] }), { status: 200 })
      );

      const config = { baseUrl: "http://jaeger:16686", authToken: undefined };
      await jaegerFetch("/traces", { service: "kiro", tags: ['{"key":"val"}'] }, config);

      const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
      expect(calledUrl).toContain("service=kiro");
    });

    it("includes Authorization header when token is set", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({}), { status: 200 })
      );

      const config = { baseUrl: "http://jaeger:16686", authToken: "my-token" };
      await jaegerFetch("/services", undefined, config);

      const headers = vi.mocked(fetch).mock.calls[0][1]?.headers as Record<string, string>;
      expect(headers.Authorization).toBe("Bearer my-token");
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("not found", { status: 404 })
      );

      const config = { baseUrl: "http://jaeger:16686", authToken: undefined };
      await expect(jaegerFetch("/traces/invalid", undefined, config)).rejects.toThrow(
        "Jaeger API error 404: not found"
      );
    });
  });
});
