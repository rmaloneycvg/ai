/**
 * Edit Time Estimator — calculates total time spent editing by combining
 * git commit timestamps, file modification times, and Kiro session windows.
 * Merges activity points into sessions and distinguishes AI-assisted vs manual time.
 */

import type { GitCommitEntry, KiroSession, EditSession, TimeEstimate } from "../types.js";

// ─── Activity Points ────────────────────────────────────────────────────────

interface ActivityPoint {
  timestamp: number; // Unix ms
  source: "commit" | "kiro_start" | "kiro_end" | "file_mtime";
}

interface TimeWindow {
  start: number;
  end: number;
}

/**
 * Build activity points from git commits.
 */
export function commitActivityPoints(commits: GitCommitEntry[]): ActivityPoint[] {
  return commits.map((c) => ({
    timestamp: new Date(c.timestamp).getTime(),
    source: "commit" as const,
  }));
}

/**
 * Build activity points from Kiro session boundaries.
 * We add intermediate points to ensure sessions aren't split by the gap threshold.
 */
export function kiroActivityPoints(sessions: KiroSession[]): ActivityPoint[] {
  const points: ActivityPoint[] = [];
  for (const session of sessions) {
    const start = new Date(session.createdAt).getTime();
    const end = new Date(session.updatedAt).getTime();
    points.push({ timestamp: start, source: "kiro_start" });

    // Add intermediate points every 15 minutes to prevent gap-splitting
    const intervalMs = 15 * 60 * 1000;
    let current = start + intervalMs;
    while (current < end) {
      points.push({ timestamp: current, source: "kiro_start" });
      current += intervalMs;
    }

    points.push({ timestamp: end, source: "kiro_end" });
  }
  return points;
}

/**
 * Build activity points from file modification timestamps.
 */
export function fileMtimeActivityPoints(mtimes: number[]): ActivityPoint[] {
  return mtimes.map((ts) => ({
    timestamp: ts,
    source: "file_mtime" as const,
  }));
}

// ─── Session Merging ────────────────────────────────────────────────────────

/**
 * Merge activity points into contiguous work sessions.
 * Points within `gapMinutes` of each other are merged into one session.
 */
export function mergeIntoSessions(points: ActivityPoint[], gapMinutes: number): TimeWindow[] {
  if (points.length === 0) return [];

  // Sort by timestamp
  const sorted = [...points].sort((a, b) => a.timestamp - b.timestamp);
  const gapMs = gapMinutes * 60 * 1000;

  const sessions: TimeWindow[] = [];
  let currentStart = sorted[0].timestamp;
  let currentEnd = sorted[0].timestamp;

  for (let i = 1; i < sorted.length; i++) {
    const point = sorted[i];
    if (point.timestamp - currentEnd > gapMs) {
      // Gap exceeds threshold — close current session, start new one
      sessions.push({ start: currentStart, end: currentEnd });
      currentStart = point.timestamp;
      currentEnd = point.timestamp;
    } else {
      // Extend current session
      currentEnd = point.timestamp;
    }
  }

  // Close final session
  sessions.push({ start: currentStart, end: currentEnd });

  return sessions;
}

// ─── AI/Manual Split ────────────────────────────────────────────────────────

/**
 * Get Kiro session time windows.
 */
export function kiroTimeWindows(sessions: KiroSession[]): TimeWindow[] {
  return sessions.map((s) => ({
    start: new Date(s.createdAt).getTime(),
    end: new Date(s.updatedAt).getTime(),
  }));
}

/**
 * Check if a time window overlaps with any Kiro session.
 */
export function overlapsKiroSession(window: TimeWindow, kiroWindows: TimeWindow[]): boolean {
  for (const kw of kiroWindows) {
    // Overlap: starts before other ends AND ends after other starts
    if (window.start <= kw.end && window.end >= kw.start) {
      return true;
    }
  }
  return false;
}

/**
 * Calculate the overlap duration (ms) between a work session and all Kiro windows.
 */
export function calculateOverlapMs(window: TimeWindow, kiroWindows: TimeWindow[]): number {
  let totalOverlap = 0;

  for (const kw of kiroWindows) {
    const overlapStart = Math.max(window.start, kw.start);
    const overlapEnd = Math.min(window.end, kw.end);
    if (overlapStart < overlapEnd) {
      totalOverlap += overlapEnd - overlapStart;
    }
  }

  return totalOverlap;
}

// ─── Main Estimator ─────────────────────────────────────────────────────────

export interface TimeEstimatorInput {
  commits: GitCommitEntry[];
  kiroSessions: KiroSession[];
  fileMtimes?: number[];
  gapMinutes: number;
}

/**
 * Estimate total edit time from all sources.
 */
export function estimateEditTime(input: TimeEstimatorInput): TimeEstimate {
  const { commits, kiroSessions, fileMtimes = [], gapMinutes } = input;

  // Build all activity points
  const allPoints: ActivityPoint[] = [
    ...commitActivityPoints(commits),
    ...kiroActivityPoints(kiroSessions),
    ...fileMtimeActivityPoints(fileMtimes),
  ];

  if (allPoints.length === 0) {
    return {
      totalEditMinutes: 0,
      aiAssistedMinutes: 0,
      manualMinutes: 0,
      sessions: [],
    };
  }

  // Merge into work sessions
  const workSessions = mergeIntoSessions(allPoints, gapMinutes);
  const kiroWindows = kiroTimeWindows(kiroSessions);

  // Calculate durations and AI/manual split
  let totalEditMs = 0;
  let aiAssistedMs = 0;
  const editSessions: EditSession[] = [];

  for (const ws of workSessions) {
    const durationMs = ws.end - ws.start;
    // Minimum session duration: if start === end (single point), count as 1 minute
    const effectiveDurationMs = durationMs === 0 ? 60_000 : durationMs;
    totalEditMs += effectiveDurationMs;

    const overlapMs = calculateOverlapMs(ws, kiroWindows);
    const isAiAssisted = overlapMs > 0;

    if (isAiAssisted) {
      aiAssistedMs += effectiveDurationMs;
    }

    editSessions.push({
      start: new Date(ws.start).toISOString(),
      end: new Date(ws.end).toISOString(),
      durationMinutes: Math.round(effectiveDurationMs / 60_000),
      aiAssisted: isAiAssisted,
    });
  }

  const manualMs = totalEditMs - aiAssistedMs;

  return {
    totalEditMinutes: Math.round(totalEditMs / 60_000),
    aiAssistedMinutes: Math.round(aiAssistedMs / 60_000),
    manualMinutes: Math.round(manualMs / 60_000),
    sessions: editSessions,
  };
}
