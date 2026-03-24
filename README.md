# gradient-lab

`gradient-lab` is the Phase 14 notebook layer for Gradient Linux.
It stays intentionally thin:

- upstream JupyterHub provides the core notebook server
- `gradient_lab.spawner` adds compute-group aware spawn hooks
- `gradient_lab.config` centralizes the JupyterHub wiring
- `src/index.ts` is a minimal frontend scaffold for the Phase 14 sidebar work
- `scripts/gradient-lab.service` installs the systemd unit

## Layout

- `jupyterhub_config.py` - JupyterHub entrypoint
- `gradient_lab/` - Python package for config and spawner helpers
- `tests/` - unit tests for the repo-local Python logic
- `src/` - minimal frontend extension scaffold
- `scripts/` - systemd unit files

## Quick Start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` to validate the Python scaffold.
4. Launch JupyterHub with `jupyterhub --config jupyterhub_config.py`.

## Notes

- The notebook root is fixed at `/gradient/notebooks/{username}`.
- Users must already exist as Unix accounts and belong to a `gradient-*` group.
- This repository does not replace upstream JupyterHub.
