/**
 * Kiro Session Collector — parses Kiro CLI session data for AI telemetry,
 * tool usage, prompts, and session durations.
 */

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { expandHome } from "../config.js";
import type { Config, CollectorResult, KiroSession, KiroCollectorData } from "../types.js";

const KIRO_SESSIONS_DIR = "~/.kiro/sessions";

// ─── Session Metadata Parsing ───────────────────────────────────────────────

interface RawSessionMeta {
  id: string;
  workspacePaths: string[];
  createdAt: string;
  lastModifiedAt?: string;
  title?: string;
  session_created_reason?: string;
}

/**
 * Parse a Kiro CLI v3 session metadata JSON file.
 */
export function parseSessionMeta(content: string): RawSessionMeta | null {
  try {
    const parsed = JSON.parse(content);
    if (!parsed.id || !parsed.createdAt) return null;
    return parsed as RawSessionMeta;
  } catch {
    return null;
  }
}

/**
 * Check if a session was active on the target date.
 */
export function isSessionOnDate(meta: RawSessionMeta, date: string): boolean {
  const dayStart = new Date(`${date}T00:00:00Z`);
  const dayEnd = new Date(`${date}T23:59:59.999Z`);

  const created = new Date(meta.createdAt);
  const updated = new Date(meta.lastModifiedAt || meta.createdAt);

  // Session overlaps with the target date if:
  // - created before end of day AND updated after start of day
  return created <= dayEnd && updated >= dayStart;
}

// ─── JSONL Parsing ──────────────────────────────────────────────────────────

interface JsonlEntry {
  role?: string;
  content?: unknown[];
  type?: string;
  name?: string;
}

/**
 * Parse a session JSONL file and extract tool calls and prompt counts.
 * Supports Kiro CLI v3 format.
 */
export function parseSessionJsonl(content: string): { promptCount: number; toolCalls: Record<string, number> } {
  const toolCalls: Record<string, number> = {};
  let promptCount = 0;

  for (const line of content.split("\n")) {
    if (!line.trim()) continue;

    try {
      const entry = JSON.parse(line);
      const payload = entry.payload || entry; // v3 uses payload wrapper

      // Count user prompts
      if (payload.type === "user") {
        promptCount++;
      }

      // Count tool calls in v3 format
      if (payload.type === "tool_call") {
        const toolName = payload.toolName || "unknown";
        toolCalls[toolName] = (toolCalls[toolName] || 0) + 1;
      }

      // Legacy format support (v2)
      if (entry.role === "user") {
        promptCount++;
      }

      // Legacy assistant messages with tool use blocks (v2)
      if (entry.role === "assistant" && Array.isArray(entry.content)) {
        for (const block of entry.content) {
          if (block.kind === "tool_use" || block.type === "tool_use") {
            const toolName = block.name || block.data?.name || "unknown";
            toolCalls[toolName] = (toolCalls[toolName] || 0) + 1;
          }
        }
      }

      // Legacy top-level tool use (v2)
      if (entry.type === "tool_use" || entry.kind === "tool_use") {
        const toolName = entry.name || "unknown";
        toolCalls[toolName] = (toolCalls[toolName] || 0) + 1;
      }
    } catch {
      // Skip malformed lines
    }
  }

  return { promptCount, toolCalls };
}

/**
 * Calculate session duration in minutes from timestamps.
 */
export function calculateDuration(createdAt: string, updatedAt: string): number {
  const start = new Date(createdAt);
  const end = new Date(updatedAt || createdAt);
  const diffMs = end.getTime() - start.getTime();
  return Math.max(0, Math.round(diffMs / 60_000));
}

// ─── Collector ──────────────────────────────────────────────────────────────

/**
 * Discover session files in the Kiro CLI v3 sessions directory.
 * Format: ~/.kiro/sessions/{workspace_id}/sess_{uuid}/session.json
 */
