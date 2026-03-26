"""Custom JupyterHub spawner hooks for Gradient Linux quotas."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping

from .config import notebook_dir_for

try:
    from jupyterhub.spawner import LocalProcessSpawner
except Exception:  # pragma: no cover - fallback for bootstrap tests

    class LocalProcessSpawner:  # type: ignore[no-redef]
        """LocalProcessSpawner fallback used when JupyterHub is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.user = SimpleNamespace(name="")

        def user_env(self, env: Mapping[str, str]) -> dict[str, str]:
            return dict(env)

        def make_preexec_fn(self, name: str) -> Callable[[], None]:
            return lambda: None


def _username_for(spawner: Any) -> str:
    user = getattr(spawner, "user", None)
    return getattr(user, "name", "") or ""


def _parse_payload(stdout: str) -> dict[str, Any]:
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _group_from_payload(payload: Mapping[str, Any]) -> str | None:
    group = payload.get("group")
    if isinstance(group, str) and group:
        return group
    team = payload.get("team")
    if isinstance(team, Mapping):
        nested_group = team.get("group")
        if isinstance(nested_group, str) and nested_group:
            return nested_group
    return None


def _quota_from_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    quota = payload.get("quota")
    if isinstance(quota, dict):
        return quota
    limits = payload.get("limits")
    if isinstance(limits, dict):
        return limits
    extracted = {
        key: value
        for key, value in payload.items()
        if key in {"cpu_cores", "memory_gb", "gpu_fraction", "gpu_count", "disk_gb"}
        and value is not None
    }
    return extracted or None


def _role_from_payload(payload: Mapping[str, Any]) -> str | None:
    role = payload.get("role")
    return role if isinstance(role, str) and role else None


def _status_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    status: dict[str, Any] = {}
    group = _group_from_payload(payload)
    if group:
        status["group"] = group
    role = _role_from_payload(payload)
    if role:
        status["role"] = role
    quota = _quota_from_payload(payload)
    if quota:
        status["quota"] = quota
    return status


def fetch_team_status(username: str, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    """fetch_team_status resolves group and quota metadata for a user via concave."""
    result = runner(
        ["concave", "team", "status", "--user", username, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if getattr(result, "returncode", 1) != 0:
        return {}
    return _status_payload(_parse_payload(getattr(result, "stdout", "")))


def fetch_user_group(username: str, runner: Callable[..., Any] = subprocess.run) -> str | None:
    """fetch_user_group resolves the compute group for a user via concave."""
    return fetch_team_status(username, runner=runner).get("group")


def fetch_group_quota(group: str, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any] | None:
    """fetch_group_quota resolves the quota for a compute group via concave."""
    result = runner(
        ["concave", "team", "status", group, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if getattr(result, "returncode", 1) != 0:
        return None
    return _quota_from_payload(_parse_payload(getattr(result, "stdout", "")))


def build_gradient_env(
    base_env: Mapping[str, str],
    *,
    group: str | None = None,
    role: str | None = None,
    quota: Mapping[str, Any] | None = None,
    notebook_dir: str | None = None,
) -> dict[str, str]:
    """build_gradient_env merges Gradient Linux quota metadata into a session env."""
    env = dict(base_env)
    if group:
        env["GRADIENT_GROUP"] = group
        env["GRADIENT_CGROUP_SLICE"] = f"gradient-{group}.slice"
    if role:
        env["GRADIENT_ROLE"] = role
    if notebook_dir:
        env["GRADIENT_NOTEBOOK_DIR"] = notebook_dir
    if quota:
        for key, value in quota.items():
            if value is None:
                continue
            suffix = "".join(ch if ch.isalnum() else "_" for ch in str(key).upper()).strip("_")
            env[f"GRADIENT_QUOTA_{suffix}"] = str(value)
        cpu = quota.get("cpu_cores")
        memory = quota.get("memory_gb")
        if cpu is not None:
            env["GRADIENT_CPU_LIMIT"] = str(cpu)
        if memory is not None:
            env["GRADIENT_MEM_LIMIT"] = str(memory)
    return env


def _notebook_path_for(username: str) -> Path:
    return Path(notebook_dir_for(username))


def _ensure_notebook_dir(username: str) -> str:
    notebook_path = _notebook_path_for(username)
    notebook_path.mkdir(parents=True, exist_ok=True)
    return str(notebook_path)


def _best_effort_cgroup_scope(group: str, runner: Callable[..., Any]) -> None:
    command = [
        "systemd-run",
        "--scope",
        "--quiet",
        "--slice",
        f"gradient-{group}.slice",
        "true",
    ]
    runner(command, capture_output=True, text=True, check=False)


class GradientSpawner(LocalProcessSpawner):
    """GradientSpawner enforces compute-group metadata at notebook spawn time."""

    def __init__(self, *args: Any, runner: Callable[..., Any] = subprocess.run, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._runner = runner
        self._team_status_cache: dict[str, Any] | None = None

    def _team_status(self) -> dict[str, Any]:
        if self._team_status_cache is not None:
            return dict(self._team_status_cache)
        username = _username_for(self)
        if not username:
            return {}
        self._team_status_cache = fetch_team_status(username, runner=self._runner)
        return dict(self._team_status_cache)

    def user_env(self, env: Mapping[str, str]) -> dict[str, str]:
        """user_env adds Gradient Linux session metadata to the notebook environment."""
        base_env = super().user_env(env)
        username = _username_for(self)
        status = self._team_status()
        notebook_dir = _ensure_notebook_dir(username) if username else None
        return build_gradient_env(
            base_env,
            group=status.get("group"),
            role=status.get("role"),
            quota=status.get("quota"),
            notebook_dir=notebook_dir,
        )

    def make_preexec_fn(self, name: str) -> Callable[[], None]:
        """make_preexec_fn injects a best-effort cgroup scope before exec."""
        parent_fn = super().make_preexec_fn(name)
        username = _username_for(self)
        status = self._team_status()
        group = status.get("group")

        def preexec() -> None:
            if callable(parent_fn):
                parent_fn()
            if username:
                _ensure_notebook_dir(username)
            if group:
                _best_effort_cgroup_scope(group, self._runner)

        return preexec
