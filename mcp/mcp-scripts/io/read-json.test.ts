import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { readJson } from "./read-json";
import { writeFileSync, mkdirSync, rmSync } from "node:fs";
import { join } from "node:path";

const tmpDir = join(import.meta.dirname, "__test_tmp_read");

beforeEach(() => {
  mkdirSync(tmpDir, { recursive: true });
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

describe("readJson", () => {
  it("reads valid JSON file", () => {
    const file = join(tmpDir, "valid.json");
    writeFileSync(file, '{"name":"test","version":1}');

    const result = readJson(file);
    expect(result.success).toBe(true);
    expect(result.data).toEqual({ name: "test", version: 1 });
  });

  it("reads JSON array", () => {
    const file = join(tmpDir, "array.json");
    writeFileSync(file, '[1, 2, 3]');

    const result = readJson(file);
    expect(result.success).toBe(true);
    expect(result.data).toEqual([1, 2, 3]);
  });

  it("returns error for missing file", () => {
    const result = readJson(join(tmpDir, "missing.json"));
    expect(result.success).toBe(false);
    expect(result.error).toContain("File not found");
  });

  it("returns error for invalid JSON", () => {
    const file = join(tmpDir, "invalid.json");
    writeFileSync(file, "not { valid json");

    const result = readJson(file);
    expect(result.success).toBe(false);
    expect(result.error).toContain("Parse error");
  });
});
