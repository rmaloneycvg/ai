#!/usr/bin/env node
/**
 * MCP Server: linear
 * Tools: linear_list_teams, linear_list_issues, linear_get_issue,
 *        linear_create_issue, linear_create_issues_bulk,
 *        linear_list_projects, linear_create_project,
 *        linear_list_cycles, linear_get_cycle_metrics,
 *        linear_create_cycle, linear_create_document,
 *        linear_create_relation
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { listTeams, listIssues, getIssue, listProjects, listCycles, getCycleMetrics } from "../linear/queries.js";
import { createIssue, createIssuesBulk, createProject, createCycle, createDocument, createIssueRelation } from "../linear/mutations.js";

const server = new McpServer({
  name: "linear",
  version: "0.1.0",
});

// ─── Read Operations ──────────────────────────────────────────────

server.tool(
  "linear_list_teams",
  "List all teams in the Linear workspace",
  {},
  async () => {
    try {
      const teams = await listTeams();
      return { content: [{ type: "text", text: JSON.stringify(teams, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_list_issues",
  "List issues for a team with optional filters (state, assignee, label, project, cycle, priority)",
  {
    teamId: z.string().describe("Team ID"),
    state: z.string().optional().describe("Filter by state name (e.g., 'In Progress', 'Done')"),
    assigneeId: z.string().optional().describe("Filter by assignee ID"),
    labelName: z.string().optional().describe("Filter by label name"),
    projectId: z.string().optional().describe("Filter by project (epic) ID"),
    cycleId: z.string().optional().describe("Filter by cycle (sprint) ID"),
    priority: z.number().optional().describe("Filter by priority (0=none, 1=urgent, 2=high, 3=medium, 4=low)"),
    first: z.number().optional().describe("Max results (default 50)"),
  },
  async ({ teamId, state, assigneeId, labelName, projectId, cycleId, priority, first }) => {
    try {
      const issues = await listIssues({
        teamId,
        filter: { state, assigneeId, labelName, projectId, cycleId, priority },
        first,
      });
      return { content: [{ type: "text", text: JSON.stringify(issues, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_get_issue",
  "Get a single issue by ID with full details",
  { issueId: z.string().describe("Issue ID") },
  async ({ issueId }) => {
    try {
      const issue = await getIssue(issueId);
      if (!issue) return { content: [{ type: "text", text: JSON.stringify({ error: "Issue not found" }) }], isError: true };
      return { content: [{ type: "text", text: JSON.stringify(issue, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_list_projects",
  "List all projects (epics) for a team with their issues",
  { teamId: z.string().describe("Team ID") },
  async ({ teamId }) => {
    try {
      const projects = await listProjects(teamId);
      return { content: [{ type: "text", text: JSON.stringify(projects, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_list_cycles",
  "List cycles (sprints) for a team",
  {
    teamId: z.string().describe("Team ID"),
    includeCompleted: z.boolean().optional().describe("Include completed cycles (default false)"),
  },
  async ({ teamId, includeCompleted }) => {
    try {
      const cycles = await listCycles(teamId, includeCompleted ?? false);
      return { content: [{ type: "text", text: JSON.stringify(cycles, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_get_cycle_metrics",
  "Get sprint metrics for the active cycle (or a specific cycle). Returns progress, completion rates, breakdown by assignee/label/priority.",
  {
    teamId: z.string().describe("Team ID"),
    cycleId: z.string().optional().describe("Specific cycle ID (defaults to active cycle)"),
  },
  async ({ teamId, cycleId }) => {
    try {
      const metrics = await getCycleMetrics(teamId, cycleId);
      if (!metrics) return { content: [{ type: "text", text: JSON.stringify({ error: "No active cycle found" }) }], isError: true };
      return { content: [{ type: "text", text: JSON.stringify(metrics, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Write Operations ─────────────────────────────────────────────

server.tool(
  "linear_create_issue",
  "Create a single issue (story, bug, task, or sub-issue). Set parentId for sub-issues.",
  {
    teamId: z.string().describe("Team ID"),
    title: z.string().describe("Issue title"),
    description: z.string().optional().describe("Issue description (markdown)"),
    priority: z.number().optional().describe("Priority: 0=none, 1=urgent, 2=high, 3=medium, 4=low"),
    estimate: z.number().optional().describe("Point estimate"),
    assigneeId: z.string().optional().describe("Assignee user ID"),
    labelIds: z.array(z.string()).optional().describe("Array of label IDs"),
    projectId: z.string().optional().describe("Project (epic) ID"),
    cycleId: z.string().optional().describe("Cycle (sprint) ID"),
    parentId: z.string().optional().describe("Parent issue ID (for sub-issues)"),
  },
  async (input) => {
    try {
      const result = await createIssue(input);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        isError: !result.success,
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_create_issues_bulk",
  "Create multiple issues at once. Input is a JSON array of issue objects (same fields as linear_create_issue).",
  {
    issues: z.string().describe("JSON array of issue objects with fields: teamId, title, description, priority, estimate, assigneeId, labelIds, projectId, cycleId, parentId"),
  },
  async ({ issues: issuesStr }) => {
    try {
      const issues = JSON.parse(issuesStr);
      if (!Array.isArray(issues)) throw new Error("Input must be a JSON array");
      const result = await createIssuesBulk(issues);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_create_project",
  "Create a project (epic) in Linear",
  {
    teamIds: z.array(z.string()).describe("Team IDs the project belongs to"),
    name: z.string().describe("Project name"),
    description: z.string().optional().describe("Project description (markdown)"),
    targetDate: z.string().optional().describe("Target completion date (ISO format)"),
    startDate: z.string().optional().describe("Start date (ISO format)"),
  },
  async (input) => {
    try {
      const result = await createProject(input);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        isError: !result.success,
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_create_cycle",
  "Create a cycle (sprint) for a team",
  {
    teamId: z.string().describe("Team ID"),
    name: z.string().optional().describe("Cycle name"),
    startsAt: z.string().describe("Start datetime (ISO format)"),
    endsAt: z.string().describe("End datetime (ISO format)"),
  },
  async (input) => {
    try {
      const result = await createCycle(input);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        isError: !result.success,
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_create_document",
  "Create a document in Linear (for design docs, meeting notes, sprint reports)",
  {
    title: z.string().describe("Document title"),
    content: z.string().describe("Document content (markdown)"),
    projectId: z.string().optional().describe("Associated project ID"),
  },
  async (input) => {
    try {
      const result = await createDocument(input);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        isError: !result.success,
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "linear_create_relation",
  "Create a relation between two issues (blocks, duplicate, related)",
  {
    issueId: z.string().describe("Source issue ID"),
    relatedIssueId: z.string().describe("Target issue ID"),
    type: z.enum(["blocks", "duplicate", "related"]).describe("Relation type"),
  },
  async (input) => {
    try {
      const result = await createIssueRelation(input);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        isError: !result.success,
      };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Server Startup ───────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("linear MCP server failed to start:", err);
  process.exit(1);
});
