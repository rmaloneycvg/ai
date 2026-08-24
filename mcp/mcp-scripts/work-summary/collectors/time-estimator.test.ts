import { describe, it, expect } from "vitest";
import {
  commitActivityPoints,
  kiroActivityPoints,
  mergeIntoSessions,
  kiroTimeWindows,
  overlapsKiroSession,
  calculateOverlapMs,
  estimateEditTime,
} from "./time-estimator.js";
import type { GitCommitEntry, KiroSession } from "../types.js";

// ─── Helpers ────────────────────────────────────────────────────────────────

function makeCommit(timestamp: string): GitCommitEntry {
  return {
    hash: "abc",
    timestamp,
    message: "test",
    branch: "main",
    repoName: "repo",
    repoPath: "/repo",
    files: [],
    categories: [],
    aiAssisted: false,
  };
}

function makeKiroSession(createdAt: string, updatedAt: string): KiroSession {
  return {
    sessionId: "sess-1",
    createdAt,
    updatedAt,
    title: "Test",
    cwd: "/repo",
    promptCount: 5,
    toolCalls: {},
    durationMinutes: 0,
  };
}

function toMs(iso: string): number {
  return new Date(iso).getTime();
}

// ─── commitActivityPoints ───────────────────────────────────────────────────

describe("commitActivityPoints", () => {
  it("converts commits to activity points", () => {
    const commits = [
      makeCommit("2026-08-24T09:00:00Z"),
      makeCommit("2026-08-24T10:30:00Z"),
    ];
    const points = commitActivityPoints(commits);
    expect(points).toHaveLength(2);
    expect(points[0].source).toBe("commit");
    expect(points[0].timestamp).toBe(toMs("2026-08-24T09:00:00Z"));
  });

  it("returns empty for no commits", () => {
    expect(commitActivityPoints([])).toEqual([]);
  });
});

// ─── kiroActivityPoints ─────────────────────────────────────────────────────

