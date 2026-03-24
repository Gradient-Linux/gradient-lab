"""Custom JupyterHub spawner hooks for Gradient Linux quotas."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace
from typing import Any, Callable, Mapping

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
    return group if isinstance(group, str) and group else None


def _quota_from_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    quota = payload.get("quota")
    return quota if isinstance(quota, dict) else None


def fetch_user_group(username: str, runner: Callable[..., Any] = subprocess.run) -> str | None:
    """fetch_user_group resolves the compute group for a user via concave."""
    result = runner(
        ["concave", "team", "status", "--user", username, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if getattr(result, "returncode", 1) != 0:
        return None
    return _group_from_payload(_parse_payload(getattr(result, "stdout", "")))


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
    quota: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """build_gradient_env merges Gradient Linux quota metadata into a session env."""
    env = dict(base_env)
    if group:
        env["GRADIENT_GROUP"] = group
    if quota:
        cpu = quota.get("cpu_cores")
        memory = quota.get("memory_gb")
        if cpu is not None:
            env["GRADIENT_CPU_LIMIT"] = str(cpu)
        if memory is not None:
            env["GRADIENT_MEM_LIMIT"] = str(memory)
    return env


def _systemd_slice_command(group: str, username: str) -> list[str]:
    return [
        "systemd-run",
        "--scope",
        "--slice",
        f"gradient-{group}.slice",
        "--uid",
        username,
        "--",
    ]


class GradientSpawner(LocalProcessSpawner):
    """GradientSpawner enforces compute-group metadata at notebook spawn time."""

    def __init__(self, *args: Any, runner: Callable[..., Any] = subprocess.run, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._runner = runner

    def user_env(self, env: Mapping[str, str]) -> dict[str, str]:
        """user_env adds Gradient Linux session metadata to the notebook environment."""
        base_env = super().user_env(env)
        username = _username_for(self)
        group = fetch_user_group(username, runner=self._runner) if username else None
        quota = fetch_group_quota(group, runner=self._runner) if group else None
        return build_gradient_env(base_env, group=group, quota=quota)

    def make_preexec_fn(self, name: str) -> Callable[[], None]:
        """make_preexec_fn injects a best-effort cgroup scope before exec."""
        parent_fn = super().make_preexec_fn(name)
        username = _username_for(self)
        group = fetch_user_group(username, runner=self._runner) if username else None

        def preexec() -> None:
            if callable(parent_fn):
                parent_fn()
            if group:
                self._runner(
                    _systemd_slice_command(group, name),
                    capture_output=True,
                    text=True,
                    check=False,
                )

        return preexec
