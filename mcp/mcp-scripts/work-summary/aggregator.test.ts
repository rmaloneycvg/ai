import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock all collectors
vi.mock("./collectors/git-collector.js", () => ({
  collectGitCommits: vi.fn(),
}));
vi.mock("./collectors/kiro-collector.js", () => ({
  collectKiroSessions: vi.fn(),
}));
vi.mock("./collectors/chrome-collector.js", () => ({
  collectChromeHistory: vi.fn(),
}));
vi.mock("./collectors/teams-collector.js", () => ({
  collectTeamsMeetings: vi.fn(),
}));
vi.mock("./collectors/google-meet-collector.js", () => ({
  collectGoogleMeetMeetings: vi.fn(),
}));
vi.mock("./collectors/zoom-collector.js", () => ({
  collectZoomMeetings: vi.fn(),
}));
vi.mock("./collectors/slack-collector.js", () => ({
  collectSlackActivity: vi.fn(),
}));
vi.mock("./collectors/outlook-collector.js", () => ({
  collectOutlookEmails: vi.fn(),
}));

// Mock config to avoid file system reads
vi.mock("./config.js", () => ({
  loadConfig: vi.fn(() => ({
    workspacePaths: ["~/workspace"],
    author: { name: "Test User", email: "test@example.com" },
    sessionGapMinutes: 30,
    outputDir: "/tmp/work-summaries-test",
    collectors: {
      git: { enabled: true },
      kiro: { enabled: true },
      chrome: { enabled: false },
      teams: { enabled: false },
      "google-meet": { enabled: false },
      zoom: { enabled: false },
      slack: { enabled: false },
      outlook: { enabled: false },
    },
  })),
  expandHome: vi.fn((p: string) => p.replace("~", "/home/test")),
  isCollectorEnabled: vi.fn((config: any, name: string) => config.collectors[name]?.enabled ?? false),
}));

// Mock fs to prevent actual file writes
vi.mock("node:fs", async () => {
  const actual = await vi.importActual("node:fs");
  return {
    ...actual,
    existsSync: vi.fn(() => true),
    mkdirSync: vi.fn(),
    writeFileSync: vi.fn(),
  };
});

import { generateSummary } from "./aggregator.js";
import { collectGitCommits } from "./collectors/git-collector.js";
import { collectKiroSessions } from "./collectors/kiro-collector.js";
import { collectChromeHistory } from "./collectors/chrome-collector.js";

const mockGitCollect = vi.mocked(collectGitCommits);
const mockKiroCollect = vi.mocked(collectKiroSessions);
const mockChromeCollect = vi.mocked(collectChromeHistory);

describe("generateSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mocked responses
    mockGitCollect.mockResolvedValue({
      success: true,
      data: {
        commits: [
          {
            hash: "abc123",
            timestamp: "2026-08-24T09:30:00Z",
            message: "feat: add dashboard",
            branch: "main",
            repoName: "my-app",
            repoPath: "/home/test/workspace/my-app",
            files: [{ path: "src/dashboard.ts", status: "A" }],
            categories: [],
            aiAssisted: false,
          },
        ],
        reposScanned: 3,
        reposWithCommits: 1,
      },
      errors: [],
      source: "git",
    });

    mockKiroCollect.mockResolvedValue({
      success: true,
      data: {
        sessions: [
          {
            sessionId: "sess-1",
            createdAt: "2026-08-24T09:00:00Z",
            updatedAt: "2026-08-24T10:00:00Z",
            title: "Dashboard work",
            cwd: "/home/test/workspace/my-app",
            promptCount: 8,
            toolCalls: { read_file: 5, grep_search: 3 },
            durationMinutes: 60,
          },
        ],
        totalDurationMinutes: 60,
        totalPrompts: 8,
        toolUsageAggregate: { read_file: 5, grep_search: 3 },
      },
      errors: [],
      source: "kiro",
    });

    mockChromeCollect.mockResolvedValue({
      success: true,
      data: { entries: [], searchCount: 0, devToolsSessions: 0 },
      errors: [],
      source: "chrome",
    });
  });

  it("runs the full pipeline and produces a summary", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.success).toBe(true);
    expect(result.summary).not.toBeNull();
    expect(result.summary!.date).toBe("2026-08-24");
    expect(result.summary!.author).toBe("Test User");
  });

  it("categorizes commits", async () => {
    const result = await generateSummary("2026-08-24");

    const commit = result.summary!.timeline.find((e) => e.type === "commit");
    expect(commit).toBeDefined();
    // The commit has an A-status file = feature
    expect(commit!.category).toBe("feature");
  });

  it("flags AI-assisted commits from Kiro sessions", async () => {
    const result = await generateSummary("2026-08-24");

    // Commit at 09:30 overlaps with Kiro session 09:00-10:00
    const commitEntry = result.summary!.timeline.find((e) => e.type === "commit");
    expect(commitEntry).toBeDefined();
    expect(commitEntry!.aiAssisted).toBe(true);
  });

  it("calculates time estimates", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.summary!.summary.totalEditTime).not.toBe("0m");
    expect(result.summary!.summary.aiAssistedTime).not.toBe("0m");
  });

  it("produces markdown output", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.markdown).not.toBeNull();
    expect(result.markdown).toContain("# Daily Work Summary");
    expect(result.markdown).toContain("2026-08-24");
  });

  it("reports collector results with timing", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.collectorResults.length).toBeGreaterThan(0);
    const gitResult = result.collectorResults.find((r) => r.name === "git");
    expect(gitResult).toBeDefined();
    expect(gitResult!.success).toBe(true);
    expect(gitResult!.durationMs).toBeGreaterThanOrEqual(0);
  });

  it("handles disabled collectors gracefully", async () => {
    const result = await generateSummary("2026-08-24");

    const chromeResult = result.collectorResults.find((r) => r.name === "chrome");
    expect(chromeResult).toBeDefined();
    // Chrome is disabled in mock config
    expect(chromeResult!.errors[0]).toContain("disabled");
  });

  it("handles collector failures gracefully", async () => {
    mockGitCollect.mockRejectedValue(new Error("git not found"));

    const result = await generateSummary("2026-08-24");

    // Pipeline still succeeds with partial data
    expect(result.success).toBe(true);
    expect(result.summary).not.toBeNull();
    const gitResult = result.collectorResults.find((r) => r.name === "git");
    expect(gitResult!.success).toBe(false);
    expect(gitResult!.errors[0]).toContain("git not found");
  });

  it("uses today's date when none provided", async () => {
    const result = await generateSummary();

    const today = new Date().toISOString().split("T")[0];
    expect(result.summary!.date).toBe(today);
  });

  it("includes Kiro session data in AI sessions summary", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.summary!.aiSessions.count).toBe(1);
    expect(result.summary!.aiSessions.toolUsage.read_file).toBe(5);
  });

  it("sets communication data to null for disabled collectors", async () => {
    const result = await generateSummary("2026-08-24");

    expect(result.summary!.communications.teams).toBeNull();
    expect(result.summary!.communications.slack).toBeNull();
  });
});
