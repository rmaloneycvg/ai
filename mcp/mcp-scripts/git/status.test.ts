import { describe, it, expect } from "vitest";
import { parseStatus } from "./status";

describe("parseStatus", () => {
  it("parses staged files", () => {
    const input = "M  src/index.ts\nA  src/new.ts";
    const result = parseStatus(input);

    expect(result.staged).toEqual([
      { path: "src/index.ts", index: "M", workTree: " " },
      { path: "src/new.ts", index: "A", workTree: " " },
    ]);
    expect(result.unstaged).toEqual([]);
    expect(result.untracked).toEqual([]);
  });

  it("parses unstaged files", () => {
    const input = " M src/index.ts\n D src/old.ts";
    const result = parseStatus(input);

    expect(result.staged).toEqual([]);
    expect(result.unstaged).toEqual([
      { path: "src/index.ts", index: " ", workTree: "M" },
      { path: "src/old.ts", index: " ", workTree: "D" },
    ]);
  });

  it("parses untracked files", () => {
    const input = "?? new-file.ts\n?? another.ts";
    const result = parseStatus(input);

    expect(result.untracked).toEqual(["new-file.ts", "another.ts"]);
    expect(result.staged).toEqual([]);
    expect(result.unstaged).toEqual([]);
  });

  it("parses mixed status", () => {
    const input = "MM src/both.ts\nA  src/added.ts\n?? untracked.ts";
    const result = parseStatus(input);

    expect(result.staged).toEqual([
      { path: "src/both.ts", index: "M", workTree: "M" },
      { path: "src/added.ts", index: "A", workTree: " " },
    ]);
    expect(result.unstaged).toEqual([
      { path: "src/both.ts", index: "M", workTree: "M" },
    ]);
    expect(result.untracked).toEqual(["untracked.ts"]);
  });

  it("handles empty input", () => {
    const result = parseStatus("");
    expect(result.staged).toEqual([]);
    expect(result.unstaged).toEqual([]);
    expect(result.untracked).toEqual([]);
  });
});
