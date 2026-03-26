"""Jupyter Server configuration for gradient-lab."""

from __future__ import annotations

try:
    c  # type: ignore[name-defined]
except NameError:
    from traitlets.config import get_config

    c = get_config()

from gradient_lab.config import SERVICE_DISPLAY_NAME, SERVER_EXTENSION_MODULE

c.ServerApp.jpserver_extensions = {SERVER_EXTENSION_MODULE: True}
c.ServerApp.default_url = "/lab"
c.ServerApp.tornado_settings = {
    "headers": {
        "X-Gradient-Lab": SERVICE_DISPLAY_NAME,
    }
}
