/**
 * Template Renderer — produces JSON and Markdown output from aggregated work summary data.
 */

import type {
  WorkSummary,
  GitCommitEntry,
  KiroCollectorData,
  ChromeCollectorData,
  CommunicationData,
  TimeEstimate,
  TimelineEntry,
  FileChangeSummary,
  CategoryCounts,
  WorkCategory,
} from "./types.js";
import { classifyFile } from "./categorizer.js";

// ─── Duration Formatting ────────────────────────────────────────────────────

/**
 * Format minutes into human-readable duration string.
 */
export function formatDuration(minutes: number): string {
  if (minutes <= 0) return "0m";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}m`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

// ─── Timeline Building ──────────────────────────────────────────────────────

/**
 * Build chronological timeline entries from all data sources.
 */
export function buildTimeline(
  commits: GitCommitEntry[],
  kiroData: KiroCollectorData | null,
  chromeData: ChromeCollectorData | null
): TimelineEntry[] {
  const entries: TimelineEntry[] = [];

  // Git commits
  for (const commit of commits) {
    entries.push({
      timestamp: commit.timestamp,
      type: "commit",
      description: `[${commit.repoName}] ${commit.message}`,
      repo: commit.repoName,
      aiAssisted: commit.aiAssisted,
      category: commit.categories[0],
      source: "git",
    });
  }

  // Kiro sessions
  if (kiroData) {
    for (const session of kiroData.sessions) {
      entries.push({
        timestamp: session.createdAt,
        type: "ai_session",
        description: `AI session: ${session.title} (${formatDuration(session.durationMinutes)}, ${session.promptCount} prompts)`,
        source: "kiro",
      });
    }
  }

  // Chrome activity
  if (chromeData) {
    for (const entry of chromeData.entries) {
      if (entry.category === "search") {
        entries.push({
          timestamp: entry.timestamp,
          type: "search",
          description: `Search: ${entry.searchQuery || entry.title}`,
          source: "chrome",
        });
      } else if (entry.category === "devtools") {
        entries.push({
          timestamp: entry.timestamp,
          type: "devtools",
          description: `DevTools opened`,
          source: "chrome",
        });
      }
    }
  }

  // Sort chronologically
  entries.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  return entries;
}

// ─── Category Counting ──────────────────────────────────────────────────────

/**
 * Count test functions in a test file by reading its content.
 * Supports multiple languages and test frameworks.
 */
export function countTestFunctions(filePath: string, repoPath: string): number {
  try {
    const { readFileSync } = require("node:fs");
    const { join } = require("node:path");
    
    const fullPath = join(repoPath, filePath);
    const content = readFileSync(fullPath, "utf-8");
    
    const extension = filePath.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'py':
        return countPythonTests(content);
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
        return countJavaScriptTests(content);
      case 'cs':
        return countCSharpTests(content);
      case 'java':
        return countJavaTests(content);
      case 'go':
        return countGoTests(content);
      default:
        return 1; // Fallback for unknown file types
    }
  } catch {
    // File doesn't exist or can't be read (maybe deleted), assume 1 test per file
    return 1;
  }
}

/**
 * Count Python test functions (pytest, unittest)
 */
function countPythonTests(content: string): number {
  // Match various test function patterns:
  // - def test_*( (pytest style)
  // - def Test*( (unittest class methods starting with Test)
  // - async def test_*( (async tests)
  const testFunctionPattern = /^[ \t]*(?:async\s+)?def\s+(test_\w+|Test\w+)\s*\(/gm;
  const matches = content.match(testFunctionPattern);
  return matches ? matches.length : 0;
}

/**
 * Count JavaScript/TypeScript test functions (Jest, Vitest, Mocha, etc.)
 */
function countJavaScriptTests(content: string): number {
  // Match various JS/TS test patterns:
  // - test('...', () => {}) or test("...", () => {})
  // - it('...', () => {}) or it("...", () => {})
  // - describe.each or test.each (parameterized)
  const testPatterns = [
    /(?:^|\s)(?:test|it)\s*\(/gm,
    /(?:^|\s)(?:test|it)\.each\s*\(/gm,
    /(?:^|\s)(?:test|it)\.(?:skip|only|concurrent)\s*\(/gm,
  ];
  
  let total = 0;
  for (const pattern of testPatterns) {
    const matches = content.match(pattern);
    if (matches) total += matches.length;
  }
  
  return total;
}

/**
 * Count C# test functions (NUnit, xUnit, MSTest)
 */
function countCSharpTests(content: string): number {
  // Match C# test method patterns:
  // - [Test] public void TestMethod()
  // - [Fact] public void TestMethod() (xUnit)
  // - [TestMethod] public void TestMethod() (MSTest)
  const testPatterns = [
    /\[Test\]/gm,
    /\[Fact\]/gm,
    /\[Theory\]/gm,
    /\[TestMethod\]/gm,
  ];
  
  let total = 0;
  for (const pattern of testPatterns) {
    const matches = content.match(pattern);
    if (matches) total += matches.length;
  }
  
  return total;
}

/**
 * Count Java test functions (JUnit)
 */
function countJavaTests(content: string): number {
  // Match Java test method patterns:
  // - @Test public void testMethod()
  // - @ParameterizedTest
  const testPatterns = [
    /@Test/gm,
    /@ParameterizedTest/gm,
    /@RepeatedTest/gm,
  ];
  
  let total = 0;
  for (const pattern of testPatterns) {
    const matches = content.match(pattern);
    if (matches) total += matches.length;
  }
  
  return total;
}

/**
 * Count Go test functions
 */
function countGoTests(content: string): number {
  // Match Go test function patterns:
  // - func TestSomething(t *testing.T) {}
  // - func BenchmarkSomething(b *testing.B) {} (for performance tests)
  const testFunctionPattern = /^func\s+(Test\w+|Benchmark\w+)\s*\(/gm;
  const matches = content.match(testFunctionPattern);
  return matches ? matches.length : 0;
}

/**
 * Count files per category across all commits.
 * For test files, counts individual test functions. For other files, counts files.
 */
export function countCategories(commits: GitCommitEntry[]): CategoryCounts {
  const counts: CategoryCounts = {
    features: 0,
    refactors: 0,
    unitTests: 0,
    integrationTests: 0,
    perfTests: 0,
    docs: 0,
  };

  // Track unique files to avoid double counting
  const seenFiles = new Set<string>();

  for (const commit of commits) {
    for (const file of commit.files) {
      const fileKey = `${commit.repoName}:${file.path}`;
      
      // Skip if we've already counted this file
      if (seenFiles.has(fileKey)) continue;
      seenFiles.add(fileKey);

      // Categorize individual files
      const fileCategory = classifyFile(file.path);
      if (fileCategory) {
        let testCount = 1; // Default for non-Python or if parsing fails
        
        // For test files, count actual test functions
        if (fileCategory === "unit-test" || fileCategory === "integration-test" || fileCategory === "performance-test") {
          if (file.path.endsWith(".py") && file.status !== "D") {
            testCount = countTestFunctions(file.path, commit.repoPath);
          }
        }
        
        switch (fileCategory) {
          case "unit-test": counts.unitTests += testCount; break;
          case "integration-test": counts.integrationTests += testCount; break;
          case "performance-test": counts.perfTests += testCount; break;
          case "documentation": counts.docs++; break;
        }
      } else {
        // For non-test files, use commit-level categorization
        for (const commitCat of commit.categories) {
          switch (commitCat) {
            case "feature": counts.features++; break;
            case "refactor": counts.refactors++; break;
          }
          break; // Only count once per file
        }
      }
    }
  }

  return counts;
}

// ─── Files Changed Summary ──────────────────────────────────────────────────

/**
 * Build deduplicated file change summary from all commits.
 */
export function buildFilesChanged(commits: GitCommitEntry[]): FileChangeSummary[] {
  const seen = new Map<string, FileChangeSummary>();

  for (const commit of commits) {
    for (const file of commit.files) {
      const key = `${commit.repoName}:${file.path}`;
      if (!seen.has(key)) {
        seen.set(key, {
          path: file.path,
          repo: commit.repoName,
          status: file.status,
          category: commit.branch, // Use branch name instead of categories
        });
      }
    }
  }

  return Array.from(seen.values());
}

// ─── JSON Renderer ──────────────────────────────────────────────────────────

export interface RenderInput {
  date: string;
  authorName: string;
  commits: GitCommitEntry[];
  kiroData: KiroCollectorData | null;
  chromeData: ChromeCollectorData | null;
  communications: CommunicationData;
  timeEstimate: TimeEstimate;
}

/**
 * Render the full WorkSummary JSON object.
 */
export function renderJson(input: RenderInput): WorkSummary {
  const { date, authorName, commits, kiroData, chromeData, communications, timeEstimate } = input;

  const timeline = buildTimeline(commits, kiroData, chromeData);
  const categories = countCategories(commits);
  const filesChanged = buildFilesChanged(commits);

  return {
    date,
    author: authorName,
    summary: {
      totalCommits: commits.length,
      totalEditTime: formatDuration(timeEstimate.totalEditMinutes),
      aiAssistedTime: formatDuration(timeEstimate.aiAssistedMinutes),
      manualTime: formatDuration(timeEstimate.manualMinutes),
      categories,
    },
    timeline,
    filesChanged,
    aiSessions: {
      count: kiroData?.sessions.length || 0,
      totalDuration: formatDuration(kiroData?.totalDurationMinutes || 0),
      toolUsage: kiroData?.toolUsageAggregate || {},
    },
    browserActivity: {
      searches: chromeData?.entries
        .filter((e) => e.category === "search")
        .map((e) => ({ query: e.searchQuery || e.title, timestamp: e.timestamp })) || [],
      devToolsSessions: chromeData?.devToolsSessions || 0,
    },
    communications,
    timeBreakdown: {
      coding: formatDuration(timeEstimate.totalEditMinutes),
      meetings: "0m", // Will be populated when communication stubs are implemented
      aiPaired: formatDuration(timeEstimate.aiAssistedMinutes),
      manual: formatDuration(timeEstimate.manualMinutes),
    },
  };
}

// ─── Markdown Renderer ──────────────────────────────────────────────────────

/**
 * Render a full Markdown work summary from the JSON object.
 */
export function renderMarkdown(summary: WorkSummary): string {
  const lines: string[] = [];

  // Header
  lines.push(`# Daily Work Summary — ${summary.date}`);
  lines.push("");
  lines.push(`**Author:** ${summary.author}`);
  lines.push("");

  // Summary Stats
  lines.push("## Summary");
  lines.push("");
  lines.push("| Metric | Value |");
  lines.push("|--------|-------|");
  lines.push(`| Total Commits | ${summary.summary.totalCommits} |`);
  lines.push(`| Total Edit Time | ${summary.summary.totalEditTime} |`);
  lines.push(`| AI-Assisted Time | ${summary.summary.aiAssistedTime} |`);
  lines.push(`| Manual Time | ${summary.summary.manualTime} |`);
  lines.push(`| Features | ${summary.summary.categories.features} |`);
  lines.push(`| Refactors | ${summary.summary.categories.refactors} |`);
  lines.push(`| Unit Tests | ${summary.summary.categories.unitTests} |`);
  lines.push(`| Integration Tests | ${summary.summary.categories.integrationTests} |`);
  lines.push(`| Performance Tests | ${summary.summary.categories.perfTests} |`);
  lines.push(`| Documentation | ${summary.summary.categories.docs} |`);
  lines.push("");

  // Timeline
  lines.push("## Timeline");
  lines.push("");
  if (summary.timeline.length === 0) {
    lines.push("_No activity recorded._");
  } else {
    for (const entry of summary.timeline) {
      const time = formatTimeOnly(entry.timestamp);
      const badge = typeBadge(entry.type);
      const aiFlag = entry.aiAssisted ? " 🤖" : "";
      lines.push(`- \`${time}\` ${badge} ${entry.description}${aiFlag}`);
    }
  }
  lines.push("");

  // Accomplishments by Category
  lines.push("## Accomplishments by Category");
  lines.push("");
  renderCategorySection(lines, summary, "feature", "### Features");
  renderCategorySection(lines, summary, "refactor", "### Refactors");
  renderCategorySection(lines, summary, "unit-test", "### Unit Tests");
  renderCategorySection(lines, summary, "integration-test", "### Integration Tests");
  renderCategorySection(lines, summary, "performance-test", "### Performance Tests");
  renderCategorySection(lines, summary, "documentation", "### Documentation");

  // Files Changed
  lines.push("## Files Changed");
  lines.push("");
  if (summary.filesChanged.length === 0) {
    lines.push("_No files changed._");
  } else {
    lines.push("| Path | Repo | Status | Branch |");
    lines.push("|------|------|--------|--------|");
    for (const file of summary.filesChanged) {
      lines.push(`| \`${file.path}\` | ${file.repo} | ${file.status} | ${file.category} |`);
    }
  }
  lines.push("");

  // AI Activity
  lines.push("## AI Activity");
  lines.push("");
  lines.push(`- **Sessions:** ${summary.aiSessions.count}`);
  lines.push(`- **Total Duration:** ${summary.aiSessions.totalDuration}`);
  if (Object.keys(summary.aiSessions.toolUsage).length > 0) {
    lines.push("- **Top Tools:**");
    const sorted = Object.entries(summary.aiSessions.toolUsage)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);
    for (const [tool, count] of sorted) {
      lines.push(`  - \`${tool}\`: ${count}`);
    }
  }
  lines.push("");

  // Browser Research
  lines.push("## Browser Research");
  lines.push("");
  lines.push(`- **DevTools Sessions:** ${summary.browserActivity.devToolsSessions}`);
  if (summary.browserActivity.searches.length > 0) {
    // Deduplicate searches by query + timestamp (rounded to minute)
    const uniqueSearches = summary.browserActivity.searches.reduce((acc, search) => {
      const time = formatTimeOnly(search.timestamp);
      const key = `${time}:${search.query}`;
      if (!acc.has(key)) {
        acc.set(key, { query: search.query, timestamp: search.timestamp });
      }
      return acc;
    }, new Map<string, { query: string; timestamp: string }>());
    
    const deduped = Array.from(uniqueSearches.values());
    lines.push(`- **Searches (${deduped.length}):**`);
    for (const s of deduped.slice(0, 20)) {
      const time = formatTimeOnly(s.timestamp);
      lines.push(`  - \`${time}\` ${s.query}`);
    }
  } else {
    lines.push("- _No searches recorded._");
  }
  lines.push("");

  // Communications
  lines.push("## Communications");
  lines.push("");
  const comms = summary.communications;
  if (!comms.teams && !comms.googleMeet && !comms.zoom && !comms.slack && !comms.outlook) {
    lines.push("_Communication collectors not configured._");
  } else {
    if (comms.teams) lines.push(`- **Teams Meetings:** ${comms.teams.length}`);
    if (comms.googleMeet) lines.push(`- **Google Meet:** ${comms.googleMeet.length}`);
    if (comms.zoom) lines.push(`- **Zoom Meetings:** ${comms.zoom.length}`);
    if (comms.slack) lines.push(`- **Slack Channels Active:** ${comms.slack.length}`);
    if (comms.outlook) lines.push(`- **Emails:** ${comms.outlook.length}`);
  }
  lines.push("");

  // Time Breakdown
  lines.push("## Time Breakdown");
  lines.push("");
  lines.push("| Activity | Duration |");
  lines.push("|----------|----------|");
  lines.push(`| Coding | ${summary.timeBreakdown.coding} |`);
  lines.push(`| AI-Paired | ${summary.timeBreakdown.aiPaired} |`);
  lines.push(`| Manual | ${summary.timeBreakdown.manual} |`);
  lines.push(`| Meetings | ${summary.timeBreakdown.meetings} |`);
  lines.push("");

  return lines.join("\n");
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatTimeOnly(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch {
    return isoTimestamp;
  }
}

function typeBadge(type: string): string {
  switch (type) {
    case "commit": return "📝";
    case "ai_session": return "🤖";
    case "search": return "🔍";
    case "devtools": return "🛠️";
    case "meeting": return "📅";
    case "slack": return "💬";
    case "email": return "📧";
    default: return "•";
  }
}

function renderCategorySection(
  lines: string[],
  summary: WorkSummary,
  category: WorkCategory,
  heading: string
): void {
  const entries = summary.timeline.filter(
    (e) => e.type === "commit" && e.category === category
  );

  lines.push(heading);
  lines.push("");
  if (entries.length === 0) {
    lines.push("_None_");
  } else {
    for (const entry of entries) {
      const aiFlag = entry.aiAssisted ? " 🤖" : "";
      lines.push(`- ${entry.description}${aiFlag}`);
    }
  }
  lines.push("");
}
