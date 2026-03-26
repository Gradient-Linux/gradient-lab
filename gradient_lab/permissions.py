"""Role and action helpers shared by the gradient-lab runtime."""

from __future__ import annotations

from typing import Any

ROLE_ORDER = {
    "gradient-viewer": 0,
    "gradient-developer": 1,
    "gradient-operator": 2,
    "gradient-admin": 3,
}

ACTION_CATALOG: list[dict[str, Any]] = [
    {
        "id": "refresh-status",
        "label": "Refresh status",
        "minimum_role": "gradient-developer",
        "operator_only": False,
    },
    {
        "id": "sync-baseline",
        "label": "Sync baseline",
        "minimum_role": "gradient-developer",
        "operator_only": False,
    },
    {
        "id": "reconcile-quota",
        "label": "Reconcile cgroup quota",
        "minimum_role": "gradient-operator",
        "operator_only": True,
    },
    {
        "id": "rebuild-scope",
        "label": "Rebuild notebook scope",
        "minimum_role": "gradient-operator",
        "operator_only": True,
    },
    {
        "id": "provision-user",
        "label": "Provision user",
        "minimum_role": "gradient-admin",
        "operator_only": True,
    },
]


def normalize_role(role: str | None) -> str:
    """normalize_role returns a known Gradient role or viewer fallback."""
    if role in ROLE_ORDER:
        return role
    return "gradient-viewer"


def role_level(role: str | None) -> int:
    """role_level returns the numeric precedence for a role string."""
    return ROLE_ORDER[normalize_role(role)]


def visible_actions(role: str | None) -> list[dict[str, Any]]:
    """visible_actions filters operator-only actions out for lower roles."""
    current_level = role_level(role)
    actions: list[dict[str, Any]] = []
    for action in ACTION_CATALOG:
        if current_level < role_level(action["minimum_role"]):
            continue
        actions.append(dict(action))
    return actions
