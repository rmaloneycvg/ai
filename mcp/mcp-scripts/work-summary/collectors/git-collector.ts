/**
 * Git Collector — discovers repos and collects commits across all branches for a date range.
 */

import { execSync } from "node:child_process";
import { expandHome } from "../config.js";
import type { Config, CollectorResult, GitCommitEntry, FileChange, FileStatus } from "../types.js";

export interface GitCollectorData {
  commits: GitCommitEntry[];
  reposScanned: number;
  reposWithCommits: number;
}

// ─── Repo Discovery ─────────────────────────────────────────────────────────

/**
 * Find all git repositories under the given paths (max depth 3).
 */
export function discoverRepos(paths: string[]): string[] {
  const repos: string[] = [];

  for (const rawPath of paths) {
    const searchPath = expandHome(rawPath);
    try {
      const output = execSync(
        `find "${searchPath}" -maxdepth 4 -name .git -type d 2>/dev/null`,
        { encoding: "utf-8", timeout: 15_000 }
      );
      for (const line of output.trim().split("\n")) {
        if (line) {
          // .git directory -> parent is the repo root
          repos.push(line.replace(/\/\.git$/, ""));
        }
      }
    } catch {
      // find may fail for inaccessible dirs — skip
    }
  }

  return repos;
}

/**
 * Extract repo name from its path (last path segment).
 */
export function repoName(repoPath: string): string {
  return repoPath.split("/").filter(Boolean).pop() || repoPath;
}

// ─── Commit Parsing ─────────────────────────────────────────────────────────

const COMMIT_SEPARATOR = "---COMMIT_BOUNDARY---";

/**
 * Build the git log command for a specific repo and date range.
 */
export function buildGitLogCommand(email: string, after: string, before: string): string {
  // Use a boundary marker to separate commits reliably
  const format = `${COMMIT_SEPARATOR}%n%H|%aI|%s|%D`;
  return `git log --all --author="${email}" --after="${after}" --before="${before}" --format="${format}" --name-status`;
}

/**
 * Parse raw git log output into structured commit entries.
 */
export function parseGitLog(raw: string, repo: string): GitCommitEntry[] {
  const commits: GitCommitEntry[] = [];

  if (!raw.trim()) return commits;

  // Split by commit boundary
  const blocks = raw.split(COMMIT_SEPARATOR).filter((b) => b.trim());

  for (const block of blocks) {
    const lines = block.trim().split("\n");
    if (lines.length === 0) continue;

    // First line is the formatted header: hash|timestamp|subject|refs
    const headerLine = lines[0];
    const pipeIdx1 = headerLine.indexOf("|");
    if (pipeIdx1 === -1) continue;

    const hash = headerLine.slice(0, pipeIdx1);
    const rest1 = headerLine.slice(pipeIdx1 + 1);

    const pipeIdx2 = rest1.indexOf("|");
    if (pipeIdx2 === -1) continue;

    const timestamp = rest1.slice(0, pipeIdx2);
    const rest2 = rest1.slice(pipeIdx2 + 1);

    const pipeIdx3 = rest2.indexOf("|");
    if (pipeIdx3 === -1) continue;

    const message = rest2.slice(0, pipeIdx3);
    const refs = rest2.slice(pipeIdx3 + 1);

    // Extract branch from refs (e.g., "HEAD -> main, origin/main")
    const branch = parseBranch(refs);

    // Remaining lines are file status entries (e.g., "M\tpath/to/file")
    const files: FileChange[] = [];
    for (let i = 1; i < lines.length; i++) {
      const fileLine = lines[i].trim();
      if (!fileLine) continue;

      const parsed = parseFileChange(fileLine);
      if (parsed) files.push(parsed);
    }

    commits.push({
      hash,
      timestamp,
      message,
      branch,
      repoName: repoName(repo),
      repoPath: repo,
      files,
      categories: [], // populated by categorizer later
      aiAssisted: false, // populated by AI flagger later
    });
  }

  return commits;
}

/**
 * Parse branch name from git ref decoration.
 */
export function parseBranch(refs: string): string {
  if (!refs.trim()) return "unknown";

  // Look for "HEAD -> branchname" first
  const headMatch = refs.match(/HEAD\s*->\s*([^,]+)/);
  if (headMatch) return headMatch[1].trim();

  // Otherwise take the first ref
  const firstRef = refs.split(",")[0].trim();
  // Strip "origin/" prefix if present
  return firstRef.replace(/^origin\//, "");
}

/**
 * Parse a single file change line from git log --name-status.
 */
export function parseFileChange(line: string): FileChange | null {
  // Format: "M\tpath/to/file" or "R100\told\tnew"
  const match = line.match(/^([AMDRC]\d*)\t(.+)/);
  if (!match) return null;

  const statusChar = match[1][0] as FileStatus;
  let path = match[2];

  // For renames (R) and copies (C), take the new path (after tab)
  if ((statusChar === "R" || statusChar === "C") && path.includes("\t")) {
    path = path.split("\t")[1];
  }

  return { path, status: statusChar };
}

// ─── Collector ──────────────────────────────────────────────────────────────

/**
 * Collect git commits for a given date across all configured workspace repos.
 */
export async function collectGitCommits(
  date: string,
  config: Config
): Promise<CollectorResult<GitCollectorData>> {
  const errors: string[] = [];

  // Date range: start of day to end of day
  const after = `${date}T00:00:00`;
  const before = `${date}T23:59:59`;

  const repos = discoverRepos(config.workspacePaths);
  if (repos.length === 0) {
    return {
      success: true,
      data: { commits: [], reposScanned: 0, reposWithCommits: 0 },
      errors: ["No git repositories found in configured workspace paths"],
      source: "git",
    };
  }

  const allCommits: GitCommitEntry[] = [];
  let reposWithCommits = 0;

  for (const repo of repos) {
    try {
      const cmd = buildGitLogCommand(config.author.email, after, before);
      const output = execSync(cmd, {
        encoding: "utf-8",
        cwd: repo,
        timeout: 10_000,
      });

      const commits = parseGitLog(output, repo);
      if (commits.length > 0) {
        reposWithCommits++;
        allCommits.push(...commits);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      // Don't fail the whole collection for one repo
      errors.push(`Failed to read git log for ${repoName(repo)}: ${msg}`);
    }
  }

  // Sort chronologically
  allCommits.sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  return {
    success: true,
    data: {
      commits: allCommits,
      reposScanned: repos.length,
      reposWithCommits,
    },
    errors,
    source: "git",
  };
}

// ─── Collector Interface Implementation ─────────────────────────────────────

export const gitCollector = {
  name: "git",
  collect: collectGitCommits,
};
