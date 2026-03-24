"""JupyterHub configuration for gradient-lab."""

from __future__ import annotations

try:
    c  # type: ignore[name-defined]
except NameError:
    from traitlets.config import get_config

    c = get_config()

from gradient_lab.config import apply_jupyterhub_config

apply_jupyterhub_config(c)

