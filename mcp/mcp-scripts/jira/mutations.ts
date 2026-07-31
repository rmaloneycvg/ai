/**
 * Jira write operations — create issues, epics, sprints, and link issues.
 */

import { jiraFetch, type JiraIssue } from "./client.js";

// ─── Issue Creation ───────────────────────────────────────────────

export interface CreateIssueInput {
  projectKey: string;
  issueType: string; // "Epic", "Story", "Task", "Sub-task", "Bug"
  summary: string;
  description?: string; // Plain text (converted to ADF)
  priority?: string; // "Highest", "High", "Medium", "Low", "Lowest"
  assigneeId?: string;
  labels?: string[];
  components?: string[];
  epicKey?: string; // parent epic issue key
  parentKey?: string; // parent issue key (for sub-tasks)
  sprintId?: number;
  originalEstimateHours?: number;
  customFields?: Record<string, unknown>;
}

export interface CreateIssueResult {
  success: boolean;
  issue?: { id: string; key: string; self: string };
  error?: string;
}

function toAdf(text: string): unknown {
  return {
    version: 1,
    type: "doc",
    content: text.split("\n\n").map((paragraph) => ({
      type: "paragraph",
      content: [{ type: "text", text: paragraph }],
    })),
  };
}

export async function createIssue(input: CreateIssueInput): Promise<CreateIssueResult> {
  const fields: Record<string, unknown> = {
    project: { key: input.projectKey },
    issuetype: { name: input.issueType },
    summary: input.summary,
  };

  if (input.description) fields.description = toAdf(input.description);
  if (input.priority) fields.priority = { name: input.priority };
  if (input.assigneeId) fields.assignee = { accountId: input.assigneeId };
  if (input.labels?.length) fields.labels = input.labels;
  if (input.components?.length) fields.components = input.components.map((name) => ({ name }));
  if (input.parentKey) fields.parent = { key: input.parentKey };
  if (input.epicKey && input.issueType !== "Epic") fields.parent = { key: input.epicKey };
  if (input.originalEstimateHours) fields.timeoriginalestimate = input.originalEstimateHours * 3600;
  if (input.customFields) Object.assign(fields, input.customFields);

  try {
    const result = await jiraFetch<{ id: string; key: string; self: string }>("/issue", {
      method: "POST",
      body: { fields },
    });

    // Move to sprint if specified (requires separate agile API call)
    if (input.sprintId && result.id) {
      await moveToSprint(result.id, input.sprintId);
    }

    return { success: true, issue: result };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export interface BulkCreateResult {
  created: Array<{ key: string; summary: string }>;
  errors: Array<{ summary: string; error: string }>;
}

export async function createIssuesBulk(issues: CreateIssueInput[]): Promise<BulkCreateResult> {
  const created: BulkCreateResult["created"] = [];
  const errors: BulkCreateResult["errors"] = [];

  for (const input of issues) {
    const result = await createIssue(input);
    if (result.success && result.issue) {
      created.push({ key: result.issue.key, summary: input.summary });
    } else {
      errors.push({ summary: input.summary, error: result.error ?? "Unknown error" });
    }
  }

  return { created, errors };
}

// ─── Sprint Management ────────────────────────────────────────────

async function moveToSprint(issueId: string, sprintId: number): Promise<void> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  const response = await fetch(
    `${baseUrl}/rest/agile/1.0/sprint/${sprintId}/issue`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Basic ${auth}`,
      },
      body: JSON.stringify({ issues: [issueId] }),
    }
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to move issue to sprint: ${text}`);
  }
}

export interface CreateSprintInput {
  boardId: number;
  name: string;
  startDate?: string; // ISO format
  endDate?: string; // ISO format
  goal?: string;
}

export interface CreateSprintResult {
  success: boolean;
  sprint?: { id: number; name: string; state: string };
  error?: string;
}

export async function createSprint(input: CreateSprintInput): Promise<CreateSprintResult> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  try {
    const response = await fetch(
      `${baseUrl}/rest/agile/1.0/sprint`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Basic ${auth}`,
        },
        body: JSON.stringify({
          name: input.name,
          originBoardId: input.boardId,
          startDate: input.startDate,
          endDate: input.endDate,
          goal: input.goal,
        }),
      }
    );

    if (!response.ok) {
      const text = await response.text();
      return { success: false, error: `Jira API error: ${text}` };
    }

    const sprint = await response.json() as { id: number; name: string; state: string };
    return { success: true, sprint };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// ─── Issue Links (Dependencies) ───────────────────────────────────

export interface CreateLinkInput {
  inwardIssueKey: string; // "is blocked by"
  outwardIssueKey: string; // "blocks"
  linkType: string; // "Blocks", "Duplicate", "Relates"
}

export async function createIssueLink(input: CreateLinkInput): Promise<{ success: boolean; error?: string }> {
  try {
    await jiraFetch("/issueLink", {
      method: "POST",
      body: {
        type: { name: input.linkType },
        inwardIssue: { key: input.inwardIssueKey },
        outwardIssue: { key: input.outwardIssueKey },
      },
    });
    return { success: true };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// ─── Transitions ──────────────────────────────────────────────────

export interface TransitionInput {
  issueKey: string;
  transitionName: string;
}

export async function transitionIssue(input: TransitionInput): Promise<{ success: boolean; error?: string }> {
  try {
    // Get available transitions
    const transitions = await jiraFetch<{ transitions: Array<{ id: string; name: string }> }>(
      `/issue/${input.issueKey}/transitions`
    );

    const transition = transitions.transitions.find(
      (t) => t.name.toLowerCase() === input.transitionName.toLowerCase()
    );

    if (!transition) {
      const available = transitions.transitions.map((t) => t.name).join(", ");
      return { success: false, error: `Transition "${input.transitionName}" not found. Available: ${available}` };
    }

    await jiraFetch(`/issue/${input.issueKey}/transitions`, {
      method: "POST",
      body: { transition: { id: transition.id } },
    });

    return { success: true };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// ─── Add Comment ──────────────────────────────────────────────────

export async function addComment(issueKey: string, body: string): Promise<{ success: boolean; error?: string }> {
  try {
    await jiraFetch(`/issue/${issueKey}/comment`, {
      method: "POST",
      body: { body: toAdf(body) },
    });
    return { success: true };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}
