import { describe, it, expect } from "vitest";
import {
  buildSessionWindows,
  findMatchingSession,
  isCwdMatch,
  flagAiAssistedCommits,
} from "./ai-flagger.js";
import type { GitCommitEntry, KiroSession } from "./types.js";

// ─── Helpers ────────────────────────────────────────────────────────────────

function makeCommit(timestamp: string, repoPath = "/home/user/workspace/project"): GitCommitEntry {
  return {
    hash: "abc123",
    timestamp,
    message: "test commit",
    branch: "main",
    repoName: "project",
    repoPath,
    files: [{ path: "src/file.ts", status: "M" }],
    categories: ["feature"],
    aiAssisted: false,
  };
}

function makeSession(
  createdAt: string,
  updatedAt: string,
  cwd = "/home/user/workspace/project"
): KiroSession {
  return {
    sessionId: `sess-${createdAt}`,
    createdAt,
    updatedAt,
    title: "Test Session",
    cwd,
    promptCount: 5,
    toolCalls: { read_file: 3, grep_search: 2 },
    durationMinutes: 60,
  };
}

// ─── buildSessionWindows ────────────────────────────────────────────────────

describe("buildSessionWindows", () => {
  it("converts sessions to time windows", () => {
    const sessions = [makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z")];
    const windows = buildSessionWindows(sessions);
    expect(windows).toHaveLength(1);
    expect(windows[0].sessionId).toBe("sess-2026-08-24T09:00:00Z");
    expect(windows[0].start).toBe(new Date("2026-08-24T09:00:00Z").getTime());
    expect(windows[0].end).toBe(new Date("2026-08-24T10:00:00Z").getTime());
    expect(windows[0].cwd).toBe("/home/user/workspace/project");
  });

  it("handles empty sessions array", () => {
    expect(buildSessionWindows([])).toEqual([]);
  });
});

// ─── isCwdMatch ─────────────────────────────────────────────────────────────

describe("isCwdMatch", () => {
  it("matches exact paths", () => {
    expect(isCwdMatch("/home/user/workspace/project", "/home/user/workspace/project")).toBe(true);
  });

  it("matches when session cwd is within repo", () => {
    expect(isCwdMatch(
      "/home/user/workspace/project/src",
      "/home/user/workspace/project"
    )).toBe(true);
  });

  it("matches when repo is within session cwd", () => {
    expect(isCwdMatch(
      "/home/user/workspace",
      "/home/user/workspace/project"
    )).toBe(true);
  });

  it("does not match unrelated paths", () => {
    expect(isCwdMatch(
      "/home/user/workspace/other-project",
      "/home/user/workspace/project"
    )).toBe(false);
  });

  it("handles trailing slashes", () => {
    expect(isCwdMatch(
      "/home/user/workspace/project/",
      "/home/user/workspace/project"
    )).toBe(true);
  });

  it("returns false for empty strings", () => {
    expect(isCwdMatch("", "/path")).toBe(false);
    expect(isCwdMatch("/path", "")).toBe(false);
  });
});

// ─── findMatchingSession ────────────────────────────────────────────────────

describe("findMatchingSession", () => {
  const windows = buildSessionWindows([
    makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z", "/home/user/workspace/project"),
    makeSession("2026-08-24T14:00:00Z", "2026-08-24T16:00:00Z", "/home/user/workspace/other"),
  ]);

  it("finds matching session by time overlap", () => {
    const match = findMatchingSession(
      "2026-08-24T09:30:00Z",
      "/anywhere",
      windows
    );
    expect(match).not.toBeNull();
    expect(match!.sessionId).toBe("sess-2026-08-24T09:00:00Z");
  });

  it("returns null when no time overlap", () => {
    const match = findMatchingSession(
      "2026-08-24T12:00:00Z",
      "/anywhere",
      windows
    );
    expect(match).toBeNull();
  });

  it("matches at exact session start", () => {
    const match = findMatchingSession("2026-08-24T09:00:00Z", "/path", windows);
    expect(match).not.toBeNull();
  });

  it("matches at exact session end", () => {
    const match = findMatchingSession("2026-08-24T10:00:00Z", "/path", windows);
    expect(match).not.toBeNull();
  });

  it("prefers cwd-matching session when matchCwd is true", () => {
    const match = findMatchingSession(
      "2026-08-24T14:30:00Z",
      "/home/user/workspace/other",
      windows,
      { matchCwd: true }
    );
    expect(match).not.toBeNull();
    expect(match!.sessionId).toBe("sess-2026-08-24T14:00:00Z");
  });

  it("falls back to time-only match when cwd doesn't match", () => {
    const match = findMatchingSession(
      "2026-08-24T14:30:00Z",
      "/home/user/workspace/unrelated",
      windows,
      { matchCwd: true }
    );
    // Should still match by time even though cwd doesn't match
    expect(match).not.toBeNull();
  });
});

// ─── flagAiAssistedCommits ──────────────────────────────────────────────────

describe("flagAiAssistedCommits", () => {
  it("flags commits that overlap with Kiro sessions", () => {
    const commits = [
      makeCommit("2026-08-24T09:30:00Z"),
      makeCommit("2026-08-24T12:00:00Z"), // No overlap
    ];
    const sessions = [
      makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z"),
    ];

    const result = flagAiAssistedCommits(commits, sessions);
    expect(result[0].aiAssisted).toBe(true);
    expect(result[0].sessionId).toBe("sess-2026-08-24T09:00:00Z");
    expect(result[1].aiAssisted).toBe(false);
    expect(result[1].sessionId).toBeUndefined();
  });

  it("handles multiple sessions", () => {
    const commits = [
      makeCommit("2026-08-24T09:30:00Z"),
      makeCommit("2026-08-24T14:30:00Z"),
      makeCommit("2026-08-24T18:00:00Z"), // No overlap
    ];
    const sessions = [
      makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z"),
      makeSession("2026-08-24T14:00:00Z", "2026-08-24T15:00:00Z"),
    ];

    const result = flagAiAssistedCommits(commits, sessions);
    expect(result[0].aiAssisted).toBe(true);
    expect(result[1].aiAssisted).toBe(true);
    expect(result[2].aiAssisted).toBe(false);
  });

  it("returns commits unchanged when no sessions", () => {
    const commits = [makeCommit("2026-08-24T09:30:00Z")];
    const result = flagAiAssistedCommits(commits, []);
    expect(result[0].aiAssisted).toBe(false);
  });

  it("handles empty commits array", () => {
    const sessions = [makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z")];
    const result = flagAiAssistedCommits([], sessions);
    expect(result).toEqual([]);
  });

  it("mutates commits in place", () => {
    const commits = [makeCommit("2026-08-24T09:30:00Z")];
    const sessions = [makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z")];

    const result = flagAiAssistedCommits(commits, sessions);
    expect(result).toBe(commits); // Same reference
    expect(commits[0].aiAssisted).toBe(true);
  });

  it("uses cwd matching when preferCwdMatch is set", () => {
    const commits = [
      makeCommit("2026-08-24T09:30:00Z", "/home/user/workspace/project"),
    ];
    const sessions = [
      makeSession("2026-08-24T09:00:00Z", "2026-08-24T10:00:00Z", "/home/user/workspace/project"),
    ];

    const result = flagAiAssistedCommits(commits, sessions, { preferCwdMatch: true });
    expect(result[0].aiAssisted).toBe(true);
  });
});
