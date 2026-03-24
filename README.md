# gradient-lab

Notebook and collaboration wiring for Gradient Linux, built on top of JupyterHub.

## What it does

`gradient-lab` keeps the notebook tier thin. It configures JupyterHub for Gradient Linux accounts, injects team metadata into spawned notebook sessions, and leaves infrastructure authority with `concave`, `concave-resolver`, and the compute layer. The repository currently includes a Python package for JupyterHub wiring, a custom spawner, service files, and a minimal frontend scaffold.

## Requirements

- Ubuntu 24.04 LTS
- Python 3.11+
- JupyterHub 4+
- JupyterLab 4+
- Node.js 20+ for the frontend scaffold

## Install

`gradient-lab` is not released as a standalone package yet. Current work uses source builds for development and integration testing.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

## Usage

Run the repository-local JupyterHub wrapper from source:

```bash
jupyterhub --config jupyterhub_config.py
```

The notebook root is `/gradient/notebooks/{username}`. Team metadata is requested from `concave` during spawn.

## Configuration

Repository-local JupyterHub settings live in [`gradient_lab/config.py`](gradient_lab/config.py). The current defaults include:

- Hub bind address: `127.0.0.1:8889`
- Notebook root template: `/gradient/notebooks/{username}`
- PAM authentication
- `gradient_lab.spawner.GradientSpawner` as the active spawner

## Architecture

`gradient-lab` is a thin integration layer. It does not replace upstream JupyterHub and it does not own quota policy, Docker orchestration, or environment resolution. It reads team and quota metadata from `concave`, adds that metadata to spawned notebook sessions, and keeps the collaboration surface downstream of the core control plane.

## Development

### Prerequisites

Install Python 3.11 or newer. Install Node.js only if you need to work on the frontend scaffold.

### Build

The Python package is editable-install based. The frontend scaffold does not publish a separate build artifact yet.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

### Test

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Repo layout

```text
gradient-lab/
  gradient_lab/       JupyterHub config and custom spawner
  tests/              unit tests
  src/                frontend scaffold
  scripts/            systemd unit file
  jupyterhub_config.py
```

## Roadmap

The current line is a development preview for Gradient Linux v0.5. Near-term work focuses on quota-aware spawning, tighter `concave` integration, and a fuller browser-facing collaboration surface.

## License

License terms have not been published in this repository yet.
