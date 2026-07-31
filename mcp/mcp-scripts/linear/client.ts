/**
 * Linear GraphQL API client.
 *
 * Requires LINEAR_API_KEY environment variable.
 * API docs: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
 */

const LINEAR_API_URL = "https://api.linear.app/graphql";

export interface LinearConfig {
  apiKey: string;
}

export interface LinearResponse<T = unknown> {
  data?: T;
  errors?: Array<{ message: string; extensions?: Record<string, unknown> }>;
}

export function getConfig(): LinearConfig {
  const apiKey = process.env.LINEAR_API_KEY;
  if (!apiKey) {
    throw new Error("LINEAR_API_KEY environment variable is required");
  }
  return { apiKey };
}

export async function graphql<T = unknown>(
  query: string,
  variables?: Record<string, unknown>,
  config?: LinearConfig
): Promise<LinearResponse<T>> {
  const { apiKey } = config ?? getConfig();

  const response = await fetch(LINEAR_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: apiKey,
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!response.ok) {
    throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<LinearResponse<T>>;
}

// ─── Common Types ─────────────────────────────────────────────────

export interface LinearIssue {
  id: string;
  identifier: string;
  title: string;
  description?: string;
  state: { name: string };
  priority: number;
  estimate?: number;
  assignee?: { name: string; email: string };
  labels: { nodes: Array<{ name: string }> };
  project?: { name: string };
  cycle?: { number: number; name?: string };
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface LinearProject {
  id: string;
  name: string;
  description?: string;
  state: string;
  progress: number;
  startDate?: string;
  targetDate?: string;
  issues: { nodes: LinearIssue[] };
}

export interface LinearCycle {
  id: string;
  number: number;
  name?: string;
  startsAt: string;
  endsAt: string;
  progress: number;
  issues: { nodes: LinearIssue[] };
}

export interface LinearTeam {
  id: string;
  name: string;
  key: string;
}
