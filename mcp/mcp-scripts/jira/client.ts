/**
 * Jira REST API v3 client (Cloud).
 *
 * Requires environment variables:
 *   JIRA_BASE_URL — e.g., https://yourcompany.atlassian.net
 *   JIRA_EMAIL — Atlassian account email
 *   JIRA_API_TOKEN — API token from https://id.atlassian.com/manage-profile/security/api-tokens
 */

export interface JiraConfig {
  baseUrl: string;
  email: string;
  apiToken: string;
}

export function getConfig(): JiraConfig {
  const baseUrl = process.env.JIRA_BASE_URL;
  const email = process.env.JIRA_EMAIL;
  const apiToken = process.env.JIRA_API_TOKEN;

  if (!baseUrl) throw new Error("JIRA_BASE_URL environment variable is required");
  if (!email) throw new Error("JIRA_EMAIL environment variable is required");
  if (!apiToken) throw new Error("JIRA_API_TOKEN environment variable is required");

  return { baseUrl: baseUrl.replace(/\/$/, ""), email, apiToken };
}

export async function jiraFetch<T = unknown>(
  path: string,
  options: { method?: string; body?: unknown } = {},
  config?: JiraConfig
): Promise<T> {
  const { baseUrl, email, apiToken } = config ?? getConfig();
  const auth = Buffer.from(`${email}:${apiToken}`).toString("base64");

  const response = await fetch(`${baseUrl}/rest/api/3${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Basic ${auth}`,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Jira API error ${response.status}: ${errorBody}`);
  }

  // 204 No Content
  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

// ─── Common Types ─────────────────────────────────────────────────

export interface JiraIssue {
  id: string;
  key: string;
  self: string;
  fields: {
    summary: string;
    description?: unknown; // ADF format
    status: { name: string; statusCategory: { name: string } };
    issuetype: { name: string };
    priority: { name: string };
    assignee?: { displayName: string; emailAddress: string };
    reporter?: { displayName: string };
    labels: string[];
    components: Array<{ name: string }>;
    sprint?: { id: number; name: string; state: string };
    parent?: { key: string; fields: { summary: string } };
    created: string;
    updated: string;
    resolutiondate?: string;
    timeoriginalestimate?: number; // seconds
    timespent?: number; // seconds
    [key: string]: unknown;
  };
}

export interface JiraProject {
  id: string;
  key: string;
  name: string;
  projectTypeKey: string;
}

export interface JiraSprint {
  id: number;
  name: string;
  state: string; // "active", "closed", "future"
  startDate?: string;
  endDate?: string;
  completeDate?: string;
  goal?: string;
}

export interface JiraBoard {
  id: number;
  name: string;
  type: string; // "scrum" or "kanban"
  location: { projectKey: string };
}
