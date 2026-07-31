import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  listServices,
  listOperations,
  searchTraces,
  getTrace,
  getDependencies,
  summarizeTrace,
  analyzeBottlenecks,
  kiroSlowSessions,
  kiroSessionsByCommand,
  kiroSessionTrace,
  kiroTracesByModel,
  kiroSecurityTraces,
} from "./queries.js";
import type { JaegerTrace } from "./client.js";

vi.mock("./client.js", () => ({
  getConfig: () => ({ baseUrl: "http://jaeger:16686", authToken: undefined }),
  jaegerFetch: vi.fn(),
}));

import { jaegerFetch } from "./client.js";
const mockJaegerFetch = vi.mocked(jaegerFetch);

describe("jaeger/queries", () => {
  beforeEach(() => {
    mockJaegerFetch.mockReset();
  });

  describe("listServices", () => {
    it("fetches /services endpoint", async () => {
      mockJaegerFetch.mockResolvedValue({ data: ["api", "worker"], total: 2, limit: 0, offset: 0 });

      const result = await listServices();

      expect(mockJaegerFetch).toHaveBeenCalledWith("/services", undefined, undefined);
      expect(result.data).toEqual(["api", "worker"]);
    });
  });

  describe("listOperations", () => {
    it("fetches operations for a service", async () => {
      mockJaegerFetch.mockResolvedValue({ data: ["GET /users", "POST /users"], total: 2, limit: 0, offset: 0 });

      const result = await listOperations("api");

      expect(mockJaegerFetch).toHaveBeenCalledWith("/services/api/operations", undefined, undefined);
      expect(result.data).toHaveLength(2);
    });
  });

  describe("searchTraces", () => {
    it("passes service and limit", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 10, offset: 0 });

      await searchTraces({ service: "kiro", limit: 10 });

      expect(mockJaegerFetch).toHaveBeenCalledWith(
        "/traces",
        expect.objectContaining({ service: "kiro", limit: "10" }),
        undefined
      );
    });

    it("serializes tags as JSON", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 20, offset: 0 });

      await searchTraces({ service: "kiro", tags: { "http.status_code": "500" } });

      const params = mockJaegerFetch.mock.calls[0][1] as Record<string, string>;
      expect(JSON.parse(params.tags)).toEqual({ "http.status_code": "500" });
    });

    it("includes duration filters when provided", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 20, offset: 0 });

      await searchTraces({ service: "kiro", minDuration: "1s", maxDuration: "10s" });

      expect(mockJaegerFetch).toHaveBeenCalledWith(
        "/traces",
        expect.objectContaining({ minDuration: "1s", maxDuration: "10s" }),
        undefined
      );
    });
  });

  describe("getTrace", () => {
    it("fetches specific trace by ID", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [{ traceID: "abc123", spans: [], processes: {} }] });

      await getTrace("abc123");

      expect(mockJaegerFetch).toHaveBeenCalledWith("/traces/abc123", undefined, undefined);
    });
  });

  describe("getDependencies", () => {
    it("fetches service dependencies", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [{ parent: "api", child: "db", callCount: 100 }] });

      await getDependencies("1234567890", "3600000");

      expect(mockJaegerFetch).toHaveBeenCalledWith(
        "/dependencies",
        { endTs: "1234567890", lookback: "3600000" },
        undefined
      );
    });
  });

  describe("summarizeTrace", () => {
    it("calculates duration and service breakdown", () => {
      const trace: JaegerTrace = {
        traceID: "trace-1",
        spans: [
          {
            traceID: "trace-1",
            spanID: "span-1",
            operationName: "GET /users",
            references: [],
            startTime: 1000000,
            duration: 500000, // 500ms
            tags: [],
            logs: [],
            processID: "p1",
          },
          {
            traceID: "trace-1",
            spanID: "span-2",
            operationName: "SELECT users",
            references: [{ refType: "CHILD_OF", traceID: "trace-1", spanID: "span-1" }],
            startTime: 1200000,
            duration: 300000, // 300ms
            tags: [],
            logs: [],
            processID: "p2",
          },
        ],
        processes: {
          p1: { serviceName: "api", tags: [] },
          p2: { serviceName: "database", tags: [] },
        },
      };

      const summary = summarizeTrace(trace);

      expect(summary.traceId).toBe("trace-1");
      expect(summary.spanCount).toBe(2);
      expect(summary.totalDurationMs).toBe(500); // 500ms total from first span
      expect(summary.serviceBreakdown.api).toEqual({ count: 1, totalDuration: 500000 });
      expect(summary.serviceBreakdown.database).toEqual({ count: 1, totalDuration: 300000 });
    });

    it("identifies slow spans (> 10% of total duration)", () => {
      const trace: JaegerTrace = {
        traceID: "trace-2",
        spans: [
          {
            traceID: "trace-2",
            spanID: "s1",
            operationName: "fast-op",
            references: [],
            startTime: 0,
            duration: 10000, // 10ms
            tags: [],
            logs: [],
            processID: "p1",
          },
          {
            traceID: "trace-2",
            spanID: "s2",
            operationName: "slow-op",
            references: [],
            startTime: 10000,
            duration: 990000, // 990ms
            tags: [{ key: "db.type", type: "string", value: "postgres" }],
            logs: [],
            processID: "p1",
          },
        ],
        processes: { p1: { serviceName: "api", tags: [] } },
      };

      const summary = summarizeTrace(trace);

      expect(summary.slowSpans).toHaveLength(1);
      expect(summary.slowSpans[0].operationName).toBe("slow-op");
      expect(summary.slowSpans[0].tags["db.type"]).toBe("postgres");
    });

    it("identifies error spans", () => {
      const trace: JaegerTrace = {
        traceID: "trace-3",
        spans: [
          {
            traceID: "trace-3",
            spanID: "s1",
            operationName: "failing-op",
            references: [],
            startTime: 0,
            duration: 100000,
            tags: [{ key: "error", type: "bool", value: true }],
            logs: [],
            processID: "p1",
          },
        ],
        processes: { p1: { serviceName: "api", tags: [] } },
      };

      const summary = summarizeTrace(trace);

      expect(summary.errors).toHaveLength(1);
      expect(summary.errors[0].operationName).toBe("failing-op");
    });
  });

  describe("analyzeBottlenecks", () => {
    it("ranks operations by total time contribution", () => {
      const traces: JaegerTrace[] = [
        {
          traceID: "t1",
          spans: [
            { traceID: "t1", spanID: "s1", operationName: "db-query", references: [], startTime: 0, duration: 800000, tags: [], logs: [], processID: "p1" },
            { traceID: "t1", spanID: "s2", operationName: "serialize", references: [], startTime: 0, duration: 200000, tags: [], logs: [], processID: "p1" },
          ],
          processes: { p1: { serviceName: "api", tags: [] } },
        },
        {
          traceID: "t2",
          spans: [
            { traceID: "t2", spanID: "s3", operationName: "db-query", references: [], startTime: 0, duration: 900000, tags: [], logs: [], processID: "p1" },
          ],
          processes: { p1: { serviceName: "api", tags: [] } },
        },
      ];

      const analysis = analyzeBottlenecks(traces);

      expect(analysis.traceCount).toBe(2);
      expect(analysis.topOperations[0].name).toBe("api::db-query");
      expect(analysis.topOperations[0].count).toBe(2);
      expect(analysis.topOperations[0].maxMs).toBe(900);
    });
  });

  describe("kiro-specific queries", () => {
    it("kiroSlowSessions searches with min duration and kiro tags", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 10, offset: 0 });

      await kiroSlowSessions("3s", 5);

      expect(mockJaegerFetch).toHaveBeenCalledWith(
        "/traces",
        expect.objectContaining({
          service: "kiro-session-handler",
          minDuration: "3s",
          limit: "5",
        }),
        undefined
      );
    });

    it("kiroSessionsByCommand searches by command type tag", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 20, offset: 0 });

      await kiroSessionsByCommand("code_review");

      const params = mockJaegerFetch.mock.calls[0][1] as Record<string, string>;
      expect(JSON.parse(params.tags)).toEqual({ "kiro.command.type": "code_review" });
    });

    it("kiroSessionTrace searches by session ID", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 1, offset: 0 });

      await kiroSessionTrace("sess-abc-123");

      const params = mockJaegerFetch.mock.calls[0][1] as Record<string, string>;
      expect(JSON.parse(params.tags)).toEqual({ "kiro.session.id": "sess-abc-123" });
    });

    it("kiroTracesByModel searches by model tag", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 20, offset: 0 });

      await kiroTracesByModel("claude-sonnet-5");

      const params = mockJaegerFetch.mock.calls[0][1] as Record<string, string>;
      expect(JSON.parse(params.tags)).toEqual({ "kiro.model.name": "claude-sonnet-5" });
    });

    it("kiroSecurityTraces searches for flagged traces", async () => {
      mockJaegerFetch.mockResolvedValue({ data: [], total: 0, limit: 20, offset: 0 });

      await kiroSecurityTraces();

      const params = mockJaegerFetch.mock.calls[0][1] as Record<string, string>;
      expect(JSON.parse(params.tags)).toEqual({ "kiro.security.flagged": "true" });
    });
  });
});
