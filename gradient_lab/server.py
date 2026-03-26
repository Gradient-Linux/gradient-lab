"""Notebook-server status endpoint for gradient-lab."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

try:
    from tornado.web import RequestHandler
except Exception:  # pragma: no cover - fallback for bootstrap tests

    class RequestHandler:  # type: ignore[no-redef]
        """Minimal RequestHandler fallback used when Tornado is unavailable."""

        def set_header(self, name: str, value: str) -> None:
            self.headers = getattr(self, "headers", {})
            self.headers[name] = value

        def write(self, chunk: Any) -> None:
            self.body = chunk

from .config import SERVICE_DISPLAY_NAME
from .permissions import normalize_role, visible_actions

RESOLVER_STATUS_URL = "http://127.0.0.1:7777/api/v1/env/status"


def _json_response(url: str, opener: Callable[..., Any] = urllib.request.urlopen, timeout: float = 2.0) -> dict[str, Any]:
    try:
        with opener(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network failure path
        return {"available": False, "error": str(exc)}
    try:
        data = json.loads(payload or "{}")
    except json.JSONDecodeError:
        return {"available": False, "error": "invalid JSON from concave"}
    return data if isinstance(data, dict) else {"available": False, "error": "unexpected payload"}


def _coerce_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _quota_from_env(env: Mapping[str, str]) -> dict[str, Any]:
    quota: dict[str, Any] = {}
    group = env.get("GRADIENT_GROUP")
    if group:
        quota["group"] = group
    role = normalize_role(env.get("GRADIENT_ROLE") or env.get("JUPYTERHUB_ROLE"))
    quota["role"] = role
    cpu = _coerce_int(env.get("GRADIENT_CPU_LIMIT") or env.get("GRADIENT_QUOTA_CPU_CORES"))
    memory = _coerce_int(env.get("GRADIENT_MEM_LIMIT") or env.get("GRADIENT_QUOTA_MEMORY_GB"))
    gpu = _coerce_int(env.get("GRADIENT_QUOTA_GPU_COUNT"))
    if cpu is not None:
        quota["cpu_cores"] = cpu
    if memory is not None:
        quota["memory_gb"] = memory
    if gpu is not None:
        quota["gpu_count"] = gpu

    extras: dict[str, Any] = {}
    for key, value in env.items():
        if not key.startswith("GRADIENT_QUOTA_"):
            continue
        suffix = key.removeprefix("GRADIENT_QUOTA_").lower()
        if suffix in {"cpu_cores", "memory_gb", "gpu_count"}:
            continue
        extras[suffix] = value
    if extras:
        quota["extra"] = extras
    return quota


def build_status_payload(env: Mapping[str, str], opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    """build_status_payload combines resolver status, quota metadata, and role actions."""
    role = normalize_role(env.get("GRADIENT_ROLE") or env.get("JUPYTERHUB_ROLE"))
    if env.get("JUPYTERHUB_ADMIN") in {"1", "true", "True"}:
        role = "gradient-admin"
    payload = {
        "service": SERVICE_DISPLAY_NAME,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "group": env.get("GRADIENT_GROUP", ""),
        "role": role,
        "quota": _quota_from_env(env),
        "resolver": _json_response(RESOLVER_STATUS_URL, opener=opener),
        "actions": visible_actions(role),
    }
    return payload


class GradientLabStatusHandler(RequestHandler):
    """Serve the sidebar payload used by the JupyterLab extension."""

    def get(self) -> None:
        self.set_header("Content-Type", "application/json")
        self.write(build_status_payload(os.environ))


def load_jupyter_server_extension(server_app: Any) -> None:
    """Register the gradient-lab status endpoint."""
    web_app = getattr(server_app, "web_app", None)
    if web_app is None:  # pragma: no cover - defensive bootstrap
        return
    base_url = web_app.settings.get("base_url", "/")
    route = f"{base_url.rstrip('/')}/gradient-lab/status"
    web_app.add_handlers(".*$", [(route, GradientLabStatusHandler)])


def _jupyter_server_extension_points() -> list[dict[str, str]]:
    return [{"module": "gradient_lab.server"}]
