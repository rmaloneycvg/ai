import { describe, it, expect } from "vitest";
import { ConfigSchema, loadConfig, expandHome, isCollectorEnabled, DEFAULT_CONFIG } from "./config.js";

describe("ConfigSchema", () => {
  it("validates a complete valid config", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: ["~/workspace"],
      author: { name: "Test User", email: "test@example.com" },
      sessionGapMinutes: 30,
      outputDir: "~/output",
      collectors: { git: { enabled: true } },
    });
    expect(result.success).toBe(true);
  });

  it("rejects config with empty workspacePaths", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: [],
      author: { name: "Test", email: "t@t.com" },
      sessionGapMinutes: 30,
      outputDir: "~/out",
      collectors: {},
    });
    expect(result.success).toBe(false);
  });

  it("rejects config with invalid email", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: ["~/ws"],
      author: { name: "Test", email: "not-an-email" },
      sessionGapMinutes: 30,
      outputDir: "~/out",
      collectors: {},
    });
    expect(result.success).toBe(false);
  });

  it("rejects config with negative sessionGapMinutes", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: ["~/ws"],
      author: { name: "Test", email: "t@t.com" },
      sessionGapMinutes: -5,
      outputDir: "~/out",
      collectors: {},
    });
    expect(result.success).toBe(false);
  });

  it("applies default sessionGapMinutes when not provided", () => {
    const result = ConfigSchema.parse({
      workspacePaths: ["~/ws"],
      author: { name: "Test", email: "t@t.com" },
      outputDir: "~/out",
      collectors: {},
    });
    expect(result.sessionGapMinutes).toBe(30);
  });

  it("accepts chromeUserOverride as optional", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: ["~/ws"],
      author: { name: "Test", email: "t@t.com" },
      sessionGapMinutes: 30,
      outputDir: "~/out",
      chromeUserOverride: "myuser",
      collectors: {},
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.chromeUserOverride).toBe("myuser");
    }
  });

  it("accepts collector config with nested values", () => {
    const result = ConfigSchema.safeParse({
      workspacePaths: ["~/ws"],
      author: { name: "Test", email: "t@t.com" },
      sessionGapMinutes: 30,
      outputDir: "~/out",
      collectors: {
        teams: { enabled: false, config: { clientId: "abc", tenantId: "xyz" } },
      },
    });
    expect(result.success).toBe(true);
  });
});

describe("loadConfig", () => {
  it("returns DEFAULT_CONFIG when file does not exist", () => {
    const config = loadConfig("/nonexistent/path/config.json");
    expect(config).toEqual(DEFAULT_CONFIG);
  });

  it("loads the actual config.json from disk", () => {
    const config = loadConfig();
    expect(config.workspacePaths).toContain("~/workspace");
    expect(config.author.email).toBe("rsmaloney@gmail.com");
    expect(config.collectors.git.enabled).toBe(true);
    expect(config.collectors.teams.enabled).toBe(false);
  });
});

describe("expandHome", () => {
  it("expands ~ to home directory", () => {
    const result = expandHome("~/workspace");
    expect(result).not.toContain("~");
    expect(result).toMatch(/\/workspace$/);
  });

  it("leaves absolute paths unchanged", () => {
    expect(expandHome("/usr/local/bin")).toBe("/usr/local/bin");
  });

  it("leaves relative paths unchanged", () => {
    expect(expandHome("relative/path")).toBe("relative/path");
  });
});

describe("isCollectorEnabled", () => {
  it("returns true for enabled collector", () => {
    expect(isCollectorEnabled(DEFAULT_CONFIG, "git")).toBe(true);
  });

  it("returns false for disabled collector", () => {
    expect(isCollectorEnabled(DEFAULT_CONFIG, "teams")).toBe(false);
  });

  it("returns false for unknown collector", () => {
    expect(isCollectorEnabled(DEFAULT_CONFIG, "nonexistent")).toBe(false);
  });
});
