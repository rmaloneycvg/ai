/**
 * Configuration loader and schema for the Work Summary Tracker.
 */

import { z } from "zod";
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── Zod Schemas ────────────────────────────────────────────────────────────

const AuthorSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

const CollectorToggleSchema = z.object({
  enabled: z.boolean(),
  config: z.record(z.unknown()).optional(),
});

export const ConfigSchema = z.object({
  workspacePaths: z.array(z.string().min(1)).min(1),
  author: AuthorSchema,
  chromeUserOverride: z.string().optional(),
  sessionGapMinutes: z.number().int().positive().default(30),
  outputDir: z.string().min(1),
  collectors: z.record(CollectorToggleSchema),
});

export type Config = z.infer<typeof ConfigSchema>;

// ─── Defaults ───────────────────────────────────────────────────────────────

const DEFAULT_CONFIG_PATH = resolve(__dirname, "config.json");

export const DEFAULT_CONFIG: Config = {
  workspacePaths: ["~/workspace"],
  author: { name: "Ryan Maloney", email: "rsmaloney@gmail.com" },
  sessionGapMinutes: 30,
  outputDir: "~/workspace/work-summaries",
  collectors: {
    git: { enabled: true },
    kiro: { enabled: true },
    chrome: { enabled: true },
    teams: { enabled: false },
    "google-meet": { enabled: false },
    zoom: { enabled: false },
    slack: { enabled: false },
    outlook: { enabled: false },
  },
};

// ─── Loader ─────────────────────────────────────────────────────────────────

/**
 * Resolve ~ to the user's home directory.
 */
export function expandHome(p: string): string {
  if (p.startsWith("~/") || p === "~") {
    return resolve(process.env.HOME || "/home/ryanm", p.slice(2));
  }
  return p;
}

/**
 * Load configuration from disk, falling back to defaults.
 * Validates against the Zod schema and throws on invalid config.
 */
export function loadConfig(configPath?: string): Config {
  const filePath = configPath || DEFAULT_CONFIG_PATH;

  if (!existsSync(filePath)) {
    return DEFAULT_CONFIG;
  }

  const raw = readFileSync(filePath, "utf-8");
  const parsed = JSON.parse(raw);
  return ConfigSchema.parse(parsed);
}

/**
 * Check if a specific collector is enabled.
 */
export function isCollectorEnabled(config: Config, name: string): boolean {
  return config.collectors[name]?.enabled ?? false;
}

/**
 * Get collector-specific config values.
 */
export function getCollectorConfig(config: Config, name: string): Record<string, unknown> {
  return config.collectors[name]?.config ?? {};
}
