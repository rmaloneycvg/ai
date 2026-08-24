import { describe, it, expect } from "vitest";
import {
  formatDuration,
  buildTimeline,
  countCategories,
  buildFilesChanged,
  renderJson,
  renderMarkdown,
} from "./renderer.js";
import type { GitCommitEntry, KiroCollectorData, ChromeCollectorData, RenderInput } from "./renderer.js";

// ─── Helpers ────────────────────────────────────────────────────────────────

function makeCommit(overrides: Partial<GitCommitEntry> = {}): GitCommitEntry {
  return {
    hash: "abc123",
    timestamp: "2026-08-24T09:30:00Z",
    message: "feat: add login",
    branch: "main",
    repoName: "my-app",
    repoPath: "/home/user/workspace/my-app",
    files: [{ path: "src/login.ts", status: "A" }],
    categories: ["feature"],
    aiAssisted: true,
    sessionId: "sess-1",
    ...overrides,
  };
}

const mockKiroData: KiroCollectorData = {
  sessions: [
    {
      sessionId: "sess-1",
      createdAt: "2026-08-24T09:00:00Z",
      updatedAt: "2026-08-24T10:30:00Z",
      title: "Login feature",
      cwd: "/home/user/workspace/my-app",
      promptCount: 12,
      toolCalls: { read_file: 8, grep_search: 5, execute_bash: 3 },
      durationMinutes: 90,
    },
  ],
  totalDurationMinutes: 90,
  totalPrompts: 12,
  toolUsageAggregate: { read_file: 8, grep_search: 5, execute_bash: 3 },
};

const mockChromeData: ChromeCollectorData = {
  entries: [
    { timestamp: "2026-08-24T09:15:00Z", url: "https://google.com/search?q=typescript+generics", title: "typescript generics", category: "search", searchQuery: "typescript generics" },
    { timestamp: "2026-08-24T10:00:00Z", url: "chrome-devtools://devtools/bundled/inspector.html", title: "DevTools", category: "devtools" },
  ],
  searchCount: 1,
  devToolsSessions: 1,
};

// ─── formatDuration ─────────────────────────────────────────────────────────

describe("formatDuration", () => {
  it("formats zero", () => expect(formatDuration(0)).toBe("0m"));
  it("formats minutes only", () => expect(formatDuration(45)).toBe("45m"));
  it("formats hours only", () => expect(formatDuration(120)).toBe("2h"));
  it("formats hours and minutes", () => expect(formatDuration(90)).toBe("1h 30m"));
  it("formats large values", () => expect(formatDuration(510)).toBe("8h 30m"));
  it("handles negative as zero", () => expect(formatDuration(-5)).toBe("0m"));
});

// ─── buildTimeline ──────────────────────────────────────────────────────────

describe("buildTimeline", () => {
  it("combines commits, kiro sessions, and chrome entries chronologically", () => {
    const commits = [makeCommit()];
    const timeline = buildTimeline(commits, mockKiroData, mockChromeData);

    expect(timeline.length).toBeGreaterThan(0);
    // Should be sorted by timestamp
    for (let i = 1; i < timeline.length; i++) {
      expect(timeline[i].timestamp >= timeline[i - 1].timestamp).toBe(true);
    }
  });

  it("includes commit entries with repo and AI flag", () => {
    const commits = [makeCommit()];
    const timeline = buildTimeline(commits, null, null);

    expect(timeline).toHaveLength(1);
    expect(timeline[0].type).toBe("commit");
    expect(timeline[0].description).toContain("my-app");
    expect(timeline[0].description).toContain("feat: add login");
    expect(timeline[0].aiAssisted).toBe(true);
  });

  it("includes Kiro session entries", () => {
    const timeline = buildTimeline([], mockKiroData, null);
    expect(timeline).toHaveLength(1);
    expect(timeline[0].type).toBe("ai_session");
    expect(timeline[0].description).toContain("Login feature");
  });

  it("includes search and devtools entries from Chrome", () => {
    const timeline = buildTimeline([], null, mockChromeData);
    expect(timeline).toHaveLength(2);
    expect(timeline[0].type).toBe("search");
    expect(timeline[0].description).toContain("typescript generics");
    expect(timeline[1].type).toBe("devtools");
  });

  it("handles all null data", () => {
    expect(buildTimeline([], null, null)).toEqual([]);
  });
});

// ─── countCategories ────────────────────────────────────────────────────────

describe("countCategories", () => {
  it("counts commits per category", () => {
    const commits = [
      makeCommit({ categories: ["feature"] }),
      makeCommit({ categories: ["feature", "unit-test"] }),
      makeCommit({ categories: ["refactor"] }),
      makeCommit({ categories: ["documentation"] }),
    ];

    const counts = countCategories(commits);
    expect(counts.features).toBe(2);
    expect(counts.unitTests).toBe(1);
    expect(counts.refactors).toBe(1);
    expect(counts.docs).toBe(1);
    expect(counts.integrationTests).toBe(0);
    expect(counts.perfTests).toBe(0);
  });

  it("returns zeros for empty commits", () => {
    const counts = countCategories([]);
    expect(counts.features).toBe(0);
    expect(counts.refactors).toBe(0);
  });
});

