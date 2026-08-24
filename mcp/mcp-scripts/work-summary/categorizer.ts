/**
 * Commit Categorizer — classifies commits into work categories based on
 * file paths, commit messages, and file age.
 */

import { execSync } from "node:child_process";
import type { GitCommitEntry, WorkCategory, FileChange } from "./types.js";

// ─── Pattern Definitions ────────────────────────────────────────────────────

const UNIT_TEST_PATTERNS = [
  /\.test\.[tj]sx?$/,
  /\.spec\.[tj]sx?$/,
  /Test\.cs$/,
  /Tests\.cs$/,
  /test_[^/]+\.py$/,
  /_test\.go$/,
  /\.test\.go$/,
  /Tests?\.java$/,
];

const INTEGRATION_TEST_PATTERNS = [
  /integration/i,
  /e2e/i,
  /\.e2e\.[tj]sx?$/,
  /\.integration\.[tj]sx?$/,
];

const PERFORMANCE_TEST_PATTERNS = [
  /perf/i,
  /benchmark/i,
  /load[_-]?test/i,
  /stress[_-]?test/i,
  /\.perf\.[tj]sx?$/,
  /\.bench\.[tj]sx?$/,
];

const DOCUMENTATION_PATTERNS = [
  /\.md$/i,
  /\.mdx$/i,
  /^docs\//,
  /\/docs\//,
  /README/i,
  /CHANGELOG/i,
  /CONTRIBUTING/i,
  /LICENSE/,
  /\.adoc$/i,
  /\.rst$/i,
];

const REFACTOR_MESSAGE_KEYWORDS = [
  /\brefactor\b/i,
  /\bcleanup\b/i,
  /\bclean[- ]up\b/i,
  /\brename\b/i,
  /\breorganize\b/i,
  /\brestructure\b/i,
  /\bsimplify\b/i,
  /\bextract\b/i,
  /\bmove\b/i,
];

const DOCUMENTATION_MESSAGE_KEYWORDS = [
  /^docs:/i,
  /^doc:/i,
  /\bdocumentation\b/i,
  /\bREADME\b/,
  /\bchangelog\b/i,
];

const PERFORMANCE_MESSAGE_KEYWORDS = [
  /\bperf\b/i,
  /\bperformance\b/i,
  /\bbenchmark\b/i,
  /\boptimize\b/i,
  /\boptimise\b/i,
];

const INTEGRATION_TEST_MESSAGE_KEYWORDS = [
  /\bintegration test/i,
  /\be2e test/i,
  /\bend[- ]to[- ]end/i,
];

// ─── File Classification ────────────────────────────────────────────────────

/**
 * Classify a single file path into a category.
 */
export function classifyFile(filePath: string): WorkCategory | null {
  // Order matters: more specific patterns first

  // Integration tests (check before unit tests since some match both)
  if (INTEGRATION_TEST_PATTERNS.some((p) => p.test(filePath))) {
    // But also check if it's actually a test file
    if (UNIT_TEST_PATTERNS.some((p) => p.test(filePath))) {
      return "integration-test";
    }
    // Could be integration test directory with non-test files
    if (filePath.match(/\.(test|spec)\./)) {
      return "integration-test";
    }
  }

  // Performance tests
  if (PERFORMANCE_TEST_PATTERNS.some((p) => p.test(filePath))) {
    if (UNIT_TEST_PATTERNS.some((p) => p.test(filePath)) || filePath.match(/\.(test|spec|bench)\./)) {
      return "performance-test";
    }
  }

  // Unit tests
  if (UNIT_TEST_PATTERNS.some((p) => p.test(filePath))) {
    return "unit-test";
  }

  // Documentation
  if (DOCUMENTATION_PATTERNS.some((p) => p.test(filePath))) {
    return "documentation";
  }

  return null;
}

/**
 * Classify based on commit message keywords.
 */
export function classifyMessage(message: string): WorkCategory | null {
  if (INTEGRATION_TEST_MESSAGE_KEYWORDS.some((p) => p.test(message))) {
    return "integration-test";
  }
  if (PERFORMANCE_MESSAGE_KEYWORDS.some((p) => p.test(message))) {
    return "performance-test";
  }
  if (DOCUMENTATION_MESSAGE_KEYWORDS.some((p) => p.test(message))) {
    return "documentation";
  }
  if (REFACTOR_MESSAGE_KEYWORDS.some((p) => p.test(message))) {
    return "refactor";
  }
  return null;
}

