/**
 * Aggregator — orchestrates all collectors into a single generateSummary pipeline.
 */

import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { loadConfig, expandHome, isCollectorEnabled } from "./config.js";
import { collectGitCommits } from "./collectors/git-collector.js";
import { collectKiroSessions } from "./collectors/kiro-collector.js";
import { collectChromeHistory } from "./collectors/chrome-collector.js";
import { collectTeamsMeetings } from "./collectors/teams-collector.js";
import { collectGoogleMeetMeetings } from "./collectors/google-meet-collector.js";
import { collectZoomMeetings } from "./collectors/zoom-collector.js";
import { collectSlackActivity } from "./collectors/slack-collector.js";
import { collectOutlookEmails } from "./collectors/outlook-collector.js";
import { categorizeCommits } from "./categorizer.js";
import { flagAiAssistedCommits } from "./ai-flagger.js";
import { estimateEditTime } from "./collectors/time-estimator.js";
import { renderJson, renderMarkdown } from "./renderer.js";
import type {
  Config,
  WorkSummary,
  GitCommitEntry,
  KiroCollectorData,
  ChromeCollectorData,
  CommunicationData,
  TimeEstimate,
} from "./types.js";

// ─── Pipeline Result ────────────────────────────────────────────────────────

export interface AggregatorResult {
  success: boolean;
  summary: WorkSummary | null;
  markdown: string | null;
  outputFiles: { json?: string; markdown?: string };
  collectorResults: {
    name: string;
    success: boolean;
    durationMs: number;
    errors: string[];
  }[];
  errors: string[];
}

// ─── Collector Runner ───────────────────────────────────────────────────────

async function runCollector<T>(
  name: string,
  enabled: boolean,
  fn: () => Promise<{ success: boolean; data: T | null; errors: string[] }>
): Promise<{ name: string; success: boolean; data: T | null; durationMs: number; errors: string[] }> {
  if (!enabled) {
    return { name, success: true, data: null, durationMs: 0, errors: [`${name}: disabled`] };
  }

  const start = Date.now();
  try {
    const result = await fn();
    return {
      name,
      success: result.success,
      data: result.data,
      durationMs: Date.now() - start,
      errors: result.errors,
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      name,
      success: false,
      data: null,
      durationMs: Date.now() - start,
      errors: [`${name} collector crashed: ${msg}`],
    };
  }
}

// ─── Main Pipeline ──────────────────────────────────────────────────────────

/**
 * Generate a complete work summary for the given date.
 */
export async function generateSummary(
  date?: string,
  configPath?: string
): Promise<AggregatorResult> {
  const targetDate = date || new Date().toISOString().split("T")[0];
  const config = loadConfig(configPath);
  const errors: string[] = [];
  const collectorResults: AggregatorResult["collectorResults"] = [];

  // ── Run collectors in parallel ──────────────────────────────────────────

  const [gitResult, kiroResult, chromeResult, teamsResult, meetResult, zoomResult, slackResult, outlookResult] =
    await Promise.all([
      runCollector("git", isCollectorEnabled(config, "git"), () => collectGitCommits(targetDate, config)),
      runCollector("kiro", isCollectorEnabled(config, "kiro"), () => collectKiroSessions(targetDate, config)),
      runCollector("chrome", isCollectorEnabled(config, "chrome"), () => collectChromeHistory(targetDate, config)),
      runCollector("teams", isCollectorEnabled(config, "teams"), () => collectTeamsMeetings(targetDate, config)),
      runCollector("google-meet", isCollectorEnabled(config, "google-meet"), () => collectGoogleMeetMeetings(targetDate, config)),
      runCollector("zoom", isCollectorEnabled(config, "zoom"), () => collectZoomMeetings(targetDate, config)),
      runCollector("slack", isCollectorEnabled(config, "slack"), () => collectSlackActivity(targetDate, config)),
      runCollector("outlook", isCollectorEnabled(config, "outlook"), () => collectOutlookEmails(targetDate, config)),
    ]);

  // Collect results
  for (const r of [gitResult, kiroResult, chromeResult, teamsResult, meetResult, zoomResult, slackResult, outlookResult]) {
    collectorResults.push({
      name: r.name,
      success: r.success,
      durationMs: r.durationMs,
      errors: r.errors,
    });
  }

  // ── Process git commits ─────────────────────────────────────────────────

  let commits: GitCommitEntry[] = gitResult.data?.commits || [];

  // Categorize
  categorizeCommits(commits);

  // Flag AI-assisted
  const kiroData: KiroCollectorData | null = kiroResult.data;
  if (kiroData && kiroData.sessions.length > 0) {
    flagAiAssistedCommits(commits, kiroData.sessions, { preferCwdMatch: true });
  }

  // ── Estimate edit time ──────────────────────────────────────────────────

  const timeEstimate: TimeEstimate = estimateEditTime({
    commits,
    kiroSessions: kiroData?.sessions || [],
    gapMinutes: config.sessionGapMinutes,
  });

  // ── Build communication data ────────────────────────────────────────────

  const communications: CommunicationData = {
    teams: teamsResult.data || null,
    googleMeet: meetResult.data || null,
    zoom: zoomResult.data || null,
    slack: slackResult.data || null,
    outlook: outlookResult.data || null,
  };

  // ── Render output ───────────────────────────────────────────────────────

  const chromeData: ChromeCollectorData | null = chromeResult.data;

  const summary = renderJson({
    date: targetDate,
    authorName: config.author.name,
    commits,
    kiroData,
    chromeData,
    communications,
    timeEstimate,
  });

  const markdown = renderMarkdown(summary);

  // ── Write output files ──────────────────────────────────────────────────

  const outputFiles: { json?: string; markdown?: string } = {};

  try {
    const outputDir = expandHome(config.outputDir);
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    const jsonPath = join(outputDir, `${targetDate}.json`);
    const mdPath = join(outputDir, `${targetDate}.md`);

    writeFileSync(jsonPath, JSON.stringify(summary, null, 2), "utf-8");
    writeFileSync(mdPath, markdown, "utf-8");

    outputFiles.json = jsonPath;
    outputFiles.markdown = mdPath;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    errors.push(`Failed to write output files: ${msg}`);
  }

  return {
    success: true,
    summary,
    markdown,
    outputFiles,
    collectorResults,
    errors,
  };
}

/**
 * Get the current configuration and collector status.
 */
export function getStatus(configPath?: string): {
  config: Config;
  collectors: { name: string; enabled: boolean; hasCredentials: boolean }[];
} {
  const config = loadConfig(configPath);

  const collectors = Object.entries(config.collectors).map(([name, toggle]) => {
    const collectorConfig = toggle.config || {};
    const hasCredentials = Object.values(collectorConfig).some(
      (v) => typeof v === "string" && v.length > 0
    );
    return { name, enabled: toggle.enabled, hasCredentials };
  });

  return { config, collectors };
}
