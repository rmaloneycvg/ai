#!/usr/bin/env node
/**
 * MCP Server: jira
 * Tools: jira_list_projects, jira_search_issues, jira_get_issue,
 *        jira_create_issue, jira_create_issues_bulk,
 *        jira_list_sprints, jira_get_sprint_metrics,
 *        jira_create_sprint, jira_create_link,
 *        jira_transition_issue, jira_add_comment
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { listProjects, listBoards, listSprints, searchIssues, getIssue, getSprintMetrics } from "../jira/queries.js";
import { createIssue, createIssuesBulk, createSprint, createIssueLink, transitionIssue, addComment } from "../jira/mutations.js";

const server = new McpServer({
  name: "jira",
  version: "0.1.0",
});

// ─── Read Operations ──────────────────────────────────────────────

server.tool(
  "jira_list_projects",
  "List all accessible Jira projects",
  {},
  async () => {
    try {
      const projects = await listProjects();
      return { content: [{ type: "text", text: JSON.stringify(projects, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jira_search_issues",
  "Search Jira issues using JQL. Returns issue key, summary, status, type, priority, assignee, labels, sprint, estimates.",
  {
    jql: z.string().describe("JQL query (e.g., 'project = PROJ AND sprint in openSprints()')"),
    maxResults: z.number().optional().describe("Max results (default 50)"),
  },
  async ({ jql, maxResults }) => {
    try {
      const issues = await searchIssues({ jql, maxResults });
      // Return a concise summary for each issue
      const summary = issues.map((i) => ({
        key: i.key,
        summary: i.fields.summary,
        status: i.fields.status.name,
        type: i.fields.issuetype.name,
        priority: i.fields.priority.name,
        assignee: i.fields.assignee?.displayName ?? null,
        labels: i.fields.labels,
        parent: i.fields.parent?.key ?? null,
        estimateHours: i.fields.timeoriginalestimate ? i.fields.timeoriginalestimate / 3600 : null,
        spentHours: i.fields.timespent ? i.fields.timespent / 3600 : null,
      }));
      return { content: [{ type: "text", text: JSON.stringify(summary, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jira_get_issue",
  "Get full details of a single Jira issue by key (e.g., PROJ-123)",
  { issueKey: z.string().describe("Issue key (e.g., PROJ-123)") },
  async ({ issueKey }) => {
    try {
      const issue = await getIssue(issueKey);
      return { content: [{ type: "text", text: JSON.stringify(issue, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jira_list_sprints",
  "List sprints for a project's board. Filter by state: active, closed, future.",
  {
    projectKey: z.string().describe("Project key (e.g., PROJ)"),
    state: z.enum(["active", "closed", "future"]).optional().describe("Filter sprint state (default: all)"),
  },
  async ({ projectKey, state }) => {
    try {
      const boards = await listBoards(projectKey);
      if (boards.length === 0) {
        return { content: [{ type: "text", text: JSON.stringify({ error: `No boards found for project ${projectKey}` }) }], isError: true };
      }
      const sprints = await listSprints(boards[0].id, state);
      return { content: [{ type: "text", text: JSON.stringify(sprints, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

server.tool(
  "jira_get_sprint_metrics",
  "Get sprint metrics: completion rates, estimate accuracy, breakdown by assignee/type/priority, carry-over count.",
  { sprintId: z.number().describe("Sprint ID") },
  async ({ sprintId }) => {
    try {
      const metrics = await getSprintMetrics(sprintId);
      return { content: [{ type: "text", text: JSON.stringify(metrics, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: JSON.stringify({ error: String(err) }) }], isError: true };
    }
  }
);

// ─── Write Operations ─────────────────────────────────────────────

server.tool(
  "jira_create_issue",
  "Create a Jira issue (Epic, Story, Task, Sub-task, or Bug)",
  {
    projectKey: z.string().describe("Project key (e.g., PROJ)"),
    issueType: z.enum(["Epic", "Story", "Task", "Sub-task", "Bug"]).describe("Issue type"),
    summary: z.string().describe("Issue title/summary"),
    description: z.string().optional().describe("Issue description (plain text, converted to ADF)"),
    priority: z.enum(["Highest", "High", "Medium", "Low", "Lowest"]).optional().describe("Priority"),
    assigneeId: z.string().optional().describe("Assignee account ID"),
    labels: z.array(z.string()).optional().describe("Labels"),
    components: z.array(z.string()).optional().describe("Component names"),
    epicKey: z.string().optional().describe("Parent epic key (for stories/tasks)"),
    parentKey: z.string().optional().describe("Parent issue key (for sub-tasks)"),
    sprintId: z.number().optional().describe("Sprint ID to add the issue to"),
    originalEstimateHours: z.number().optional().describe("Original estimate in hours"),
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
  "jira_create_issues_bulk",
  "Create multiple Jira issues at once. Input is a JSON array of issue objects.",
  {
    issues: z.string().describe("JSON array of issue objects with fields: projectKey, issueType, summary, description, priority, assigneeId, labels, components, epicKey, parentKey, sprintId, originalEstimateHours"),
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
  "jira_create_sprint",
  "Create a new sprint on a board",
  {
    projectKey: z.string().describe("Project key (used to find the board)"),
    name: z.string().describe("Sprint name"),
    startDate: z.string().optional().describe("Start date (ISO format)"),
    endDate: z.string().optional().describe("End date (ISO format)"),
    goal: z.string().optional().describe("Sprint goal"),
  },
  async ({ projectKey, name, startDate, endDate, goal }) => {
    try {
      const boards = await listBoards(projectKey);
      if (boards.length === 0) {
        return { content: [{ type: "text", text: JSON.stringify({ error: `No boards found for project ${projectKey}` }) }], isError: true };
      }
      const result = await createSprint({ boardId: boards[0].id, name, startDate, endDate, goal });
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
  "jira_create_link",
  "Create a link between two issues (Blocks, Duplicate, Relates)",
  {
    outwardIssueKey: z.string().describe("Issue key that blocks/relates (e.g., PROJ-1)"),
    inwardIssueKey: z.string().describe("Issue key that is blocked by/related to (e.g., PROJ-2)"),
    linkType: z.enum(["Blocks", "Duplicate", "Relates"]).describe("Link type"),
  },
  async (input) => {
    try {
      const result = await createIssueLink(input);
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
  "jira_transition_issue",
  "Transition an issue to a new status (e.g., 'In Progress', 'Done')",
  {
    issueKey: z.string().describe("Issue key (e.g., PROJ-123)"),
    transitionName: z.string().describe("Target status name (e.g., 'In Progress', 'In Review', 'Done')"),
  },
  async (input) => {
    try {
      const result = await transitionIssue(input);
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
  "jira_add_comment",
  "Add a comment to an issue (for meeting notes, decisions, status updates)",
  {
    issueKey: z.string().describe("Issue key (e.g., PROJ-123)"),
    body: z.string().describe("Comment text (plain text, converted to ADF)"),
  },
  async ({ issueKey, body }) => {
    try {
      const result = await addComment(issueKey, body);
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
  console.error("jira MCP server failed to start:", err);
  process.exit(1);
});
