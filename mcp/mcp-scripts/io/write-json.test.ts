import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { writeJson } from "./write-json";
import { readFileSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";

const tmpDir = join(import.meta.dirname, "__test_tmp_write");

beforeEach(() => {
  mkdirSync(tmpDir, { recursive: true });
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

describe("writeJson", () => {
  it("writes JSON with default indent", () => {
    const file = join(tmpDir, "out.json");
    const result = writeJson(file, { key: "value" });

    expect(result.success).toBe(true);
    const content = readFileSync(file, "utf-8");
    expect(content).toBe('{\n  "key": "value"\n}\n');
  });

  it("writes JSON with custom indent", () => {
    const file = join(tmpDir, "out4.json");
    writeJson(file, { a: 1 }, { indent: 4 });

    const content = readFileSync(file, "utf-8");
    expect(content).toBe('{\n    "a": 1\n}\n');
  });

  it("creates parent directories", () => {
    const file = join(tmpDir, "nested", "deep", "file.json");
    const result = writeJson(file, [1, 2, 3]);

    expect(result.success).toBe(true);
    expect(existsSync(file)).toBe(true);
  });

  it("returns error for undefined data", () => {
    const file = join(tmpDir, "undef.json");
    const result = writeJson(file, undefined);

    expect(result.success).toBe(false);
    expect(result.error).toContain("undefined");
  });

  it("returns error for circular references", () => {
    const file = join(tmpDir, "circular.json");
    const obj: Record<string, unknown> = {};
    obj.self = obj;

    const result = writeJson(file, obj);
    expect(result.success).toBe(false);
    expect(result.error).toContain("not JSON-serializable");
  });
});
