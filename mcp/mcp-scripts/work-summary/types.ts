/**
 * Shared types for the Work Summary Tracker.
 */

// ─── Collector Interface ────────────────────────────────────────────────────

export interface CollectorResult<T> {
  success: boolean;
  data: T | null;
  errors: string[];
  source: string;
}

export interface Collector<T> {
  name: string;
  collect(date: string, config: Config): Promise<CollectorResult<T>>;
}

// ─── Configuration ──────────────────────────────────────────────────────────

export interface AuthorConfig {
  name: string;
  email: string;
}

export interface CollectorToggle {
  enabled: boolean;
  config?: Record<string, unknown>;
}

export interface Config {
  workspacePaths: string[];
  author: AuthorConfig;
  chromeUserOverride?: string;
  sessionGapMinutes: number;
  outputDir: string;
  collectors: Record<string, CollectorToggle>;
}

// ─── Timeline ───────────────────────────────────────────────────────────────

export interface TimelineEntry {
  timestamp: string;
  type: "commit" | "ai_session" | "search" | "meeting" | "devtools" | "slack" | "email";
  description: string;
  repo?: string;
  aiAssisted?: boolean;
  category?: WorkCategory;
  source: string;
}

// ─── Git ────────────────────────────────────────────────────────────────────

export type FileStatus = "A" | "M" | "D" | "R" | "C";

export interface FileChange {
  path: string;
  status: FileStatus;
}

export interface GitCommitEntry {
  hash: string;
  timestamp: string;
  message: string;
  branch: string;
  repoName: string;
  repoPath: string;
  files: FileChange[];
  categories: WorkCategory[];
  aiAssisted: boolean;
  sessionId?: string;
}

export type WorkCategory =
  | "feature"
  | "refactor"
  | "unit-test"
  | "integration-test"
  | "performance-test"
  | "documentation";

// ─── Kiro / AI Sessions ─────────────────────────────────────────────────────

export interface KiroSession {
  sessionId: string;
  createdAt: string;
  updatedAt: string;
  title: string;
  cwd: string;
  promptCount: number;
  toolCalls: Record<string, number>;
  durationMinutes: number;
}

export interface KiroCollectorData {
  sessions: KiroSession[];
  totalDurationMinutes: number;
  totalPrompts: number;
  toolUsageAggregate: Record<string, number>;
}

// ─── Chrome / Browser ───────────────────────────────────────────────────────

export type BrowserEntryCategory = "search" | "devtools" | "general";

export interface BrowserEntry {
  timestamp: string;
  url: string;
  title: string;
  category: BrowserEntryCategory;
  searchQuery?: string;
}

export interface ChromeCollectorData {
  entries: BrowserEntry[];
  searchCount: number;
  devToolsSessions: number;
}

// ─── Communication Stubs ────────────────────────────────────────────────────

export interface MeetingEntry {
  timestamp: string;
  duration: number;
  title: string;
  attendeeCount?: number;
  source: string;
}

export interface SlackEntry {
  timestamp: string;
  channel: string;
  messageCount: number;
  source: string;
}

export interface OutlookEntry {
  timestamp: string;
  subject: string;
  from: string;
  isRead: boolean;
  source: string;
}

export interface CommunicationData {
  teams: MeetingEntry[] | null;
  googleMeet: MeetingEntry[] | null;
  zoom: MeetingEntry[] | null;
  slack: SlackEntry[] | null;
  outlook: OutlookEntry[] | null;
}

// ─── Time Estimation ────────────────────────────────────────────────────────

export interface EditSession {
  start: string;
  end: string;
  durationMinutes: number;
  aiAssisted: boolean;
}

export interface TimeEstimate {
  totalEditMinutes: number;
  aiAssistedMinutes: number;
  manualMinutes: number;
  sessions: EditSession[];
}

// ─── Summary Output ─────────────────────────────────────────────────────────

export interface CategoryCounts {
  features: number;
  refactors: number;
  unitTests: number;
  integrationTests: number;
  perfTests: number;
  docs: number;
}

export interface SummaryStats {
  totalCommits: number;
  totalEditTime: string;
  aiAssistedTime: string;
  manualTime: string;
  categories: CategoryCounts;
}

export interface FileChangeSummary {
  path: string;
  repo: string;
  status: FileStatus;
  category: WorkCategory | "uncategorized";
}

export interface AiSessionsSummary {
  count: number;
  totalDuration: string;
  toolUsage: Record<string, number>;
}

export interface BrowserActivitySummary {
  searches: { query: string; timestamp: string }[];
  devToolsSessions: number;
}

export interface TimeBreakdown {
  coding: string;
  meetings: string;
  aiPaired: string;
  manual: string;
}

export interface WorkSummary {
  date: string;
  author: string;
  summary: SummaryStats;
  timeline: TimelineEntry[];
  filesChanged: FileChangeSummary[];
  aiSessions: AiSessionsSummary;
  browserActivity: BrowserActivitySummary;
  communications: CommunicationData;
  timeBreakdown: TimeBreakdown;
}
