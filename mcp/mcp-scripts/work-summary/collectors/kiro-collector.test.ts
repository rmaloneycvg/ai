import { describe, it, expect } from "vitest";
import {
  parseSessionMeta,
  isSessionOnDate,
  parseSessionJsonl,
  calculateDuration,
  discoverSessionFiles,
} from "./kiro-collector.js";

// ─── parseSessionMeta ───────────────────────────────────────────────────────

describe("parseSessionMeta", () => {
  it("parses valid session metadata", () => {
    const meta = parseSessionMeta(JSON.stringify({
      session_id: "abc-123",
      cwd: "/home/user/workspace/project",
      created_at: "2026-08-24T10:00:00.000Z",
      updated_at: "2026-08-24T11:30:00.000Z",
      title: "feat: login flow",
    }));

    expect(meta).not.toBeNull();
    expect(meta!.session_id).toBe("abc-123");
    expect(meta!.cwd).toBe("/home/user/workspace/project");
    expect(meta!.title).toBe("feat: login flow");
  });

  it("returns null for invalid JSON", () => {
    expect(parseSessionMeta("not json")).toBeNull();
  });

  it("returns null for missing session_id", () => {
    expect(parseSessionMeta(JSON.stringify({
      cwd: "/path",
      created_at: "2026-08-24T10:00:00Z",
    }))).toBeNull();
  });

  it("returns null for missing created_at", () => {
    expect(parseSessionMeta(JSON.stringify({
      session_id: "abc",
      cwd: "/path",
    }))).toBeNull();
  });
});

// ─── isSessionOnDate ────────────────────────────────────────────────────────

describe("isSessionOnDate", () => {
  const baseMeta = {
    session_id: "test",
    cwd: "/path",
    title: "test",
  };

  it("returns true for session created and updated on target date", () => {
    expect(isSessionOnDate({
      ...baseMeta,
      created_at: "2026-08-24T10:00:00Z",
      updated_at: "2026-08-24T14:00:00Z",
    }, "2026-08-24")).toBe(true);
  });

  it("returns true for session spanning midnight (created day before, updated on target)", () => {
    expect(isSessionOnDate({
      ...baseMeta,
      created_at: "2026-08-23T22:00:00Z",
      updated_at: "2026-08-24T02:00:00Z",
    }, "2026-08-24")).toBe(true);
  });

  it("returns true for session created on target date, updated next day", () => {
    expect(isSessionOnDate({
      ...baseMeta,
      created_at: "2026-08-24T23:00:00Z",
      updated_at: "2026-08-25T01:00:00Z",
    }, "2026-08-24")).toBe(true);
  });

  it("returns false for session entirely before target date", () => {
    expect(isSessionOnDate({
      ...baseMeta,
      created_at: "2026-08-22T10:00:00Z",
      updated_at: "2026-08-22T14:00:00Z",
    }, "2026-08-24")).toBe(false);
  });

  it("returns false for session entirely after target date", () => {
    expect(isSessionOnDate({
      ...baseMeta,
      created_at: "2026-08-25T10:00:00Z",
      updated_at: "2026-08-25T14:00:00Z",
    }, "2026-08-24")).toBe(false);
  });
});

// ─── parseSessionJsonl ──────────────────────────────────────────────────────

describe("parseSessionJsonl", () => {
  it("counts user prompts", () => {
    const content = [
      JSON.stringify({ role: "user", content: [{ type: "text", text: "help me" }] }),
      JSON.stringify({ role: "assistant", content: [{ type: "text", text: "sure" }] }),
      JSON.stringify({ role: "user", content: [{ type: "text", text: "next thing" }] }),
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.promptCount).toBe(2);
  });

  it("counts tool_use blocks in assistant messages", () => {
    const content = [
      JSON.stringify({
        role: "assistant",
        content: [
          { kind: "tool_use", name: "read_file", data: {} },
          { kind: "tool_use", name: "grep_search", data: {} },
          { kind: "tool_use", name: "read_file", data: {} },
        ],
      }),
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.toolCalls).toEqual({ read_file: 2, grep_search: 1 });
  });

  it("handles type: tool_use format", () => {
    const content = [
      JSON.stringify({
        role: "assistant",
        content: [
          { type: "tool_use", name: "execute_bash" },
        ],
      }),
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.toolCalls).toEqual({ execute_bash: 1 });
  });

  it("handles top-level tool_use entries", () => {
    const content = [
      JSON.stringify({ type: "tool_use", name: "web_fetch" }),
      JSON.stringify({ type: "tool_use", name: "web_fetch" }),
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.toolCalls).toEqual({ web_fetch: 2 });
  });

  it("skips malformed lines", () => {
    const content = [
      "not json at all",
      JSON.stringify({ role: "user", content: [] }),
      "{ broken",
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.promptCount).toBe(1);
  });

  it("handles empty content", () => {
    const result = parseSessionJsonl("");
    expect(result.promptCount).toBe(0);
    expect(result.toolCalls).toEqual({});
  });

  it("handles mixed content with prompts and tools", () => {
    const content = [
      JSON.stringify({ role: "user", content: [{ type: "text", text: "find files" }] }),
      JSON.stringify({
        role: "assistant",
        content: [
          { kind: "tool_use", name: "grep_search" },
          { kind: "text", text: "Found these:" },
        ],
      }),
      JSON.stringify({ role: "user", content: [{ type: "text", text: "read that one" }] }),
      JSON.stringify({
        role: "assistant",
        content: [
          { kind: "tool_use", name: "read_file" },
        ],
      }),
    ].join("\n");

    const result = parseSessionJsonl(content);
    expect(result.promptCount).toBe(2);
    expect(result.toolCalls).toEqual({ grep_search: 1, read_file: 1 });
  });
});

// ─── calculateDuration ──────────────────────────────────────────────────────

describe("calculateDuration", () => {
  it("calculates duration in minutes", () => {
    expect(calculateDuration(
      "2026-08-24T10:00:00Z",
      "2026-08-24T11:30:00Z"
    )).toBe(90);
  });

  it("returns 0 for same timestamps", () => {
    expect(calculateDuration(
      "2026-08-24T10:00:00Z",
      "2026-08-24T10:00:00Z"
    )).toBe(0);
  });

  it("returns 0 for invalid order (negative)", () => {
    expect(calculateDuration(
      "2026-08-24T12:00:00Z",
      "2026-08-24T10:00:00Z"
    )).toBe(0);
  });

  it("handles multi-hour sessions", () => {
    expect(calculateDuration(
      "2026-08-24T08:00:00Z",
      "2026-08-24T17:30:00Z"
    )).toBe(570); // 9.5 hours
  });
});

// ─── discoverSessionFiles ───────────────────────────────────────────────────

describe("discoverSessionFiles", () => {
  it("returns empty array for nonexistent directory", () => {
    expect(discoverSessionFiles("/nonexistent/path")).toEqual([]);
  });
});
