import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  parseGitLog,
  parseBranch,
  parseFileChange,
  buildGitLogCommand,
  repoName,
  discoverRepos,
  collectGitCommits,
} from "./git-collector.js";
import type { Config } from "../types.js";

// ─── Unit Tests ─────────────────────────────────────────────────────────────

describe("repoName", () => {
  it("extracts last path segment", () => {
    expect(repoName("/home/user/workspace/my-project")).toBe("my-project");
  });

  it("handles trailing slash", () => {
    expect(repoName("/home/user/workspace/my-project/")).toBe("my-project");
  });

  it("returns path itself for simple name", () => {
    expect(repoName("project")).toBe("project");
  });
});

describe("parseBranch", () => {
  it("extracts branch from HEAD -> ref", () => {
    expect(parseBranch("HEAD -> main, origin/main")).toBe("main");
  });

  it("extracts branch from origin ref", () => {
    expect(parseBranch("origin/feature-xyz")).toBe("feature-xyz");
  });

  it("returns unknown for empty refs", () => {
    expect(parseBranch("")).toBe("unknown");
    expect(parseBranch("  ")).toBe("unknown");
  });

  it("handles multiple refs taking first", () => {
    expect(parseBranch("tag: v1.0, origin/release")).toBe("tag: v1.0");
  });

  it("trims whitespace", () => {
    expect(parseBranch("  HEAD -> development  ")).toBe("development");
  });
});

describe("parseFileChange", () => {
  it("parses added file", () => {
    expect(parseFileChange("A\tsrc/new-file.ts")).toEqual({
      path: "src/new-file.ts",
      status: "A",
    });
  });

  it("parses modified file", () => {
    expect(parseFileChange("M\tsrc/existing.ts")).toEqual({
      path: "src/existing.ts",
      status: "M",
    });
  });

  it("parses deleted file", () => {
    expect(parseFileChange("D\told-file.ts")).toEqual({
      path: "old-file.ts",
      status: "D",
    });
  });

  it("parses renamed file (takes new path)", () => {
    expect(parseFileChange("R100\told-name.ts\tnew-name.ts")).toEqual({
      path: "new-name.ts",
      status: "R",
    });
  });

  it("parses copied file (takes new path)", () => {
    expect(parseFileChange("C100\toriginal.ts\tcopy.ts")).toEqual({
      path: "copy.ts",
      status: "C",
    });
  });

  it("returns null for invalid line", () => {
    expect(parseFileChange("")).toBeNull();
    expect(parseFileChange("not a valid line")).toBeNull();
  });
});

describe("buildGitLogCommand", () => {
  it("builds correct command with author and date range", () => {
    const cmd = buildGitLogCommand("user@example.com", "2026-08-24T00:00:00", "2026-08-24T23:59:59");
    expect(cmd).toContain("--all");
    expect(cmd).toContain('--author="user@example.com"');
    expect(cmd).toContain('--after="2026-08-24T00:00:00"');
    expect(cmd).toContain('--before="2026-08-24T23:59:59"');
    expect(cmd).toContain("--name-status");
  });
});

describe("parseGitLog", () => {
  const SEPARATOR = "---COMMIT_BOUNDARY---";

  it("parses a single commit with files", () => {
    const raw = `${SEPARATOR}
abc123|2026-08-24T10:30:00-05:00|feat: add login page|HEAD -> main
A\tsrc/login.ts
M\tsrc/app.ts`;

    const commits = parseGitLog(raw, "/home/user/workspace/my-app");
    expect(commits).toHaveLength(1);
    expect(commits[0].hash).toBe("abc123");
    expect(commits[0].timestamp).toBe("2026-08-24T10:30:00-05:00");
    expect(commits[0].message).toBe("feat: add login page");
    expect(commits[0].branch).toBe("main");
    expect(commits[0].repoName).toBe("my-app");
    expect(commits[0].repoPath).toBe("/home/user/workspace/my-app");
    expect(commits[0].files).toHaveLength(2);
    expect(commits[0].files[0]).toEqual({ path: "src/login.ts", status: "A" });
    expect(commits[0].files[1]).toEqual({ path: "src/app.ts", status: "M" });
  });

  it("parses multiple commits", () => {
    const raw = `${SEPARATOR}
aaa111|2026-08-24T09:00:00-05:00|fix: typo|origin/development
M\tREADME.md
${SEPARATOR}
bbb222|2026-08-24T14:00:00-05:00|feat: dashboard|HEAD -> feature/dash
A\tsrc/dashboard.tsx
A\tsrc/dashboard.test.tsx`;

    const commits = parseGitLog(raw, "/home/user/workspace/project");
    expect(commits).toHaveLength(2);
    expect(commits[0].hash).toBe("aaa111");
    expect(commits[0].branch).toBe("development");
    expect(commits[1].hash).toBe("bbb222");
    expect(commits[1].branch).toBe("feature/dash");
    expect(commits[1].files).toHaveLength(2);
  });

  it("handles commits with no file changes (merge commits)", () => {
    const raw = `${SEPARATOR}
ccc333|2026-08-24T11:00:00-05:00|Merge branch 'feature' into main|HEAD -> main`;

    const commits = parseGitLog(raw, "/home/user/workspace/repo");
    expect(commits).toHaveLength(1);
    expect(commits[0].message).toBe("Merge branch 'feature' into main");
    expect(commits[0].files).toHaveLength(0);
  });

  it("handles empty output", () => {
    expect(parseGitLog("", "/repo")).toEqual([]);
    expect(parseGitLog("  \n  ", "/repo")).toEqual([]);
  });

  it("handles commits with no branch refs", () => {
    const raw = `${SEPARATOR}
ddd444|2026-08-24T16:00:00-05:00|chore: cleanup|
D\told-file.ts`;

    const commits = parseGitLog(raw, "/home/user/workspace/repo");
    expect(commits).toHaveLength(1);
    expect(commits[0].branch).toBe("unknown");
  });

  it("handles renamed files in commit", () => {
    const raw = `${SEPARATOR}
eee555|2026-08-24T12:00:00-05:00|refactor: rename module|HEAD -> main
R100\tsrc/old.ts\tsrc/new.ts`;

    const commits = parseGitLog(raw, "/repo");
    expect(commits).toHaveLength(1);
    expect(commits[0].files[0]).toEqual({ path: "src/new.ts", status: "R" });
  });

  it("sets default values for categories and aiAssisted", () => {
    const raw = `${SEPARATOR}
fff666|2026-08-24T08:00:00-05:00|init|HEAD -> main
A\tindex.ts`;

    const commits = parseGitLog(raw, "/repo");
    expect(commits[0].categories).toEqual([]);
    expect(commits[0].aiAssisted).toBe(false);
    expect(commits[0].sessionId).toBeUndefined();
  });
});

