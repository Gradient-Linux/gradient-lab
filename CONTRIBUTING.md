# Contributing to gradient-lab

This repository is a thin wrapper around upstream JupyterHub.
Contributions should keep that boundary intact.

## What belongs here

- JupyterHub configuration glue
- custom spawner helpers for Gradient Linux quotas
- small tests for config and spawn logic
- minimal frontend extension scaffolding
- service files and deployment docs

## What does not belong here

- a JupyterHub fork
- kernel management logic
- resolver logic
- compute engine implementation
- long-lived user data

## Development Flow

1. Work inside `gradient-lab/`.
2. Keep Python code in `gradient_lab/`.
3. Keep tests in `tests/`.
4. Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` before handing the repo back.
5. Keep commits focused and limited to this repository.

## Style

- Prefer small helper functions over large modules.
- Keep subprocess calls isolated and easy to mock.
- Keep tests deterministic and local.
