import { describe, it, expect } from "vitest";
import { collectTeamsMeetings } from "./teams-collector.js";
import { collectGoogleMeetMeetings } from "./google-meet-collector.js";
import { collectZoomMeetings } from "./zoom-collector.js";
import { collectSlackActivity } from "./slack-collector.js";
import { collectOutlookEmails } from "./outlook-collector.js";
import type { Config } from "../types.js";

// ─── Shared test config (no credentials) ───────────────────────────────────

const configNoCredentials: Config = {
  workspacePaths: ["~/workspace"],
  author: { name: "Test", email: "test@example.com" },
  sessionGapMinutes: 30,
  outputDir: "~/output",
  collectors: {
    teams: { enabled: true },
    "google-meet": { enabled: true },
    zoom: { enabled: true },
    slack: { enabled: true },
    outlook: { enabled: true },
  },
};

const configWithEmptyStrings: Config = {
  workspacePaths: ["~/workspace"],
  author: { name: "Test", email: "test@example.com" },
  sessionGapMinutes: 30,
  outputDir: "~/output",
  collectors: {
    teams: { enabled: true, config: { clientId: "", tenantId: "", clientSecret: "" } },
    "google-meet": { enabled: true, config: { credentialsPath: "", calendarId: "primary" } },
    zoom: { enabled: true, config: { accountId: "", clientId: "", clientSecret: "" } },
    slack: { enabled: true, config: { botToken: "", userToken: "" } },
    outlook: { enabled: true, config: { clientId: "", tenantId: "", clientSecret: "" } },
  },
};

// ─── Teams ──────────────────────────────────────────────────────────────────

describe("Teams collector stub", () => {
  it("returns not-configured error without credentials", async () => {
    const result = await collectTeamsMeetings("2026-08-24", configNoCredentials);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.source).toBe("teams");
    expect(result.errors[0]).toContain("Not configured");
    expect(result.errors[0]).toContain("clientId");
  });

  it("returns not-configured with empty string credentials", async () => {
    const result = await collectTeamsMeetings("2026-08-24", configWithEmptyStrings);
    expect(result.success).toBe(false);
    expect(result.errors[0]).toContain("Not configured");
  });
});

// ─── Google Meet ────────────────────────────────────────────────────────────

describe("Google Meet collector stub", () => {
  it("returns not-configured error without credentials", async () => {
    const result = await collectGoogleMeetMeetings("2026-08-24", configNoCredentials);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.source).toBe("google-meet");
    expect(result.errors[0]).toContain("Not configured");
    expect(result.errors[0]).toContain("credentialsPath");
  });

  it("returns not-configured with empty string credentials", async () => {
    const result = await collectGoogleMeetMeetings("2026-08-24", configWithEmptyStrings);
    expect(result.success).toBe(false);
    expect(result.errors[0]).toContain("Not configured");
  });
});

// ─── Zoom ───────────────────────────────────────────────────────────────────

describe("Zoom collector stub", () => {
  it("returns not-configured error without credentials", async () => {
    const result = await collectZoomMeetings("2026-08-24", configNoCredentials);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.source).toBe("zoom");
    expect(result.errors[0]).toContain("Not configured");
    expect(result.errors[0]).toContain("accountId");
  });

  it("returns not-configured with empty string credentials", async () => {
    const result = await collectZoomMeetings("2026-08-24", configWithEmptyStrings);
    expect(result.success).toBe(false);
    expect(result.errors[0]).toContain("Not configured");
  });
});

// ─── Slack ──────────────────────────────────────────────────────────────────

describe("Slack collector stub", () => {
  it("returns not-configured error without credentials", async () => {
    const result = await collectSlackActivity("2026-08-24", configNoCredentials);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.source).toBe("slack");
    expect(result.errors[0]).toContain("Not configured");
    expect(result.errors[0]).toContain("botToken");
  });

  it("returns not-configured with empty string credentials", async () => {
    const result = await collectSlackActivity("2026-08-24", configWithEmptyStrings);
    expect(result.success).toBe(false);
    expect(result.errors[0]).toContain("Not configured");
  });
});

// ─── Outlook ────────────────────────────────────────────────────────────────

describe("Outlook collector stub", () => {
  it("returns not-configured error without credentials", async () => {
    const result = await collectOutlookEmails("2026-08-24", configNoCredentials);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.source).toBe("outlook");
    expect(result.errors[0]).toContain("Not configured");
    expect(result.errors[0]).toContain("clientId");
  });

  it("returns not-configured with empty string credentials", async () => {
    const result = await collectOutlookEmails("2026-08-24", configWithEmptyStrings);
    expect(result.success).toBe(false);
    expect(result.errors[0]).toContain("Not configured");
  });
});