// ─── Integration Tests (with mocked execSync) ──────────────────────────────

vi.mock("node:child_process", () => ({
  execSync: vi.fn(),
}));

import { execSync } from "node:child_process";
const mockExecSync = vi.mocked(execSync);

const testConfig: Config = {
  workspacePaths: ["~/workspace"],
  author: { name: "Test User", email: "test@example.com" },
  sessionGapMinutes: 30,
  outputDir: "~/output",
  collectors: { git: { enabled: true } },
};

describe("discoverRepos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("finds repos from find command output", () => {
    mockExecSync.mockReturnValue(
      "/home/user/workspace/project-a/.git\n/home/user/workspace/project-b/.git\n"
    );

    const repos = discoverRepos(["~/workspace"]);
    expect(repos).toContain("/home/user/workspace/project-a");
    expect(repos).toContain("/home/user/workspace/project-b");
  });

  it("returns empty array when find fails", () => {
    mockExecSync.mockImplementation(() => {
      throw new Error("find failed");
    });

    const repos = discoverRepos(["~/nonexistent"]);
    expect(repos).toEqual([]);
  });

  it("handles empty find output", () => {
    mockExecSync.mockReturnValue("");

    const repos = discoverRepos(["~/workspace"]);
    expect(repos).toEqual([]);
  });
});

describe("collectGitCommits", () => {
  const SEPARATOR = "---COMMIT_BOUNDARY---";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("collects commits across multiple repos", async () => {
    // First call: find repos
    mockExecSync.mockImplementation((cmd: unknown, opts?: unknown) => {
      const cmdStr = String(cmd);
      if (cmdStr.startsWith("find")) {
        return "/home/user/workspace/repo-a/.git\n/home/user/workspace/repo-b/.git\n";
      }
      // Git log calls
      const cwd = (opts as { cwd?: string })?.cwd || "";
      if (cwd.includes("repo-a")) {
        return `${SEPARATOR}\naaa|2026-08-24T09:00:00-05:00|feat: thing|HEAD -> main\nA\tfile.ts\n`;
      }
      if (cwd.includes("repo-b")) {
        return `${SEPARATOR}\nbbb|2026-08-24T14:00:00-05:00|fix: bug|HEAD -> dev\nM\tbug.ts\n`;
      }
      return "";
    });

    const result = await collectGitCommits("2026-08-24", testConfig);

    expect(result.success).toBe(true);
    expect(result.data!.commits).toHaveLength(2);
    expect(result.data!.reposScanned).toBe(2);
    expect(result.data!.reposWithCommits).toBe(2);
    // Sorted chronologically
    expect(result.data!.commits[0].hash).toBe("aaa");
    expect(result.data!.commits[1].hash).toBe("bbb");
  });

  it("handles repos with no matching commits", async () => {
    mockExecSync.mockImplementation((cmd: unknown) => {
      const cmdStr = String(cmd);
      if (cmdStr.startsWith("find")) {
        return "/home/user/workspace/empty-repo/.git\n";
      }
      return ""; // No commits
    });

    const result = await collectGitCommits("2026-08-24", testConfig);

    expect(result.success).toBe(true);
    expect(result.data!.commits).toHaveLength(0);
    expect(result.data!.reposScanned).toBe(1);
    expect(result.data!.reposWithCommits).toBe(0);
  });

  it("continues collecting when one repo fails", async () => {
    let callCount = 0;
    mockExecSync.mockImplementation((cmd: unknown, opts?: unknown) => {
      const cmdStr = String(cmd);
      if (cmdStr.startsWith("find")) {
        return "/home/user/workspace/good/.git\n/home/user/workspace/bad/.git\n";
      }
      const cwd = (opts as { cwd?: string })?.cwd || "";
      if (cwd.includes("bad")) {
        throw new Error("permission denied");
      }
      return `${SEPARATOR}\nxxx|2026-08-24T10:00:00-05:00|works|HEAD -> main\nA\tok.ts\n`;
    });

    const result = await collectGitCommits("2026-08-24", testConfig);

    expect(result.success).toBe(true);
    expect(result.data!.commits).toHaveLength(1);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors[0]).toContain("bad");
  });

  it("reports when no repos found", async () => {
    mockExecSync.mockReturnValue("");

    const result = await collectGitCommits("2026-08-24", testConfig);

    expect(result.success).toBe(true);
    expect(result.data!.commits).toHaveLength(0);
    expect(result.errors).toContain("No git repositories found in configured workspace paths");
  });
});
