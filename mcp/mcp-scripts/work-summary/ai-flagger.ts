/**
 * AI-Assisted Work Flagger — correlates git commits with active Kiro sessions
 * to determine which commits were AI-paired.
 */

import type { GitCommitEntry, KiroSession } from "./types.js";

interface SessionWindow {
  sessionId: string;
  start: number; // Unix ms
  end: number;   // Unix ms
  cwd: string;
}

/**
 * Build time windows from Kiro sessions for overlap checking.
 */
export function buildSessionWindows(sessions: KiroSession[]): SessionWindow[] {
  return sessions.map((s) => ({
    sessionId: s.sessionId,
    start: new Date(s.createdAt).getTime(),
    end: new Date(s.updatedAt).getTime(),
    cwd: s.cwd,
  }));
}

/**
 * Check if a commit timestamp falls within a Kiro session window.
 * Optionally matches by working directory for stronger correlation.
 */
export function findMatchingSession(
  commitTimestamp: string,
  commitRepoPath: string,
  windows: SessionWindow[],
  options: { matchCwd?: boolean } = {}
): SessionWindow | null {
  const commitTime = new Date(commitTimestamp).getTime();

  for (const window of windows) {
    // Check time overlap
    if (commitTime >= window.start && commitTime <= window.end) {
      // If cwd matching is enabled, also check directory
      if (options.matchCwd) {
        if (isCwdMatch(window.cwd, commitRepoPath)) {
          return window;
        }
      } else {
        return window;
      }
    }
  }

  // If matchCwd was required but no match found, fall back to time-only match
  if (options.matchCwd) {
    for (const window of windows) {
      if (commitTime >= window.start && commitTime <= window.end) {
        return window;
      }
    }
  }

  return null;
}

/**
 * Check if a Kiro session's working directory matches or is a parent of the repo path.
 */
export function isCwdMatch(sessionCwd: string, repoPath: string): boolean {
  if (!sessionCwd || !repoPath) return false;

  // Normalize paths (remove trailing slashes)
  const normalizedCwd = sessionCwd.replace(/\/+$/, "");
  const normalizedRepo = repoPath.replace(/\/+$/, "");

  // Exact match or session cwd is within the repo
  return (
    normalizedCwd === normalizedRepo ||
    normalizedCwd.startsWith(normalizedRepo + "/") ||
    normalizedRepo.startsWith(normalizedCwd + "/")
  );
}

export interface FlagOptions {
  /** Try to match by working directory first for stronger correlation */
  preferCwdMatch?: boolean;
}

/**
 * Flag commits as AI-assisted based on correlation with Kiro sessions.
 * Mutates the commits in place, setting `aiAssisted` and `sessionId`.
 */
export function flagAiAssistedCommits(
  commits: GitCommitEntry[],
  sessions: KiroSession[],
  options: FlagOptions = {}
): GitCommitEntry[] {
  if (sessions.length === 0) return commits;

  const windows = buildSessionWindows(sessions);

  for (const commit of commits) {
    const match = findMatchingSession(
      commit.timestamp,
      commit.repoPath,
      windows,
      { matchCwd: options.preferCwdMatch }
    );

    if (match) {
      commit.aiAssisted = true;
      commit.sessionId = match.sessionId;
    }
  }

  return commits;
}