// ─── buildFilesChanged ──────────────────────────────────────────────────────

describe("buildFilesChanged", () => {
  it("deduplicates files across commits", () => {
    const commits = [
      makeCommit({ files: [{ path: "src/app.ts", status: "M" }] }),
      makeCommit({ files: [{ path: "src/app.ts", status: "M" }] }),
    ];

    const files = buildFilesChanged(commits);
    expect(files).toHaveLength(1);
  });

  it("includes files from different repos separately", () => {
    const commits = [
      makeCommit({ repoName: "repo-a", files: [{ path: "src/file.ts", status: "A" }] }),
      makeCommit({ repoName: "repo-b", files: [{ path: "src/file.ts", status: "A" }] }),
    ];

    const files = buildFilesChanged(commits);
    expect(files).toHaveLength(2);
  });

  it("returns empty for no commits", () => {
    expect(buildFilesChanged([])).toEqual([]);
  });
});

// ─── renderJson ─────────────────────────────────────────────────────────────

describe("renderJson", () => {
  const input: RenderInput = {
    date: "2026-08-24",
    authorName: "Ryan Maloney",
    commits: [makeCommit()],
    kiroData: mockKiroData,
    chromeData: mockChromeData,
    communications: { teams: null, googleMeet: null, zoom: null, slack: null, outlook: null },
    timeEstimate: {
      totalEditMinutes: 90,
      aiAssistedMinutes: 60,
      manualMinutes: 30,
      sessions: [],
    },
  };

  it("produces valid WorkSummary structure", () => {
    const result = renderJson(input);
    expect(result.date).toBe("2026-08-24");
    expect(result.author).toBe("Ryan Maloney");
    expect(result.summary.totalCommits).toBe(1);
    expect(result.summary.totalEditTime).toBe("1h 30m");
    expect(result.summary.aiAssistedTime).toBe("1h");
    expect(result.summary.manualTime).toBe("30m");
  });

  it("includes timeline entries", () => {
    const result = renderJson(input);
    expect(result.timeline.length).toBeGreaterThan(0);
  });

  it("includes AI session data", () => {
    const result = renderJson(input);
    expect(result.aiSessions.count).toBe(1);
    expect(result.aiSessions.totalDuration).toBe("1h 30m");
    expect(result.aiSessions.toolUsage.read_file).toBe(8);
  });

  it("includes browser activity", () => {
    const result = renderJson(input);
    expect(result.browserActivity.searches).toHaveLength(1);
    expect(result.browserActivity.devToolsSessions).toBe(1);
  });

  it("includes communication data (null for stubs)", () => {
    const result = renderJson(input);
    expect(result.communications.teams).toBeNull();
    expect(result.communications.slack).toBeNull();
  });

  it("includes time breakdown", () => {
    const result = renderJson(input);
    expect(result.timeBreakdown.coding).toBe("1h 30m");
    expect(result.timeBreakdown.aiPaired).toBe("1h");
    expect(result.timeBreakdown.manual).toBe("30m");
  });
});

// ─── renderMarkdown ─────────────────────────────────────────────────────────

describe("renderMarkdown", () => {
  const input: RenderInput = {
    date: "2026-08-24",
    authorName: "Ryan Maloney",
    commits: [
      makeCommit(),
      makeCommit({ message: "docs: update readme", categories: ["documentation"], timestamp: "2026-08-24T11:00:00Z" }),
    ],
    kiroData: mockKiroData,
    chromeData: mockChromeData,
    communications: { teams: null, googleMeet: null, zoom: null, slack: null, outlook: null },
    timeEstimate: {
      totalEditMinutes: 90,
      aiAssistedMinutes: 60,
      manualMinutes: 30,
      sessions: [],
    },
  };

  it("produces markdown with all sections", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);

    expect(md).toContain("# Daily Work Summary — 2026-08-24");
    expect(md).toContain("## Summary");
    expect(md).toContain("## Timeline");
    expect(md).toContain("## Accomplishments by Category");
    expect(md).toContain("## Files Changed");
    expect(md).toContain("## AI Activity");
    expect(md).toContain("## Browser Research");
    expect(md).toContain("## Communications");
    expect(md).toContain("## Time Breakdown");
  });

  it("includes author name", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("Ryan Maloney");
  });

  it("includes commit entries in timeline", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("feat: add login");
  });

  it("includes AI flags in timeline", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("🤖");
  });

  it("includes tool usage in AI section", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("`read_file`");
    expect(md).toContain("`grep_search`");
  });

  it("includes search queries in browser section", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("typescript generics");
  });

  it("shows not configured for communications", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("Communication collectors not configured");
  });

  it("includes files changed table", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("`src/login.ts`");
  });

  it("includes time breakdown table", () => {
    const json = renderJson(input);
    const md = renderMarkdown(json);
    expect(md).toContain("| Coding | 1h 30m |");
    expect(md).toContain("| AI-Paired | 1h |");
    expect(md).toContain("| Manual | 30m |");
  });
});
