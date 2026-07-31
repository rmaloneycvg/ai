import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getConfig, promFetch } from "./client.js";

describe("prometheus/client", () => {
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
      process.env.PROMETHEUS_URL = "http://prometheus:9090";
      process.env.PROMETHEUS_AUTH_TOKEN = "secret-token";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://prometheus:9090");
      expect(config.authToken).toBe("secret-token");
    });

    it("strips trailing slash from URL", () => {
      process.env.PROMETHEUS_URL = "http://prometheus:9090/";

      const config = getConfig();

      expect(config.baseUrl).toBe("http://prometheus:9090");
    });

    it("throws if PROMETHEUS_URL is not set", () => {
      delete process.env.PROMETHEUS_URL;

      expect(() => getConfig()).toThrow("PROMETHEUS_URL environment variable is required");
    });

    it("allows missing auth token", () => {
      process.env.PROMETHEUS_URL = "http://prometheus:9090";
      delete process.env.PROMETHEUS_AUTH_TOKEN;

      const config = getConfig();

      expect(config.authToken).toBeUndefined();
    });
  });

  describe("promFetch", () => {
    it("makes GET request with params", async () => {
      const mockResponse = { status: "success", data: { resultType: "vector", result: [] } };
      const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify(mockResponse), { status: 200 })
      );

      const config = { baseUrl: "http://prom:9090", authToken: undefined };
      const result = await promFetch("/query", { query: "up" }, config);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const calledUrl = fetchSpy.mock.calls[0][0] as string;
      expect(calledUrl).toContain("/api/v1/query");
      expect(calledUrl).toContain("query=up");
      expect(result).toEqual(mockResponse);
    });

    it("includes Authorization header when token is set", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({}), { status: 200 })
      );

      const config = { baseUrl: "http://prom:9090", authToken: "my-token" };
      await promFetch("/query", { query: "up" }, config);

      const calledOptions = vi.mocked(fetch).mock.calls[0][1];
      expect((calledOptions?.headers as Record<string, string>).Authorization).toBe("Bearer my-token");
    });

    it("does not include Authorization header when no token", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({}), { status: 200 })
      );

      const config = { baseUrl: "http://prom:9090", authToken: undefined };
      await promFetch("/query", { query: "up" }, config);

      const calledOptions = vi.mocked(fetch).mock.calls[0][1];
      expect((calledOptions?.headers as Record<string, string>).Authorization).toBeUndefined();
    });

    it("throws on non-OK response", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("bad query syntax", { status: 400 })
      );

      const config = { baseUrl: "http://prom:9090", authToken: undefined };
      await expect(promFetch("/query", { query: "invalid{" }, config)).rejects.toThrow(
        "Prometheus API error 400: bad query syntax"
      );
    });
  });
});
