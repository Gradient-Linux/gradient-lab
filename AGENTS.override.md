---
type: repo-overrides
id: gradient-lab-override
title: gradient-lab Repo Overrides
status: active
agent: lab-agent
repo: gradient-lab
updated: 2026-03-24
tags: [repo-overrides, gradient-lab]
---

# gradient-lab Repo Overrides

## Scope

This repository is owned by the Lab Agent only.

## Working Rules

- Keep `gradient-lab` a thin wrapper around upstream JupyterHub.
- Do not add JupyterHub fork logic here.
- Keep Python logic isolated to `gradient_lab/` and tests in `tests/`.
- Keep the frontend scaffold minimal until Phase 15 work lands.
- Keep system integration artifacts in `scripts/`.

## Current Boundaries

- `jupyterhub_config.py` wires upstream JupyterHub to Gradient Linux auth and spawn behavior.
- `gradient_lab/spawner.py` contains the thin custom spawner hooks.
- `gradient_lab/config.py` contains repo-local config helpers.
- `src/index.ts` is a minimal extension scaffold, not a full product UI.

