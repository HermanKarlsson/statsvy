## Contributing to statsvy

Thank you for your interest in contributing! This document explains how to set up a development environment and the preferred workflow.

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **[just](https://github.com/casey/just)** — command runner
- **Git**

### Getting Started

1. Fork the repository and clone it:

```bash
git clone https://github.com/HermanKarlsson/statsvy.git
cd statsvy
```

2. Install dependencies:

```bash
uv sync --all-extras
```

3. Set up pre-commit hooks (enforces formatting and commit message format):

```bash
just setup
```

4. Create a feature branch from `dev`:

```bash
git checkout dev
git checkout -b feat/your-feature
```

### Branching Model

We use a **main + dev** branching model:

```
feature/fix branches → dev (integration) → main (release)
```

- **`dev`** — integration branch. All feature/fix branches merge here via PR
- **`main`** — release branch. Merging `dev` into `main` triggers an automatic release
- **Feature branches** — branch from `dev`, name as `feat/description`, `fix/description`, etc.

### Commit Messages

We use **[Conventional Commits](https://www.conventionalcommits.org/)** — this is enforced by a pre-commit hook and is required for automatic versioning and changelog generation.

Format: `type(scope): subject`

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `perf` | Performance improvement | Patch |
| `docs` | Documentation only | None |
| `style` | Formatting, no logic change | None |
| `refactor` | Code restructuring | None |
| `test` | Adding/updating tests | None |
| `chore` | Build, CI, tooling | None |

For breaking changes, add `BREAKING CHANGE:` in the commit footer for a major version bump.

### Running Checks

```bash
# Run all checks (format → lint → type → test)
just check

# Individual checks
just format    # Format with ruff
just lint      # Lint with ruff
just type      # Type check with ty
just test      # Run tests with coverage
```

### Coding Standards

All code must follow the guidelines in [AGENTS.md](AGENTS.md). Key requirements:

- Ruff formatting (88 char line length)
- Type annotations on all functions
- Google-style docstrings
- Minimum 90% test coverage
- Frozen dataclasses by default
- One class per file

### Pull Requests

1. Branch from `dev`, not `main`
2. Ensure `just check` passes locally
3. Write/update tests for your changes
4. Open a PR against `dev`
5. Provide a clear description and link related issues

### Reporting Issues

Use the [issue tracker](https://github.com/HermanKarlsson/statsvy/issues). Include steps to reproduce, expected behavior, and your environment details.

Thank you for helping improve statsvy!
