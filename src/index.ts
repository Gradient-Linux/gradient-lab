export interface EnvironmentStatus {
  clean: boolean;
  diffs: PackageDiff[];
  group: string;
  lastScanned: string;
}

export interface PackageDiff {
  name: string;
  baseline: string;
  current: string;
  tier: "safe" | "flag" | "leave";
}

export const REFRESH_INTERVAL_MS = 60_000;

export function summarizeEnvironment(status: EnvironmentStatus): string {
  if (status.clean) {
    return "Clean";
  }

  return `${status.diffs.length} package diff${status.diffs.length === 1 ? "" : "s"}`;
}

