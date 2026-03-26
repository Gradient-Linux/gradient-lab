"""Repository-local JupyterHub configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SERVICE_NAME = "gradient-lab"
SERVICE_DISPLAY_NAME = "Gradient Lab"
SERVICE_DESCRIPTION = "Notebook and collaboration layer for Gradient Linux"
HUB_IP = "127.0.0.1"
HUB_PORT = 8889
HUB_BIND_URL = f"http://{HUB_IP}:{HUB_PORT}"
DB_URL = "sqlite:////var/lib/gradient/jupyterhub.sqlite"
SPAWNER_CLASS = "gradient_lab.spawner.GradientSpawner"
SERVER_EXTENSION_MODULE = "gradient_lab.server"
NOTEBOOK_DIR_TEMPLATE = "~/gradient/notebooks/{username}"
API_PROXY_SERVICE = {
    "name": "gradient-api-proxy",
    "display_name": "Gradient API Proxy",
    "url": "http://127.0.0.1:7777",
    "oauth_client_id": SERVICE_NAME,
}
DEFAULT_URL = "/lab"
ALLOW_ALL = False
OPEN_SESSIONS = True
ALLOW_NAMED_SERVERS = False
TEMPLATE_VARS = {
    "gradient_lab_brand": SERVICE_DISPLAY_NAME,
    "gradient_lab_service_name": SERVICE_NAME,
    "gradient_notebook_template": NOTEBOOK_DIR_TEMPLATE,
}
SERVER_EXTENSIONS = {SERVER_EXTENSION_MODULE: True}
ADMIN_GROUPS = ("gradient-admin",)
ALLOWED_GROUPS = ("gradient-admin", "gradient-operator", "gradient-developer")


def notebook_dir_for(username: str) -> str:
    """notebook_dir_for returns the notebook directory for a user."""
    return str(Path(NOTEBOOK_DIR_TEMPLATE.format(username=username)).expanduser())


def build_jupyterhub_settings() -> dict[str, Any]:
    """build_jupyterhub_settings returns the thin wrapper config payload."""
    return {
        "authenticator_class": "jupyterhub.auth.PAMAuthenticator",
        "allow_all": ALLOW_ALL,
        "open_sessions": OPEN_SESSIONS,
        "admin_groups": set(ADMIN_GROUPS),
        "allowed_groups": set(ALLOWED_GROUPS),
        "spawner_class": SPAWNER_CLASS,
        "ip": HUB_IP,
        "port": HUB_PORT,
        "bind_url": HUB_BIND_URL,
        "default_url": DEFAULT_URL,
        "allow_named_servers": ALLOW_NAMED_SERVERS,
        "db_url": DB_URL,
        "notebook_dir": NOTEBOOK_DIR_TEMPLATE,
        "services": [dict(API_PROXY_SERVICE)],
        "template_vars": dict(TEMPLATE_VARS),
        "server_extensions": dict(SERVER_EXTENSIONS),
    }


def apply_jupyterhub_config(config: Any) -> None:
    """apply_jupyterhub_config writes the repo-local settings onto a config object."""
    settings = build_jupyterhub_settings()
    config.JupyterHub.authenticator_class = settings["authenticator_class"]
    config.Authenticator.allow_all = settings["allow_all"]
    config.PAMAuthenticator.admin_groups = settings["admin_groups"]
    config.PAMAuthenticator.allowed_groups = settings["allowed_groups"]
    config.PAMAuthenticator.open_sessions = settings["open_sessions"]
    config.JupyterHub.spawner_class = settings["spawner_class"]
    config.JupyterHub.ip = settings["ip"]
    config.JupyterHub.port = settings["port"]
    config.JupyterHub.bind_url = settings["bind_url"]
    config.JupyterHub.default_url = settings["default_url"]
    config.JupyterHub.allow_named_servers = settings["allow_named_servers"]
    config.Spawner.notebook_dir = settings["notebook_dir"]
    config.Spawner.default_url = settings["default_url"]
    config.JupyterHub.db_url = settings["db_url"]
    config.JupyterHub.services = settings["services"]
    config.JupyterHub.template_vars = settings["template_vars"]
    config.ServerApp.jpserver_extensions = settings["server_extensions"]
