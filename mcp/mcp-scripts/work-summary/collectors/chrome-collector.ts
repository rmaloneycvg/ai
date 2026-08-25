/**
 * Chrome History Collector — reads Chrome browser history from the Windows
 * filesystem via WSL mount, extracting web searches and DevTools usage.
 */

import { existsSync, readdirSync, copyFileSync, unlinkSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import type { Config, CollectorResult, BrowserEntry, ChromeCollectorData } from "../types.js";

// ─── Chrome Time Conversion ─────────────────────────────────────────────────

/**
 * Chrome stores timestamps as microseconds since 1601-01-01 00:00:00 UTC.
 * Convert to Unix timestamp (milliseconds since 1970-01-01).
 */
const CHROME_EPOCH_OFFSET = 11644473600000000n; // microseconds between 1601 and 1970

export function chromeTimeToDate(chromeTime: bigint | number): Date {
  const microseconds = BigInt(chromeTime);
  const unixMicroseconds = microseconds - CHROME_EPOCH_OFFSET;
  const unixMs = Number(unixMicroseconds / 1000n);
  return new Date(unixMs);
}

export function dateToChromeTime(date: Date): bigint {
  const unixMs = BigInt(date.getTime());
  const unixMicroseconds = unixMs * 1000n;
  return unixMicroseconds + CHROME_EPOCH_OFFSET;
}

// ─── Windows User Detection ─────────────────────────────────────────────────

const WINDOWS_USERS_PATH = "/mnt/c/Users";
const SKIP_USERS = new Set(["Default", "Public", "All Users", "Default User", "desktop.ini"]);

/**
 * Auto-detect the Windows username by scanning /mnt/c/Users for Chrome profiles.
 */
export function detectWindowsUser(overrideUser?: string): string | null {
  if (overrideUser) {
    const historyPath = buildChromeHistoryPath(overrideUser);
    if (existsSync(historyPath)) return overrideUser;
    return null;
  }

  if (!existsSync(WINDOWS_USERS_PATH)) return null;

  const entries = readdirSync(WINDOWS_USERS_PATH, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (SKIP_USERS.has(entry.name)) continue;

    const historyPath = buildChromeHistoryPath(entry.name);
    if (existsSync(historyPath)) {
      return entry.name;
    }
  }

  return null;
}

/**
 * Build the full path to Chrome's History SQLite DB for a Windows user.
 */
export function buildChromeHistoryPath(windowsUser: string): string {
  return join(
    WINDOWS_USERS_PATH,
    windowsUser,
    "AppData",
    "Local",
    "Google",
    "Chrome",
    "User Data",
    "Default",
    "History"
  );
}

// ─── URL Classification ─────────────────────────────────────────────────────

const SEARCH_PATTERNS = [
  { pattern: /google\.com\/search\?/, extractQuery: (url: string) => new URL(url).searchParams.get("q") },
  { pattern: /bing\.com\/search\?/, extractQuery: (url: string) => new URL(url).searchParams.get("q") },
  { pattern: /duckduckgo\.com\/\?/, extractQuery: (url: string) => new URL(url).searchParams.get("q") },
  { pattern: /search\.yahoo\.com\/search/, extractQuery: (url: string) => new URL(url).searchParams.get("p") },
];

const DEVTOOLS_PATTERNS = [
  /^chrome-devtools:\/\//,
  /^devtools:\/\/devtools/,
  /chrome:\/\/inspect/,
];

export type BrowserEntryCategory = "search" | "devtools" | "general";

/**
 * Classify a URL and extract search query if applicable.
 */
export function classifyUrl(url: string): { category: BrowserEntryCategory; searchQuery?: string } {
  // Check DevTools
  for (const pattern of DEVTOOLS_PATTERNS) {
    if (pattern.test(url)) {
      return { category: "devtools" };
    }
  }

  // Check search engines
  for (const { pattern, extractQuery } of SEARCH_PATTERNS) {
    if (pattern.test(url)) {
      try {
        const query = extractQuery(url);
        return { category: "search", searchQuery: query || undefined };
      } catch {
        return { category: "search" };
      }
    }
  }

  return { category: "general" };
}

// ─── SQLite Query ───────────────────────────────────────────────────────────

/**
 * Query Chrome history using sql.js (pure JS SQLite).
 * Returns browser entries for the target date.
 */
export async function queryChromeHistory(
  dbPath: string,
  date: string
): Promise<BrowserEntry[]> {
  // Dynamic import to avoid loading sql.js unless needed
  const initSqlJs = (await import("sql.js")).default;
  const { readFileSync } = await import("node:fs");

  // Copy the DB to a temp file (Chrome locks the original)
  const tempDir = mkdtempSync(join(tmpdir(), "chrome-history-"));
  const tempDb = join(tempDir, "History");
  copyFileSync(dbPath, tempDb);

  try {
    const SQL = await initSqlJs();
    const buffer = readFileSync(tempDb);
    const db = new SQL.Database(buffer);

    // Calculate Chrome time range for the target date
    const dayStart = new Date(`${date}T00:00:00`);
    const dayEnd = new Date(`${date}T23:59:59.999`);
    const chromeStart = dateToChromeTime(dayStart);
    const chromeEnd = dateToChromeTime(dayEnd);

    const query = `
      SELECT u.url, u.title, v.visit_time
      FROM urls u
      JOIN visits v ON u.id = v.url
      WHERE v.visit_time BETWEEN ? AND ?
      ORDER BY v.visit_time ASC
    `;

    const results = db.exec(query, [chromeStart.toString(), chromeEnd.toString()]);
    db.close();

    const entries: BrowserEntry[] = [];

    if (results.length > 0) {
      for (const row of results[0].values) {
        const url = row[0] as string;
        const title = row[1] as string;
        const visitTime = BigInt(row[2] as string | number);

        const timestamp = chromeTimeToDate(visitTime).toISOString();
        const { category, searchQuery } = classifyUrl(url);

        entries.push({ timestamp, url, title, category, searchQuery });
      }
    }

    return entries;
  } finally {
    // Cleanup temp file
    try {
      unlinkSync(tempDb);
    } catch { /* ignore cleanup errors */ }
  }
}

// ─── Collector ──────────────────────────────────────────────────────────────

/**
 * Collect Chrome browser history for a given date.
 */
export async function collectChromeHistory(
  date: string,
  config: Config
): Promise<CollectorResult<ChromeCollectorData>> {
  const errors: string[] = [];

  // Detect Windows user
  const windowsUser = detectWindowsUser(config.chromeUserOverride);
  if (!windowsUser) {
    return {
      success: false,
      data: null,
      errors: ["Could not detect Windows Chrome installation. Set chromeUserOverride in config."],
      source: "chrome",
    };
  }

  const historyPath = buildChromeHistoryPath(windowsUser);
  if (!existsSync(historyPath)) {
    return {
      success: false,
      data: null,
      errors: [`Chrome History file not found at: ${historyPath}`],
      source: "chrome",
    };
  }

  try {
    const entries = await queryChromeHistory(historyPath, date);

    const searchEntries = entries.filter((e) => e.category === "search");
    const devToolsEntries = entries.filter((e) => e.category === "devtools");

    return {
      success: true,
      data: {
        entries,
        searchCount: searchEntries.length,
        devToolsSessions: devToolsEntries.length,
      },
      errors,
      source: "chrome",
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      data: null,
      errors: [`Failed to read Chrome history: ${msg}`],
      source: "chrome",
    };
  }
}

// ─── Collector Interface ────────────────────────────────────────────────────

export const chromeCollector = {
  name: "chrome",
  collect: collectChromeHistory,
};