export function discoverSessionFiles(sessionsDir: string): string[] {
  if (!existsSync(sessionsDir)) return [];

  const sessionIds: string[] = [];
  const workspaceDirs = readdirSync(sessionsDir);

  for (const workspaceDir of workspaceDirs) {
    const workspacePath = join(sessionsDir, workspaceDir);
    
    // Skip if not a directory or not a 16-char workspace ID
    if (workspaceDir.length !== 16) continue;
    
    try {
      const sessionDirs = readdirSync(workspacePath);
      for (const sessionDir of sessionDirs) {
        if (sessionDir.startsWith("sess_") && existsSync(join(workspacePath, sessionDir, "session.json"))) {
          sessionIds.push(sessionDir.replace("sess_", ""));
        }
      }
    } catch {
      // Not a directory or can't read it, skip
      continue;
    }
  }

  return sessionIds;
}

/**
 * Collect Kiro session data for a given date.
 */
export async function collectKiroSessions(
  date: string,
  config: Config
): Promise<CollectorResult<KiroCollectorData>> {
  const errors: string[] = [];
  const sessionsDir = expandHome(KIRO_SESSIONS_DIR);

  if (!existsSync(sessionsDir)) {
    return {
      success: true,
      data: {
        sessions: [],
        totalDurationMinutes: 0,
        totalPrompts: 0,
        toolUsageAggregate: {},
      },
      errors: ["Kiro sessions directory not found"],
      source: "kiro",
    };
  }

  const sessionIds = discoverSessionFiles(sessionsDir);
  const sessions: KiroSession[] = [];
  const toolUsageAggregate: Record<string, number> = {};
  let totalPrompts = 0;
  let totalDurationMinutes = 0;

  for (const sessionId of sessionIds) {
    // Find the workspace directory containing this session
    const workspaceDirs = readdirSync(sessionsDir).filter(f => 
      f.length === 16 && existsSync(join(sessionsDir, f))
    );
    
    let metaPath = "";
    let jsonlPath = "";
    
    for (const workspaceDir of workspaceDirs) {
      const sessionPath = join(sessionsDir, workspaceDir, `sess_${sessionId}`);
      const candidateMetaPath = join(sessionPath, "session.json");
      const candidateJsonlPath = join(sessionPath, "messages.jsonl");
      
      if (existsSync(candidateMetaPath)) {
        metaPath = candidateMetaPath;
        jsonlPath = candidateJsonlPath;
        break;
      }
    }
    
    if (!metaPath) continue;

    try {
      // Read and validate metadata
      const metaContent = readFileSync(metaPath, "utf-8");
      const meta = parseSessionMeta(metaContent);
      if (!meta) continue;

      // Check if session overlaps with target date
      if (!isSessionOnDate(meta, date)) continue;

      // Parse JSONL for tool usage and prompts
      let promptCount = 0;
      let toolCalls: Record<string, number> = {};

      if (existsSync(jsonlPath)) {
        const jsonlContent = readFileSync(jsonlPath, "utf-8");
        const parsed = parseSessionJsonl(jsonlContent);
        promptCount = parsed.promptCount;
        toolCalls = parsed.toolCalls;
      }

      const durationMinutes = calculateDuration(meta.createdAt, meta.lastModifiedAt || meta.createdAt);

      sessions.push({
        sessionId: meta.id,
        createdAt: meta.createdAt,
        updatedAt: meta.lastModifiedAt || meta.createdAt,
        title: meta.title || "Untitled",
        cwd: meta.workspacePaths[0] || "",
        promptCount,
        toolCalls,
        durationMinutes,
      });

      // Aggregate
      totalPrompts += promptCount;
      totalDurationMinutes += durationMinutes;
      for (const [tool, count] of Object.entries(toolCalls)) {
        toolUsageAggregate[tool] = (toolUsageAggregate[tool] || 0) + count;
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(`Failed to parse session ${sessionId}: ${msg}`);
    }
  }

  // Sort sessions chronologically
  sessions.sort((a, b) => a.createdAt.localeCompare(b.createdAt));

  return {
    success: true,
    data: {
      sessions,
      totalDurationMinutes,
      totalPrompts,
      toolUsageAggregate,
    },
    errors,
    source: "kiro",
  };
}

// ─── Collector Interface ────────────────────────────────────────────────────

export const kiroCollector = {
  name: "kiro",
  collect: collectKiroSessions,
};
