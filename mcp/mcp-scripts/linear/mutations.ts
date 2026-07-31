/**
 * Linear write operations — create issues, projects, cycles, and documents.
 */

import { graphql, type LinearIssue, type LinearProject } from "./client.js";

// ─── Issue Creation ───────────────────────────────────────────────

export interface CreateIssueInput {
  teamId: string;
  title: string;
  description?: string;
  priority?: number; // 0=none, 1=urgent, 2=high, 3=medium, 4=low
  estimate?: number;
  assigneeId?: string;
  labelIds?: string[];
  projectId?: string;
  cycleId?: string;
  parentId?: string; // for sub-issues
}

export interface CreateIssueResult {
  success: boolean;
  issue?: { id: string; identifier: string; title: string; url: string };
  error?: string;
}

export async function createIssue(input: CreateIssueInput): Promise<CreateIssueResult> {
  const res = await graphql<{ issueCreate: { success: boolean; issue: { id: string; identifier: string; title: string; url: string } } }>(`
    mutation($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier title url }
      }
    }
  `, { input });

  if (res.errors?.length) {
    return { success: false, error: res.errors.map((e) => e.message).join("; ") };
  }

  const result = res.data?.issueCreate;
  if (!result?.success) return { success: false, error: "Issue creation failed" };
  return { success: true, issue: result.issue };
}

export interface BulkCreateResult {
  created: Array<{ identifier: string; title: string; url: string }>;
  errors: Array<{ title: string; error: string }>;
}

export async function createIssuesBulk(issues: CreateIssueInput[]): Promise<BulkCreateResult> {
  const created: BulkCreateResult["created"] = [];
  const errors: BulkCreateResult["errors"] = [];

  for (const input of issues) {
    const result = await createIssue(input);
    if (result.success && result.issue) {
      created.push(result.issue);
    } else {
      errors.push({ title: input.title, error: result.error ?? "Unknown error" });
    }
  }

  return { created, errors };
}

// ─── Issue Relations (Dependencies) ──────────────────────────────

export interface CreateRelationInput {
  issueId: string;
  relatedIssueId: string;
  type: "blocks" | "duplicate" | "related";
}

export async function createIssueRelation(input: CreateRelationInput): Promise<{ success: boolean; error?: string }> {
  const res = await graphql<{ issueRelationCreate: { success: boolean } }>(`
    mutation($input: IssueRelationCreateInput!) {
      issueRelationCreate(input: $input) { success }
    }
  `, { input });

  if (res.errors?.length) {
    return { success: false, error: res.errors.map((e) => e.message).join("; ") };
  }
  return { success: res.data?.issueRelationCreate.success ?? false };
}

// ─── Project Creation (Epics) ─────────────────────────────────────

export interface CreateProjectInput {
  teamIds: string[];
  name: string;
  description?: string;
  targetDate?: string; // ISO date
  startDate?: string; // ISO date
}

export interface CreateProjectResult {
  success: boolean;
  project?: { id: string; name: string; url: string };
  error?: string;
}

export async function createProject(input: CreateProjectInput): Promise<CreateProjectResult> {
  const res = await graphql<{ projectCreate: { success: boolean; project: { id: string; name: string; url: string } } }>(`
    mutation($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project { id name url }
      }
    }
  `, { input });

  if (res.errors?.length) {
    return { success: false, error: res.errors.map((e) => e.message).join("; ") };
  }

  const result = res.data?.projectCreate;
  if (!result?.success) return { success: false, error: "Project creation failed" };
  return { success: true, project: result.project };
}

// ─── Cycle Creation (Sprints) ─────────────────────────────────────

export interface CreateCycleInput {
  teamId: string;
  name?: string;
  startsAt: string; // ISO datetime
  endsAt: string; // ISO datetime
}

export interface CreateCycleResult {
  success: boolean;
  cycle?: { id: string; number: number; startsAt: string; endsAt: string };
  error?: string;
}

export async function createCycle(input: CreateCycleInput): Promise<CreateCycleResult> {
  const res = await graphql<{ cycleCreate: { success: boolean; cycle: { id: string; number: number; startsAt: string; endsAt: string } } }>(`
    mutation($input: CycleCreateInput!) {
      cycleCreate(input: $input) {
        success
        cycle { id number startsAt endsAt }
      }
    }
  `, { input });

  if (res.errors?.length) {
    return { success: false, error: res.errors.map((e) => e.message).join("; ") };
  }

  const result = res.data?.cycleCreate;
  if (!result?.success) return { success: false, error: "Cycle creation failed" };
  return { success: true, cycle: result.cycle };
}

// ─── Document Creation ────────────────────────────────────────────

export interface CreateDocumentInput {
  title: string;
  content: string; // Markdown
  projectId?: string;
}

export interface CreateDocumentResult {
  success: boolean;
  document?: { id: string; title: string; url: string };
  error?: string;
}

export async function createDocument(input: CreateDocumentInput): Promise<CreateDocumentResult> {
  const res = await graphql<{ documentCreate: { success: boolean; document: { id: string; title: string; url: string } } }>(`
    mutation($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url }
      }
    }
  `, { input });

  if (res.errors?.length) {
    return { success: false, error: res.errors.map((e) => e.message).join("; ") };
  }

  const result = res.data?.documentCreate;
  if (!result?.success) return { success: false, error: "Document creation failed" };
  return { success: true, document: result.document };
}

// ─── Label Lookup / Creation ──────────────────────────────────────

export interface LinearLabel {
  id: string;
  name: string;
}

export async function listLabels(teamId: string): Promise<LinearLabel[]> {
  const res = await graphql<{ team: { labels: { nodes: LinearLabel[] } } }>(`
    query($teamId: String!) {
      team(id: $teamId) { labels(first: 100) { nodes { id name } } }
    }
  `, { teamId });
  return res.data?.team.labels.nodes ?? [];
}

export async function findOrCreateLabel(teamId: string, name: string): Promise<string> {
  const labels = await listLabels(teamId);
  const existing = labels.find((l) => l.name.toLowerCase() === name.toLowerCase());
  if (existing) return existing.id;

  const res = await graphql<{ issueLabelCreate: { success: boolean; issueLabel: { id: string } } }>(`
    mutation($input: IssueLabelCreateInput!) {
      issueLabelCreate(input: $input) {
        success
        issueLabel { id }
      }
    }
  `, { input: { teamId, name } });

  if (res.errors?.length || !res.data?.issueLabelCreate.success) {
    throw new Error(`Failed to create label "${name}": ${res.errors?.[0]?.message ?? "unknown"}`);
  }

  return res.data.issueLabelCreate.issueLabel.id;
}
