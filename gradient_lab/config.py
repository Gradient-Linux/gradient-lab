"""Repository-local JupyterHub configuration helpers."""

from __future__ import annotations

from typing import Any

ADMIN_GROUPS = ("gradient-admin",)
ALLOWED_GROUPS = ("gradient-admin", "gradient-operator", "gradient-developer")
HUB_IP = "127.0.0.1"
HUB_PORT = 8889
DB_URL = "sqlite:////var/lib/gradient/jupyterhub.sqlite"
SPAWNER_CLASS = "gradient_lab.spawner.GradientSpawner"
NOTEBOOK_DIR_TEMPLATE = "/gradient/notebooks/{username}"
API_PROXY_SERVICE = {
    "name": "gradient-api-proxy",
    "url": "http://127.0.0.1:7777",
    "oauth_client_id": "gradient-lab",
}


def notebook_dir_for(username: str) -> str:
    """notebook_dir_for returns the notebook directory for a user."""
    return NOTEBOOK_DIR_TEMPLATE.format(username=username)


def build_jupyterhub_settings() -> dict[str, Any]:
    """build_jupyterhub_settings returns the thin wrapper config payload."""
    return {
        "authenticator_class": "jupyterhub.auth.PAMAuthenticator",
        "admin_groups": set(ADMIN_GROUPS),
        "allowed_groups": set(ALLOWED_GROUPS),
        "spawner_class": SPAWNER_CLASS,
        "ip": HUB_IP,
        "port": HUB_PORT,
        "db_url": DB_URL,
        "notebook_dir": NOTEBOOK_DIR_TEMPLATE,
        "services": [dict(API_PROXY_SERVICE)],
    }


def apply_jupyterhub_config(config: Any) -> None:
    """apply_jupyterhub_config writes the repo-local settings onto a config object."""
    settings = build_jupyterhub_settings()
    config.JupyterHub.authenticator_class = settings["authenticator_class"]
    config.PAMAuthenticator.admin_groups = settings["admin_groups"]
    config.PAMAuthenticator.allowed_groups = settings["allowed_groups"]
    config.JupyterHub.spawner_class = settings["spawner_class"]
    config.JupyterHub.ip = settings["ip"]
    config.JupyterHub.port = settings["port"]
    config.Spawner.notebook_dir = settings["notebook_dir"]
    config.JupyterHub.db_url = settings["db_url"]
    config.JupyterHub.services = settings["services"]
