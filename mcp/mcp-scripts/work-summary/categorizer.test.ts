import { describe, it, expect } from "vitest";
import {
  classifyFile,
  classifyMessage,
  categorizeCommitPure,
  categorizeCommits,
} from "./categorizer.js";
import type { GitCommitEntry } from "./types.js";

// ─── Helper ─────────────────────────────────────────────────────────────────

function makeCommit(overrides: Partial<GitCommitEntry> = {}): GitCommitEntry {
  return {
    hash: "abc123",
    timestamp: "2026-08-24T10:00:00-05:00",
    message: "some change",
    branch: "main",
    repoName: "project",
    repoPath: "/home/user/workspace/project",
    files: [],
    categories: [],
    aiAssisted: false,
    ...overrides,
  };
}

// ─── classifyFile ───────────────────────────────────────────────────────────

describe("classifyFile", () => {
  describe("unit tests", () => {
    it("detects .test.ts files", () => {
      expect(classifyFile("src/utils.test.ts")).toBe("unit-test");
    });

    it("detects .spec.tsx files", () => {
      expect(classifyFile("components/Button.spec.tsx")).toBe("unit-test");
    });

    it("detects C# test files", () => {
      expect(classifyFile("Tests/UserServiceTest.cs")).toBe("unit-test");
      expect(classifyFile("Tests/UserServiceTests.cs")).toBe("unit-test");
    });

    it("detects Python test files", () => {
      expect(classifyFile("tests/test_parser.py")).toBe("unit-test");
    });

    it("detects Go test files", () => {
      expect(classifyFile("pkg/handler_test.go")).toBe("unit-test");
    });
  });

  describe("integration tests", () => {
    it("detects e2e test files", () => {
      expect(classifyFile("tests/e2e/login.test.ts")).toBe("integration-test");
    });

    it("detects integration directory test files", () => {
      expect(classifyFile("tests/integration/api.spec.ts")).toBe("integration-test");
    });
  });

  describe("performance tests", () => {
    it("detects benchmark test files", () => {
      expect(classifyFile("tests/benchmark/query.bench.ts")).toBe("performance-test");
    });

    it("detects perf test files", () => {
      expect(classifyFile("perf/load-test.test.ts")).toBe("performance-test");
    });
  });

  describe("documentation", () => {
    it("detects markdown files", () => {
      expect(classifyFile("README.md")).toBe("documentation");
      expect(classifyFile("docs/setup.md")).toBe("documentation");
    });

    it("detects docs directory files", () => {
      expect(classifyFile("docs/api-reference.ts")).toBe("documentation");
    });

    it("detects CHANGELOG", () => {
      expect(classifyFile("CHANGELOG.md")).toBe("documentation");
    });

    it("detects MDX files", () => {
      expect(classifyFile("content/blog-post.mdx")).toBe("documentation");
    });
  });

  describe("no category", () => {
    it("returns null for regular source files", () => {
      expect(classifyFile("src/app.ts")).toBeNull();
      expect(classifyFile("lib/database.cs")).toBeNull();
      expect(classifyFile("main.go")).toBeNull();
    });
  });
});

// ─── classifyMessage ────────────────────────────────────────────────────────

describe("classifyMessage", () => {
  it("detects documentation from docs: prefix", () => {
    expect(classifyMessage("docs: update API reference")).toBe("documentation");
  });

  it("detects refactor keywords", () => {
    expect(classifyMessage("refactor: extract validation logic")).toBe("refactor");
    expect(classifyMessage("cleanup: remove dead code")).toBe("refactor");
    expect(classifyMessage("rename UserService to AccountService")).toBe("refactor");
  });

  it("detects performance keywords", () => {
    expect(classifyMessage("perf: optimize query execution")).toBe("performance-test");
    expect(classifyMessage("benchmark: add load testing")).toBe("performance-test");
  });

  it("detects integration test keywords", () => {
    expect(classifyMessage("add integration test for auth flow")).toBe("integration-test");
    expect(classifyMessage("fix e2e test flakiness")).toBe("integration-test");
  });

  it("returns null for generic messages", () => {
    expect(classifyMessage("feat: add login page")).toBeNull();
    expect(classifyMessage("fix: null pointer in handler")).toBeNull();
  });
});

// ─── categorizeCommitPure ───────────────────────────────────────────────────

describe("categorizeCommitPure", () => {
  it("categorizes new feature files as feature", () => {
    const commit = makeCommit({
      message: "feat: add dashboard",
      files: [
        { path: "src/dashboard.tsx", status: "A" },
        { path: "src/dashboard.css", status: "A" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("feature");
  });

  it("categorizes test files as unit-test", () => {
    const commit = makeCommit({
      message: "add tests for parser",
      files: [
        { path: "src/parser.test.ts", status: "A" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("unit-test");
  });

  it("categorizes docs commit", () => {
    const commit = makeCommit({
      message: "docs: update setup guide",
      files: [
        { path: "docs/setup.md", status: "M" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("documentation");
  });

  it("categorizes refactor from message keywords", () => {
    const commit = makeCommit({
      message: "refactor: extract auth middleware",
      files: [
        { path: "src/middleware/auth.ts", status: "M" },
        { path: "src/server.ts", status: "M" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("refactor");
  });

  it("handles mixed commits with multiple categories", () => {
    const commit = makeCommit({
      message: "feat: add user module with tests",
      files: [
        { path: "src/user.ts", status: "A" },
        { path: "src/user.test.ts", status: "A" },
        { path: "docs/user-api.md", status: "A" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("feature");
    expect(categories).toContain("unit-test");
    expect(categories).toContain("documentation");
  });

  it("defaults to feature for commits with only modifications and no keywords", () => {
    const commit = makeCommit({
      message: "fix: handle null case in parser",
      files: [
        { path: "src/parser.ts", status: "M" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("feature");
  });

  it("handles commits with no files (merge commits)", () => {
    const commit = makeCommit({
      message: "Merge branch 'feature' into main",
      files: [],
    });

    const categories = categorizeCommitPure(commit);
    // No files = no category (empty array is acceptable)
    expect(categories.length).toBe(0);
  });

  it("categorizes e2e test files correctly", () => {
    const commit = makeCommit({
      message: "add e2e tests for checkout",
      files: [
        { path: "tests/e2e/checkout.test.ts", status: "A" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("integration-test");
  });

  it("categorizes performance test commit", () => {
    const commit = makeCommit({
      message: "perf: add benchmark for query layer",
      files: [
        { path: "benchmarks/query.bench.ts", status: "A" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("performance-test");
  });

  it("categorizes deleted files with refactor message", () => {
    const commit = makeCommit({
      message: "cleanup: remove deprecated helpers",
      files: [
        { path: "src/helpers/deprecated.ts", status: "D" },
        { path: "src/helpers/old-utils.ts", status: "D" },
      ],
    });

    const categories = categorizeCommitPure(commit);
    expect(categories).toContain("refactor");
  });
});

// ─── categorizeCommits (batch) ──────────────────────────────────────────────

describe("categorizeCommits", () => {
  it("mutates categories field on all commits", () => {
    const commits = [
      makeCommit({
        message: "feat: new thing",
        files: [{ path: "src/thing.ts", status: "A" }],
      }),
      makeCommit({
        message: "docs: readme",
        files: [{ path: "README.md", status: "M" }],
      }),
    ];

    const result = categorizeCommits(commits);

    expect(result[0].categories).toContain("feature");
    expect(result[1].categories).toContain("documentation");
    // Mutates in place
    expect(result).toBe(commits);
  });
});