// ─── Refactor Detection (file age) ─────────────────────────────────────────

/**
 * Check if a file's last modification was more than 8 hours before the commit.
 * This indicates a refactor rather than new development.
 *
 * @param filePath - relative path within the repo
 * @param repoPath - absolute path to the repo root
 * @param commitTimestamp - ISO timestamp of the current commit
 * @returns true if the file was last changed >8 hours ago (refactor)
 */
export function isRefactorByAge(
  filePath: string,
  repoPath: string,
  commitTimestamp: string
): boolean {
  try {
    // Get the timestamp of the previous commit that touched this file
    const output = execSync(
      `git log -2 --format=%aI -- "${filePath}"`,
      { encoding: "utf-8", cwd: repoPath, timeout: 5_000 }
    );

    const timestamps = output.trim().split("\n").filter(Boolean);
    // We need at least 2 entries: current commit and the previous one
    if (timestamps.length < 2) return false;

    const previousTimestamp = timestamps[1]; // Second entry is the prior commit
    const commitDate = new Date(commitTimestamp);
    const previousDate = new Date(previousTimestamp);

    const diffHours = (commitDate.getTime() - previousDate.getTime()) / (1000 * 60 * 60);
    return diffHours > 8;
  } catch {
    return false;
  }
}

// ─── Stubbed version for testing (no git calls) ─────────────────────────────

/**
 * Categorize a commit without checking file age (pure logic, no I/O).
 * Used as the primary categorizer; file-age checks are optional enhancement.
 */
export function categorizeCommitPure(commit: GitCommitEntry): WorkCategory[] {
  const categories = new Set<WorkCategory>();

  // 1. Check commit message for category hints
  const messageCategory = classifyMessage(commit.message);
  if (messageCategory) {
    categories.add(messageCategory);
  }

  // 2. Check each file
  for (const file of commit.files) {
    const fileCategory = classifyFile(file.path);
    if (fileCategory) {
      categories.add(fileCategory);
      continue;
    }

    // If file is modified/deleted and message suggests refactor
    if ((file.status === "M" || file.status === "D") && messageCategory === "refactor") {
      categories.add("refactor");
    }

    // New files without a specific category = feature
    if (file.status === "A" && !fileCategory) {
      categories.add("feature");
    }
  }

  // 3. If no specific category assigned, infer from file statuses
  if (categories.size === 0) {
    const hasNewFiles = commit.files.some((f) => f.status === "A");
    if (hasNewFiles) {
      categories.add("feature");
    } else if (commit.files.length > 0) {
      // All modifications with no clear category — could be feature work or refactor
      // Default to feature unless message hints otherwise
      categories.add("feature");
    }
  }

  return Array.from(categories);
}

// ─── Full Categorizer (with optional file-age checks) ───────────────────────

export interface CategorizeOptions {
  /** Whether to check git history for file age (refactor detection). Slower but more accurate. */
  checkFileAge?: boolean;
}

/**
 * Categorize a commit, optionally checking file age for refactor detection.
 */
export function categorizeCommit(
  commit: GitCommitEntry,
  options: CategorizeOptions = {}
): WorkCategory[] {
  const categories = new Set(categorizeCommitPure(commit));

  // Enhanced refactor detection via file age
  if (options.checkFileAge && !categories.has("refactor")) {
    for (const file of commit.files) {
      if (file.status === "M") {
        if (isRefactorByAge(file.path, commit.repoPath, commit.timestamp)) {
          categories.add("refactor");
          // If we previously assumed 'feature' purely from file status, remove it
          if (categories.has("feature") && commit.files.every((f) => f.status === "M")) {
            categories.delete("feature");
          }
          break; // One refactor file is enough to tag the commit
        }
      }
    }
  }

  return Array.from(categories);
}

/**
 * Categorize an array of commits, mutating their `categories` field in place.
 */
export function categorizeCommits(
  commits: GitCommitEntry[],
  options: CategorizeOptions = {}
): GitCommitEntry[] {
  for (const commit of commits) {
    commit.categories = categorizeCommit(commit, options);
  }
  return commits;
}