describe("kiroActivityPoints", () => {
  it("creates start, intermediate, and end points for each session", () => {
    // 1 hour session = start + 3 intermediate (at 15, 30, 45 min) + end = 5 points
    const sessions = [makeKiroSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z")];
    const points = kiroActivityPoints(sessions);
    expect(points.length).toBeGreaterThanOrEqual(2);
    expect(points[0].source).toBe("kiro_start");
    expect(points[points.length - 1].source).toBe("kiro_end");
  });
});

// ─── mergeIntoSessions ──────────────────────────────────────────────────────

describe("mergeIntoSessions", () => {
  it("merges points within gap threshold into one session", () => {
    const points = [
      { timestamp: toMs("2026-08-24T09:00:00Z"), source: "commit" as const },
      { timestamp: toMs("2026-08-24T09:15:00Z"), source: "commit" as const },
      { timestamp: toMs("2026-08-24T09:25:00Z"), source: "commit" as const },
    ];

    const sessions = mergeIntoSessions(points, 30);
    expect(sessions).toHaveLength(1);
    expect(sessions[0].start).toBe(toMs("2026-08-24T09:00:00Z"));
    expect(sessions[0].end).toBe(toMs("2026-08-24T09:25:00Z"));
  });

  it("splits into multiple sessions when gap exceeds threshold", () => {
    const points = [
      { timestamp: toMs("2026-08-24T09:00:00Z"), source: "commit" as const },
      { timestamp: toMs("2026-08-24T09:10:00Z"), source: "commit" as const },
      // 2 hour gap
      { timestamp: toMs("2026-08-24T11:10:00Z"), source: "commit" as const },
      { timestamp: toMs("2026-08-24T11:30:00Z"), source: "commit" as const },
    ];

    const sessions = mergeIntoSessions(points, 30);
    expect(sessions).toHaveLength(2);
    expect(sessions[0].end).toBe(toMs("2026-08-24T09:10:00Z"));
    expect(sessions[1].start).toBe(toMs("2026-08-24T11:10:00Z"));
  });

  it("handles single point", () => {
    const points = [{ timestamp: toMs("2026-08-24T09:00:00Z"), source: "commit" as const }];
    const sessions = mergeIntoSessions(points, 30);
    expect(sessions).toHaveLength(1);
    expect(sessions[0].start).toBe(sessions[0].end);
  });

  it("returns empty for no points", () => {
    expect(mergeIntoSessions([], 30)).toEqual([]);
  });

  it("sorts unsorted points before merging", () => {
    const points = [
      { timestamp: toMs("2026-08-24T09:20:00Z"), source: "commit" as const },
      { timestamp: toMs("2026-08-24T09:00:00Z"), source: "commit" as const },
    ];

    const sessions = mergeIntoSessions(points, 30);
    expect(sessions).toHaveLength(1);
    expect(sessions[0].start).toBe(toMs("2026-08-24T09:00:00Z"));
    expect(sessions[0].end).toBe(toMs("2026-08-24T09:20:00Z"));
  });
});

// ─── overlapsKiroSession ────────────────────────────────────────────────────

describe("overlapsKiroSession", () => {
  const kiroWindows = [
    { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") },
  ];

  it("returns true for overlapping window", () => {
    const window = { start: toMs("2026-08-24T09:30:00Z"), end: toMs("2026-08-24T10:30:00Z") };
    expect(overlapsKiroSession(window, kiroWindows)).toBe(true);
  });

  it("returns true for window contained within kiro session", () => {
    const window = { start: toMs("2026-08-24T09:15:00Z"), end: toMs("2026-08-24T09:45:00Z") };
    expect(overlapsKiroSession(window, kiroWindows)).toBe(true);
  });

  it("returns false for non-overlapping window", () => {
    const window = { start: toMs("2026-08-24T11:00:00Z"), end: toMs("2026-08-24T12:00:00Z") };
    expect(overlapsKiroSession(window, kiroWindows)).toBe(false);
  });

  it("returns false for empty kiro windows", () => {
    const window = { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") };
    expect(overlapsKiroSession(window, [])).toBe(false);
  });
});

// ─── calculateOverlapMs ─────────────────────────────────────────────────────

describe("calculateOverlapMs", () => {
  it("calculates partial overlap", () => {
    const window = { start: toMs("2026-08-24T09:30:00Z"), end: toMs("2026-08-24T10:30:00Z") };
    const kiroWindows = [
      { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") },
    ];
    // Overlap: 09:30 to 10:00 = 30 minutes = 1800000 ms
    expect(calculateOverlapMs(window, kiroWindows)).toBe(30 * 60 * 1000);
  });

  it("calculates full containment", () => {
    const window = { start: toMs("2026-08-24T09:15:00Z"), end: toMs("2026-08-24T09:45:00Z") };
    const kiroWindows = [
      { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") },
    ];
    // Full window is inside kiro: 30 minutes
    expect(calculateOverlapMs(window, kiroWindows)).toBe(30 * 60 * 1000);
  });

  it("returns 0 for no overlap", () => {
    const window = { start: toMs("2026-08-24T11:00:00Z"), end: toMs("2026-08-24T12:00:00Z") };
    const kiroWindows = [
      { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") },
    ];
    expect(calculateOverlapMs(window, kiroWindows)).toBe(0);
  });

  it("sums overlap across multiple kiro sessions", () => {
    const window = { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T15:00:00Z") };
    const kiroWindows = [
      { start: toMs("2026-08-24T09:00:00Z"), end: toMs("2026-08-24T10:00:00Z") }, // 1hr
      { start: toMs("2026-08-24T14:00:00Z"), end: toMs("2026-08-24T15:00:00Z") }, // 1hr
    ];
    expect(calculateOverlapMs(window, kiroWindows)).toBe(2 * 60 * 60 * 1000);
  });
});

// ─── estimateEditTime ───────────────────────────────────────────────────────

describe("estimateEditTime", () => {
  it("returns zeros for no activity", () => {
    const result = estimateEditTime({
      commits: [],
      kiroSessions: [],
      gapMinutes: 30,
    });
    expect(result.totalEditMinutes).toBe(0);
    expect(result.aiAssistedMinutes).toBe(0);
    expect(result.manualMinutes).toBe(0);
    expect(result.sessions).toEqual([]);
  });

  it("counts single commit as 1 minute", () => {
    const result = estimateEditTime({
      commits: [makeCommit("2026-08-24T09:00:00Z")],
      kiroSessions: [],
      gapMinutes: 30,
    });
    expect(result.totalEditMinutes).toBe(1);
    expect(result.manualMinutes).toBe(1);
    expect(result.aiAssistedMinutes).toBe(0);
  });

  it("calculates time between clustered commits", () => {
    const result = estimateEditTime({
      commits: [
        makeCommit("2026-08-24T09:00:00Z"),
        makeCommit("2026-08-24T09:30:00Z"),
        makeCommit("2026-08-24T10:00:00Z"),
      ],
      kiroSessions: [],
      gapMinutes: 30,
    });
    // One session from 09:00 to 10:00 = 60 minutes
    expect(result.totalEditMinutes).toBe(60);
    expect(result.manualMinutes).toBe(60);
  });

  it("flags AI-assisted time when overlapping with Kiro session", () => {
    // Kiro session runs 08:50 to 09:40
    // Commits at 09:00 and 09:30
    // Kiro start/end are also activity points, so merged session is 08:50 to 09:40 = 50 min
    const result = estimateEditTime({
      commits: [
        makeCommit("2026-08-24T09:00:00Z"),
        makeCommit("2026-08-24T09:30:00Z"),
      ],
      kiroSessions: [
        makeKiroSession("2026-08-24T08:50:00Z", "2026-08-24T09:40:00Z"),
      ],
      gapMinutes: 30,
    });
    expect(result.totalEditMinutes).toBe(50);
    expect(result.aiAssistedMinutes).toBe(50);
    expect(result.manualMinutes).toBe(0);
    expect(result.sessions[0].aiAssisted).toBe(true);
  });

  it("splits AI and manual sessions correctly", () => {
    // Morning commits: 09:00, 09:30 (no kiro overlap) = 30 min manual
    // Afternoon: Kiro session 13:50-14:40, commits at 14:00, 14:30
    // Afternoon session merges kiro_start(13:50) + commits + kiro_end(14:40) = 50 min AI
    const result = estimateEditTime({
      commits: [
        makeCommit("2026-08-24T09:00:00Z"),
        makeCommit("2026-08-24T09:30:00Z"),
        makeCommit("2026-08-24T14:00:00Z"),
        makeCommit("2026-08-24T14:30:00Z"),
      ],
      kiroSessions: [
        makeKiroSession("2026-08-24T13:50:00Z", "2026-08-24T14:40:00Z"),
      ],
      gapMinutes: 30,
    });

    expect(result.sessions).toHaveLength(2);
    expect(result.sessions[0].aiAssisted).toBe(false);
    expect(result.sessions[1].aiAssisted).toBe(true);
    expect(result.sessions[0].durationMinutes).toBe(30);
    expect(result.sessions[1].durationMinutes).toBe(50);
    expect(result.totalEditMinutes).toBe(80);
    expect(result.manualMinutes).toBe(30);
    expect(result.aiAssistedMinutes).toBe(50);
  });

  it("includes file mtimes in activity points", () => {
    const result = estimateEditTime({
      commits: [makeCommit("2026-08-24T09:00:00Z")],
      kiroSessions: [],
      fileMtimes: [toMs("2026-08-24T09:20:00Z")],
      gapMinutes: 30,
    });
    // Merged: 09:00 to 09:20 = 20 minutes
    expect(result.totalEditMinutes).toBe(20);
  });

  it("includes Kiro sessions even without commits", () => {
    // Kiro session 14:00 to 15:30 = 90 min
    // Activity points: kiro_start + kiro_end, merged into one session
    const result = estimateEditTime({
      commits: [],
      kiroSessions: [
        makeKiroSession("2026-08-24T14:00:00Z", "2026-08-24T15:30:00Z"),
      ],
      gapMinutes: 30,
    });
    // Session from kiro_start to kiro_end = 90 minutes
    expect(result.totalEditMinutes).toBe(90);
    expect(result.aiAssistedMinutes).toBe(90);
  });
});
