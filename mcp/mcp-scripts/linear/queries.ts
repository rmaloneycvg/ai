/**
 * Linear read operations — queries for metrics, reporting, and meeting prep.
 */

import { graphql, type LinearIssue, type LinearProject, type LinearCycle, type LinearTeam } from "./client.js";

// ─── Teams ────────────────────────────────────────────────────────

export async function listTeams(): Promise<LinearTeam[]> {
  const res = await graphql<{ teams: { nodes: LinearTeam[] } }>(`
    query { teams { nodes { id name key } } }
  `);
  return res.data?.teams.nodes ?? [];
}

// ─── Issues ───────────────────────────────────────────────────────

const ISSUE_FIELDS = `
  id identifier title description
  state { name }
  priority estimate
  assignee { name email }
  labels { nodes { name } }
  project { name }
  cycle { number name }
  createdAt updatedAt completedAt
`;

export interface ListIssuesParams {
  teamId: string;
  filter?: {
    state?: string;
    assigneeId?: string;
    labelName?: string;
    projectId?: string;
    cycleId?: string;
    priority?: number;
  };
  first?: number;
}

export async function listIssues(params: ListIssuesParams): Promise<LinearIssue[]> {
  const { teamId, filter, first = 50 } = params;

  const filterParts: string[] = [`team: { id: { eq: "${teamId}" } }`];
  if (filter?.state) filterParts.push(`state: { name: { eq: "${filter.state}" } }`);
  if (filter?.assigneeId) filterParts.push(`assignee: { id: { eq: "${filter.assigneeId}" } }`);
  if (filter?.labelName) filterParts.push(`labels: { name: { eq: "${filter.labelName}" } }`);
  if (filter?.projectId) filterParts.push(`project: { id: { eq: "${filter.projectId}" } }`);
  if (filter?.cycleId) filterParts.push(`cycle: { id: { eq: "${filter.cycleId}" } }`);
  if (filter?.priority !== undefined) filterParts.push(`priority: { eq: ${filter.priority} }`);

  const filterStr = filterParts.join(", ");

  const res = await graphql<{ issues: { nodes: LinearIssue[] } }>(`
    query($first: Int!) {
      issues(filter: { ${filterStr} }, first: $first, orderBy: updatedAt) {
        nodes { ${ISSUE_FIELDS} }
      }
    }
  `, { first });

  return res.data?.issues.nodes ?? [];
}

export async function getIssue(issueId: string): Promise<LinearIssue | null> {
  const res = await graphql<{ issue: LinearIssue }>(`
    query($id: String!) {
      issue(id: $id) { ${ISSUE_FIELDS} }
    }
  `, { id: issueId });
  return res.data?.issue ?? null;
}

// ─── Projects (Epics) ─────────────────────────────────────────────

export async function listProjects(teamId: string): Promise<LinearProject[]> {
  const res = await graphql<{ team: { projects: { nodes: LinearProject[] } } }>(`
    query($teamId: String!) {
      team(id: $teamId) {
        projects(first: 50) {
          nodes {
            id name description state progress startDate targetDate
            issues(first: 100) {
              nodes { ${ISSUE_FIELDS} }
            }
          }
        }
      }
    }
  `, { teamId });
  return res.data?.team.projects.nodes ?? [];
}

// ─── Cycles (Sprints) ─────────────────────────────────────────────

export async function listCycles(teamId: string, includeCompleted = false): Promise<LinearCycle[]> {
  const filter = includeCompleted ? "" : `, filter: { isActive: { eq: true } }`;
  const res = await graphql<{ team: { cycles: { nodes: LinearCycle[] } } }>(`
    query($teamId: String!) {
      team(id: $teamId) {
        cycles(first: 20, orderBy: createdAt${filter}) {
          nodes {
            id number name startsAt endsAt progress
            issues(first: 200) {
              nodes { ${ISSUE_FIELDS} }
            }
          }
        }
      }
    }
  `, { teamId });
  return res.data?.team.cycles.nodes ?? [];
}

export async function getActiveCycle(teamId: string): Promise<LinearCycle | null> {
  const cycles = await listCycles(teamId, false);
  return cycles[0] ?? null;
}

// ─── Metrics Extraction ───────────────────────────────────────────

export interface SprintMetrics {
  cycleNumber: number;
  cycleName?: string;
  startDate: string;
  endDate: string;
  progress: number;
  totalIssues: number;
  completedIssues: number;
  inProgressIssues: number;
  backlogIssues: number;
  totalEstimate: number;
  completedEstimate: number;
  byAssignee: Record<string, { total: number; completed: number; estimate: number; completedEstimate: number }>;
  byLabel: Record<string, number>;
  byPriority: Record<number, number>;
}

export async function getCycleMetrics(teamId: string, cycleId?: string): Promise<SprintMetrics | null> {
  let cycle: LinearCycle | null;

  if (cycleId) {
    const cycles = await listCycles(teamId, true);
    cycle = cycles.find((c) => c.id === cycleId) ?? null;
  } else {
    cycle = await getActiveCycle(teamId);
  }

  if (!cycle) return null;

  const issues = cycle.issues.nodes;
  const completedIssues = issues.filter((i) => i.completedAt);
  const inProgressIssues = issues.filter((i) => !i.completedAt && i.state.name !== "Backlog" && i.state.name !== "Todo");
  const backlogIssues = issues.filter((i) => i.state.name === "Backlog" || i.state.name === "Todo");

  const byAssignee: SprintMetrics["byAssignee"] = {};
  const byLabel: Record<string, number> = {};
  const byPriority: Record<number, number> = {};

  for (const issue of issues) {
    const assigneeName = issue.assignee?.name ?? "Unassigned";
    if (!byAssignee[assigneeName]) {
      byAssignee[assigneeName] = { total: 0, completed: 0, estimate: 0, completedEstimate: 0 };
    }
    byAssignee[assigneeName].total++;
    byAssignee[assigneeName].estimate += issue.estimate ?? 0;
    if (issue.completedAt) {
      byAssignee[assigneeName].completed++;
      byAssignee[assigneeName].completedEstimate += issue.estimate ?? 0;
    }

    for (const label of issue.labels.nodes) {
      byLabel[label.name] = (byLabel[label.name] ?? 0) + 1;
    }

    byPriority[issue.priority] = (byPriority[issue.priority] ?? 0) + 1;
  }

  return {
    cycleNumber: cycle.number,
    cycleName: cycle.name ?? undefined,
    startDate: cycle.startsAt,
    endDate: cycle.endsAt,
    progress: cycle.progress,
    totalIssues: issues.length,
    completedIssues: completedIssues.length,
    inProgressIssues: inProgressIssues.length,
    backlogIssues: backlogIssues.length,
    totalEstimate: issues.reduce((sum, i) => sum + (i.estimate ?? 0), 0),
    completedEstimate: completedIssues.reduce((sum, i) => sum + (i.estimate ?? 0), 0),
    byAssignee,
    byLabel,
    byPriority,
  };
}
