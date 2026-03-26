import { PageConfig } from "@jupyterlab/coreutils";

import { ACTION_CATALOG, type GradientAction, type GradientRole, normalizeRole, visibleActions } from "./permissions";

export const REFRESH_INTERVAL_MS = 60_000;

export interface ResolverStatus {
  available?: boolean;
  error?: string;
  message?: string;
  [key: string]: unknown;
}

export interface QuotaStatus {
  group: string;
  role: GradientRole;
  cpu_cores?: number;
  memory_gb?: number;
  gpu_count?: number;
  extra?: Record<string, unknown>;
}

export interface GradientLabStatus {
  service: string;
  refreshed_at: string;
  group: string;
  role: GradientRole;
  quota: QuotaStatus;
  resolver: ResolverStatus;
  actions: GradientAction[];
}

function joinBaseUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

function coerceNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

export function statusUrl(): string {
  return joinBaseUrl(PageConfig.getBaseUrl(), "gradient-lab/status");
}

export function visibleActionsForRole(role: string | undefined | null): GradientAction[] {
  return visibleActions(role, ACTION_CATALOG);
}

export async function fetchGradientLabStatus(fetchImpl: typeof fetch = fetch): Promise<GradientLabStatus> {
  const response = await fetchImpl(statusUrl(), {
    credentials: "same-origin"
  });
  if (!response.ok) {
    throw new Error(`gradient-lab status request failed with ${response.status}`);
  }
  const data = (await response.json()) as Partial<GradientLabStatus>;
  const role = normalizeRole(data.role ?? undefined);
  const quota = {
    group: typeof data.quota?.group === "string" ? data.quota.group : data.group ?? "",
    role,
    cpu_cores: coerceNumber(data.quota?.cpu_cores),
    memory_gb: coerceNumber(data.quota?.memory_gb),
    gpu_count: coerceNumber(data.quota?.gpu_count),
    extra: data.quota?.extra && typeof data.quota.extra === "object" ? data.quota.extra : undefined
  };

  return {
    service: typeof data.service === "string" ? data.service : "Gradient Lab",
    refreshed_at: typeof data.refreshed_at === "string" ? data.refreshed_at : new Date().toISOString(),
    group: typeof data.group === "string" ? data.group : quota.group,
    role,
    quota,
    resolver: data.resolver && typeof data.resolver === "object" ? data.resolver : {},
    actions: Array.isArray(data.actions) ? data.actions : visibleActionsForRole(role)
  };
}
