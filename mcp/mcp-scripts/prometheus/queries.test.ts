import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  instantQuery,
  rangeQuery,
  listMetrics,
  listLabelValues,
  getAlerts,
  getRules,
  kiroFeatureUsage,
  kiroSessionPerformance,
  kiroModelUsage,
  kiroContextSize,
  serviceErrorRates,
  kiroPromptSecurityDetections,
} from "./queries.js";

// Mock the client
vi.mock("./client.js", () => ({
  getConfig: () => ({ baseUrl: "http://prom:9090", authToken: undefined }),
  promFetch: vi.fn(),
}));

import { promFetch } from "./client.js";
const mockPromFetch = vi.mocked(promFetch);

describe("prometheus/queries", () => {
  beforeEach(() => {
    mockPromFetch.mockReset();
  });

  describe("instantQuery", () => {
    it("calls promFetch with /query path and query param", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await instantQuery("up");

      expect(mockPromFetch).toHaveBeenCalledWith("/query", { query: "up" }, undefined);
    });

    it("passes time parameter when provided", async () => {
      mockPromFetch.mockResolvedValue({ status: "success" });

      await instantQuery("up", "2024-01-01T00:00:00Z");

      expect(mockPromFetch).toHaveBeenCalledWith(
        "/query",
        { query: "up", time: "2024-01-01T00:00:00Z" },
        undefined
      );
    });
  });

  describe("rangeQuery", () => {
    it("calls promFetch with /query_range and all params", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "matrix", result: [] } });

      await rangeQuery("rate(up[5m])", "2024-01-01T00:00:00Z", "2024-01-01T01:00:00Z", "15s");

      expect(mockPromFetch).toHaveBeenCalledWith(
        "/query_range",
        {
          query: "rate(up[5m])",
          start: "2024-01-01T00:00:00Z",
          end: "2024-01-01T01:00:00Z",
          step: "15s",
        },
        undefined
      );
    });
  });

  describe("listMetrics", () => {
    it("calls label values for __name__", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: ["up", "process_cpu_seconds_total"] });

      const result = await listMetrics();

      expect(mockPromFetch).toHaveBeenCalledWith("/label/__name__/values", {}, undefined);
      expect(result.data).toContain("up");
    });

    it("passes match filter", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: [] });

      await listMetrics('{job="kiro"}');

      expect(mockPromFetch).toHaveBeenCalledWith(
        "/label/__name__/values",
        { "match[]": '{job="kiro"}' },
        undefined
      );
    });
  });

  describe("listLabelValues", () => {
    it("requests values for a specific label", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: ["kiro-api", "kiro-worker"] });

      const result = await listLabelValues("service");

      expect(mockPromFetch).toHaveBeenCalledWith("/label/service/values", undefined, undefined);
      expect(result.data).toEqual(["kiro-api", "kiro-worker"]);
    });
  });

  describe("getAlerts", () => {
    it("fetches /alerts endpoint", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { alerts: [] } });

      await getAlerts();

      expect(mockPromFetch).toHaveBeenCalledWith("/alerts", undefined, undefined);
    });
  });

  describe("getRules", () => {
    it("fetches /rules endpoint", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { groups: [] } });

      await getRules();

      expect(mockPromFetch).toHaveBeenCalledWith("/rules", undefined, undefined);
    });
  });

  describe("kiroFeatureUsage", () => {
    it("builds correct PromQL for feature usage rate", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await kiroFeatureUsage("command_.*", "10m");

      const call = mockPromFetch.mock.calls[0];
      expect(call[0]).toBe("/query");
      expect(call[1]?.query).toBe('rate(kiro_feature_invocations_total{feature=~"command_.*"}[10m])');
    });
  });

  describe("kiroSessionPerformance", () => {
    it("builds histogram_quantile query", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await kiroSessionPerformance(0.99, "1h");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).toBe("histogram_quantile(0.99, rate(kiro_session_duration_seconds_bucket[1h]))");
    });
  });

  describe("kiroModelUsage", () => {
    it("builds sum by model query", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await kiroModelUsage("2h");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).toBe('sum by (model) (rate(kiro_model_requests_total[2h]))');
    });
  });

  describe("kiroContextSize", () => {
    it("builds context token histogram query", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await kiroContextSize(0.95, "30m");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).toBe("histogram_quantile(0.95, rate(kiro_context_tokens_bucket[30m]))");
    });
  });

  describe("serviceErrorRates", () => {
    it("includes service filter when provided", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await serviceErrorRates("billing", "5m");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).toContain('service="billing"');
    });

    it("omits service filter when not provided", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await serviceErrorRates(undefined, "5m");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).not.toContain('service=');
    });
  });

  describe("kiroPromptSecurityDetections", () => {
    it("builds security detection rate query", async () => {
      mockPromFetch.mockResolvedValue({ status: "success", data: { resultType: "vector", result: [] } });

      await kiroPromptSecurityDetections("4h");

      const call = mockPromFetch.mock.calls[0];
      expect(call[1]?.query).toBe('sum by (detection_type) (rate(kiro_prompt_security_detections_total[4h]))');
    });
  });
});
