import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  searchDashboards,
  getDashboard,
  getDashboardVersions,
  queryDatasource,
  getAnnotations,
  listDatasources,
} from "./queries.js";

vi.mock("./client.js", () => ({
  getConfig: () => ({ baseUrl: "http://grafana:3000", apiKey: "test-key", orgId: undefined }),
  grafanaFetch: vi.fn(),
}));

import { grafanaFetch } from "./client.js";
const mockGrafanaFetch = vi.mocked(grafanaFetch);

describe("grafana/queries", () => {
  beforeEach(() => {
    mockGrafanaFetch.mockReset();
  });

  describe("searchDashboards", () => {
    it("searches with type=dash-db", async () => {
      mockGrafanaFetch.mockResolvedValue([{ uid: "abc", title: "Kiro Metrics" }]);

      const result = await searchDashboards("kiro");

      expect(mockGrafanaFetch).toHaveBeenCalledWith(
        "/search",
        { params: expect.objectContaining({ type: "dash-db", query: "kiro" }) },
        undefined
      );
      expect(result[0].title).toBe("Kiro Metrics");
    });

    it("includes tags filter when provided", async () => {
      mockGrafanaFetch.mockResolvedValue([]);

      await searchDashboards(undefined, ["telemetry", "kiro"]);

      const call = mockGrafanaFetch.mock.calls[0];
      expect(call[1]).toEqual({ params: { type: "dash-db", tag: "telemetry,kiro" } });
    });
  });

  describe("getDashboard", () => {
    it("fetches dashboard by UID", async () => {
      const mockDashboard = {
        meta: { url: "/d/abc/kiro" },
        dashboard: { uid: "abc", title: "Kiro", panels: [] },
      };
      mockGrafanaFetch.mockResolvedValue(mockDashboard);

      const result = await getDashboard("abc");

      expect(mockGrafanaFetch).toHaveBeenCalledWith("/dashboards/uid/abc", undefined, undefined);
      expect(result.dashboard.title).toBe("Kiro");
    });
  });

  describe("getDashboardVersions", () => {
    it("fetches version history with limit", async () => {
      mockGrafanaFetch.mockResolvedValue([{ version: 1 }, { version: 2 }]);

      await getDashboardVersions(42, 5);

      expect(mockGrafanaFetch).toHaveBeenCalledWith(
        "/dashboards/id/42/versions",
        { params: { limit: "5" } },
        undefined
      );
    });
  });

  describe("queryDatasource", () => {
    it("sends POST with queries and time range", async () => {
      mockGrafanaFetch.mockResolvedValue({ results: { A: { frames: [] } } });

      await queryDatasource({
        queries: [{ refId: "A", datasource: { type: "prometheus", uid: "prom-1" }, expr: "up" }],
        from: "now-1h",
        to: "now",
      });

      expect(mockGrafanaFetch).toHaveBeenCalledWith(
        "/ds/query",
        {
          method: "POST",
          body: {
            queries: [{ refId: "A", datasource: { type: "prometheus", uid: "prom-1" }, expr: "up" }],
            from: "now-1h",
            to: "now",
          },
        },
        undefined
      );
    });
  });

  describe("getAnnotations", () => {
    it("passes dashboard UID and tags", async () => {
      mockGrafanaFetch.mockResolvedValue([{ id: 1, text: "Deploy v1.0" }]);

      await getAnnotations("dash-1", undefined, undefined, ["deployment"], 10);

      expect(mockGrafanaFetch).toHaveBeenCalledWith(
        "/annotations",
        { params: { dashboardUID: "dash-1", tags: "deployment", limit: "10" } },
        undefined
      );
    });
  });

  describe("listDatasources", () => {
    it("fetches all datasources", async () => {
      mockGrafanaFetch.mockResolvedValue([
        { uid: "prom-1", name: "Prometheus", type: "prometheus" },
        { uid: "jaeger-1", name: "Jaeger", type: "jaeger" },
      ]);

      const result = await listDatasources();

      expect(mockGrafanaFetch).toHaveBeenCalledWith("/datasources", undefined, undefined);
      expect(result).toHaveLength(2);
    });
  });
});
