/**
 * Jira read operations — queries for metrics, reporting, and meeting prep.
 */

import { jiraFetch, type JiraIssue, type JiraProject, type JiraSprint, type JiraBoard } from "./client.js";

// ─── Projects ─────────────────────────────────────────────────────

export async function listProjects(): Promise<JiraProject[]> {
  const res = await jiraFetch<{ values: JiraProject[] }>("/project/search?maxResults=50");
  return res.values;
}

// ─── Boards & Sprints ─────────────────────────────────────────────

export async function listBoards(projectKey: string): Promise<JiraBoard[]> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  const response = await fetch(
    `${baseUrl}/rest/agile/1.0/board?projectKeyOrId=${projectKey}`,
    { headers: { Accept: "application/json", Authorization: `Basic ${auth}` } }
  );

  if (!response.ok) throw new Error(`Jira Agile API error: ${response.status}`);
  const data = await response.json() as { values: JiraBoard[] };
  return data.values;
}

export async function listSprints(boardId: number, state?: string): Promise<JiraSprint[]> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  const stateParam = state ? `&state=${state}` : "";
  const response = await fetch(
    `${baseUrl}/rest/agile/1.0/board/${boardId}/sprint?maxResults=20${stateParam}`,
    { headers: { Accept: "application/json", Authorization: `Basic ${auth}` } }
  );

  if (!response.ok) throw new Error(`Jira Agile API error: ${response.status}`);
  const data = await response.json() as { values: JiraSprint[] };
  return data.values;
}

export async function getSprintIssues(sprintId: number): Promise<JiraIssue[]> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  const response = await fetch(
    `${baseUrl}/rest/agile/1.0/sprint/${sprintId}/issue?maxResults=200&fields=summary,status,issuetype,priority,assignee,labels,components,timeoriginalestimate,timespent,created,updated,resolutiondate,parent`,
    { headers: { Accept: "application/json", Authorization: `Basic ${auth}` } }
  );

  if (!response.ok) throw new Error(`Jira Agile API error: ${response.status}`);
  const data = await response.json() as { issues: JiraIssue[] };
  return data.issues;
}

// ─── JQL Search ───────────────────────────────────────────────────

export interface SearchParams {
  jql: string;
  fields?: string[];
  maxResults?: number;
}

export async function searchIssues(params: SearchParams): Promise<JiraIssue[]> {
  const { jql, fields, maxResults = 50 } = params;
  const fieldStr = fields?.join(",") ?? "summary,status,issuetype,priority,assignee,labels,components,sprint,timeoriginalestimate,timespent,created,updated,resolutiondate,parent";

  const res = await jiraFetch<{ issues: JiraIssue[] }>(
    `/search?jql=${encodeURIComponent(jql)}&fields=${fieldStr}&maxResults=${maxResults}`
  );
  return res.issues;
}

// ─── Single Issue ─────────────────────────────────────────────────

export async function getIssue(issueKey: string): Promise<JiraIssue> {
  return jiraFetch<JiraIssue>(`/issue/${issueKey}`);
}

// ─── Metrics Extraction ───────────────────────────────────────────

export interface SprintMetrics {
  sprintId: number;
  sprintName: string;
  state: string;
  startDate?: string;
  endDate?: string;
  totalIssues: number;
  completedIssues: number;
  inProgressIssues: number;
  todoIssues: number;
  totalEstimateHours: number;
  completedEstimateHours: number;
  timeSpentHours: number;
  byAssignee: Record<string, { total: number; completed: number; estimateHours: number; spentHours: number }>;
  byIssueType: Record<string, number>;
  byPriority: Record<string, number>;
  carryOver: number; // issues not completed
}

export async function getSprintMetrics(sprintId: number): Promise<SprintMetrics> {
  const { baseUrl, email, apiToken } = (await import("./client.js")).getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  // Get sprint details
  const sprintRes = await fetch(
    `${baseUrl}/rest/agile/1.0/sprint/${sprintId}`,
    { headers: { Accept: "application/json", Authorization: `Basic ${auth}` } }
  );
  if (!sprintRes.ok) throw new Error(`Sprint ${sprintId} not found`);
  const sprint = await sprintRes.json() as JiraSprint;

  // Get issues
  const issues = await getSprintIssues(sprintId);

  const completedIssues = issues.filter(
    (i) => i.fields.status.statusCategory.name === "Done"
  );
  const inProgressIssues = issues.filter(
    (i) => i.fields.status.statusCategory.name === "In Progress"
  );
  const todoIssues = issues.filter(
    (i) => i.fields.status.statusCategory.name === "To Do"
  );

  const byAssignee: SprintMetrics["byAssignee"] = {};
  const byIssueType: Record<string, number> = {};
  const byPriority: Record<string, number> = {};

  for (const issue of issues) {
    const assignee = issue.fields.assignee?.displayName ?? "Unassigned";
    if (!byAssignee[assignee]) {
      byAssignee[assignee] = { total: 0, completed: 0, estimateHours: 0, spentHours: 0 };
    }
    byAssignee[assignee].total++;
    byAssignee[assignee].estimateHours += (issue.fields.timeoriginalestimate ?? 0) / 3600;
    byAssignee[assignee].spentHours += (issue.fields.timespent ?? 0) / 3600;
    if (issue.fields.status.statusCategory.name === "Done") {
      byAssignee[assignee].completed++;
    }

    const issueType = issue.fields.issuetype.name;
    byIssueType[issueType] = (byIssueType[issueType] ?? 0) + 1;

    const priority = issue.fields.priority.name;
    byPriority[priority] = (byPriority[priority] ?? 0) + 1;
  }

  return {
    sprintId: sprint.id,
    sprintName: sprint.name,
    state: sprint.state,
    startDate: sprint.startDate,
    endDate: sprint.endDate,
    totalIssues: issues.length,
    completedIssues: completedIssues.length,
    inProgressIssues: inProgressIssues.length,
    todoIssues: todoIssues.length,
    totalEstimateHours: issues.reduce((sum, i) => sum + ((i.fields.timeoriginalestimate ?? 0) / 3600), 0),
    completedEstimateHours: completedIssues.reduce((sum, i) => sum + ((i.fields.timeoriginalestimate ?? 0) / 3600), 0),
    timeSpentHours: issues.reduce((sum, i) => sum + ((i.fields.timespent ?? 0) / 3600), 0),
    byAssignee,
    byIssueType,
    byPriority,
    carryOver: issues.length - completedIssues.length,
  };
}
