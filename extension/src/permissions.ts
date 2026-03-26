export type GradientRole =
  | "gradient-viewer"
  | "gradient-developer"
  | "gradient-operator"
  | "gradient-admin";

export interface GradientAction {
  id: string;
  label: string;
  minimumRole: GradientRole;
  operatorOnly: boolean;
}

const ROLE_ORDER: Record<GradientRole, number> = {
  "gradient-viewer": 0,
  "gradient-developer": 1,
  "gradient-operator": 2,
  "gradient-admin": 3
};

export const ACTION_CATALOG: GradientAction[] = [
  {
    id: "refresh-status",
    label: "Refresh status",
    minimumRole: "gradient-developer",
    operatorOnly: false
  },
  {
    id: "sync-baseline",
    label: "Sync baseline",
    minimumRole: "gradient-developer",
    operatorOnly: false
  },
  {
    id: "reconcile-quota",
    label: "Reconcile cgroup quota",
    minimumRole: "gradient-operator",
    operatorOnly: true
  },
  {
    id: "rebuild-scope",
    label: "Rebuild notebook scope",
    minimumRole: "gradient-operator",
    operatorOnly: true
  },
  {
    id: "provision-user",
    label: "Provision user",
    minimumRole: "gradient-admin",
    operatorOnly: true
  }
];

export function normalizeRole(role: string | undefined | null): GradientRole {
  if (role === "gradient-viewer" || role === "gradient-developer" || role === "gradient-operator" || role === "gradient-admin") {
    return role;
  }
  return "gradient-viewer";
}

export function visibleActions(role: string | undefined | null, catalog: GradientAction[] = ACTION_CATALOG): GradientAction[] {
  const normalized = normalizeRole(role);
  const currentLevel = ROLE_ORDER[normalized];
  return catalog.filter((action) => ROLE_ORDER[action.minimumRole] <= currentLevel);
}
