/**
 * Grafana HTTP API client.
 *
 * Requires environment variables:
 *   GRAFANA_URL — e.g., http://localhost:3000
 *   GRAFANA_API_KEY — Service account token or API key
 *   GRAFANA_ORG_ID — (optional) Organization ID for multi-org setups
 */

export interface GrafanaConfig {
  baseUrl: string;
  apiKey: string;
  orgId?: string;
}

export function getConfig(): GrafanaConfig {
  const baseUrl = process.env.GRAFANA_URL;
  const apiKey = process.env.GRAFANA_API_KEY;

  if (!baseUrl) throw new Error("GRAFANA_URL environment variable is required");
  if (!apiKey) throw new Error("GRAFANA_API_KEY environment variable is required");

  return {
    baseUrl: baseUrl.replace(/\/$/, ""),
    apiKey,
    orgId: process.env.GRAFANA_ORG_ID,
  };
}

// ─── Dashboard Types ────────────────────────────────────────────

export interface GrafanaDashboard {
  id: number;
  uid: string;
  title: string;
  url: string;
  type: string;
  tags: string[];
  isStarred: boolean;
  uri: string;
}

export interface GrafanaDashboardDetail {
  meta: {
    type: string;
    canSave: boolean;
    canEdit: boolean;
    canStar: boolean;
    slug: string;
    url: string;
    expires: string;
    created: string;
    updated: string;
    updatedBy: string;
    createdBy: string;
    version: number;
  };
  dashboard: {
    id: number;
    uid: string;
    title: string;
    tags: string[];
    templating?: { list: GrafanaVariable[] };
    panels?: GrafanaPanel[];
    annotations?: { list: GrafanaAnnotationDef[] };
    version: number;
    [key: string]: unknown;
  };
}

export interface GrafanaVariable {
  name: string;
  type: string;
  label: string;
  query: string;
  current: { text: string; value: string };
  options: Array<{ text: string; value: string }>;
}

export interface GrafanaPanel {
  id: number;
  title: string;
  type: string;
  targets?: GrafanaPanelTarget[];
  fieldConfig?: unknown;
  options?: unknown;
}

export interface GrafanaPanelTarget {
  expr?: string; // PromQL
  refId: string;
  datasource?: { type: string; uid: string };
}

export interface GrafanaAnnotationDef {
  name: string;
  datasource: { type: string; uid: string };
  enable: boolean;
  iconColor: string;
}

// ─── Annotation Types ───────────────────────────────────────────

export interface GrafanaAnnotation {
  id: number;
  dashboardId: number;
  panelId: number;
  time: number;
  timeEnd: number;
  text: string;
  tags: string[];
  created: number;
  updated: number;
}

export interface CreateAnnotationRequest {
  dashboardUID?: string;
  panelId?: number;
  time?: number; // epoch ms
  timeEnd?: number;
  text: string;
  tags: string[];
}

// ─── Datasource Types ───────────────────────────────────────────

export interface GrafanaDatasource {
  id: number;
  uid: string;
  name: string;
  type: string;
  url: string;
  isDefault: boolean;
}

// ─── Dashboard Version Types ────────────────────────────────────

export interface GrafanaDashboardVersion {
  id: number;
  dashboardId: number;
  version: number;
  createdBy: string;
  created: string;
  message: string;
}

export async function grafanaFetch<T = unknown>(
  path: string,
  options: { method?: string; body?: unknown; params?: Record<string, string> } = {},
  config?: GrafanaConfig
): Promise<T> {
  const { baseUrl, apiKey, orgId } = config ?? getConfig();

  const url = new URL(`${baseUrl}/api${path}`);
  if (options.params) {
    for (const [key, value] of Object.entries(options.params)) {
      url.searchParams.set(key, value);
    }
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    Authorization: `Bearer ${apiKey}`,
  };
  if (orgId) {
    headers["X-Grafana-Org-Id"] = orgId;
  }

  const response = await fetch(url.toString(), {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Grafana API error ${response.status}: ${errorBody}`);
  }

  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}
