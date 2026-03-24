# gradient-lab docs

This directory tracks the public repository documentation for `gradient-lab`.

## Start here

- [README.md](../README.md) explains the notebook-layer boundary, local setup, and runtime defaults.
- [CONTRIBUTING.md](../CONTRIBUTING.md) covers build, test, and review expectations.

## Runtime contract

- Hub bind address: `127.0.0.1:8889`
- Notebook root template: `/gradient/notebooks/{username}`
- Spawner class: `gradient_lab.spawner.GradientSpawner`

## Scope

`gradient-lab` wires JupyterHub into the Gradient Linux control plane. It does not own quota policy, suite lifecycle, or environment resolution.
