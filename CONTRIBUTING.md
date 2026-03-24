# Contributing to gradient-lab

Contributions are welcome for JupyterHub wiring, spawner behavior, tests, and documentation. Keep the repository thin. Core infrastructure, suite management, and environment resolution belong in the rest of the Gradient Linux stack.

## Before you start

Read [README.md](README.md) and [docs/README.md](docs/README.md) before changing the JupyterHub contract or the spawner behavior.

## Development setup

Use Ubuntu 24.04 with Python 3.11 or newer.

```bash
git clone <repo-url>
cd gradient-lab
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

If you need to work on the frontend scaffold, install Node.js 20 or newer. The scaffold is present in `src/`, but it does not publish a production build pipeline yet.

## Making changes

### Branching

Use one of these branch prefixes:

- `feat/<slug>`
- `fix/<slug>`
- `docs/<slug>`

### Commit messages

Format commits as `<type>(<scope>): <summary>`.

Use these types:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `chore`

Keep the summary under 72 characters.

Examples:

- `feat(spawner): attach gradient quota environment`
- `fix(config): preserve notebook directory template`
- `docs(readme): clarify source-only install path`

### Tests

- Add or update tests for any new function or behavior change.
- Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` before opening a pull request.
- Keep subprocess calls isolated and easy to replace in tests.

### Pull requests

- Keep pull requests focused and limited to one logical change.
- Explain the effect on JupyterHub startup, spawn flow, or `concave` integration.
- Include manual validation steps when changes touch live JupyterHub behavior.

## Code conventions

- Keep `gradient-lab` as a thin wrapper around upstream JupyterHub.
- Do not fork JupyterHub behavior into large local subsystems.
- Preserve `/gradient/notebooks/{username}` as the notebook root template unless there is a documented migration plan.
- Keep calls into `concave` explicit and easy to mock.
- Use separate command arguments instead of shell interpolation.

## What we don't accept

- Dependencies added without prior discussion in an issue.
- Environment resolver logic copied into this repository.
- Quota policy duplicated here instead of being read from `concave`.
- Shell string interpolation with user-controlled input.

## License

By contributing, you agree that your contributions will be released under the repository license when one is published.
