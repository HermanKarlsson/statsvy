# Contributing

Thank you for your interest in contributing to statsvy! This guide covers development setup, workflow, and coding standards.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **[just](https://github.com/casey/just)** — command runner
- **Git**

## Getting Started

1. **Fork and clone** the repository:

    ```bash
    git clone https://github.com/<your-username>/statsvy.git
    cd statsvy
    ```

2. **Install dependencies**:

    ```bash
    uv sync --all-extras
    ```

3. **Set up pre-commit hooks** (enforces formatting and commit message format):

    ```bash
    just setup
    ```

4. **Create a feature branch** from `dev`:

    ```bash
    git checkout dev
    git checkout -b feat/your-feature
    ```

## Development Workflow

### Running Checks

```bash
# Run all checks (format → lint → type → test)
just check

# Individual checks
just format    # Format code with ruff
just lint      # Lint with ruff
just type      # Type check with ty
just test      # Run tests with coverage
```

### Quick Development

```bash
# Run statsvy without checks
just dev scan .

# Run statsvy with all checks first
just run
```

### Documentation

```bash
# Preview docs locally
just docs

# Build docs
just docs-build
```

## Branching Model

We use a **main + dev** branching model:

```
feature/fix branches → dev (integration) → main (release)
```

- **`dev`** — integration branch. All feature/fix branches merge here via PR
- **`main`** — release branch. Only `dev` merges into `main` to trigger releases
- **Feature branches** — branch from `dev`, name as `feat/description` or `fix/description`

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feat/short-description` | `feat/html-export` |
| Bug fix | `fix/short-description` | `fix/scanner-symlink` |
| Docs | `docs/short-description` | `docs/config-guide` |
| Refactor | `refactor/short-description` | `refactor/analyzer` |

## Commit Messages

We use **[Conventional Commits](https://www.conventionalcommits.org/)** — this is enforced by a pre-commit hook and is required for automatic version bumping and changelog generation.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | **Minor** (0.x.0) |
| `fix` | Bug fix | **Patch** (0.0.x) |
| `perf` | Performance improvement | Patch |
| `docs` | Documentation only | None |
| `style` | Formatting, no logic change | None |
| `refactor` | Code change, no new feature/fix | None |
| `test` | Adding/updating tests | None |
| `chore` | Build, CI, tooling changes | None |

### Breaking Changes

For a **major** version bump (x.0.0), add `BREAKING CHANGE:` in the commit footer:

```
feat(scanner): change scan output format

BREAKING CHANGE: scan() now returns ScanResult instead of dict
```

### Examples

```
feat(analyzer): add support for Rust language detection
fix(scanner): handle symlink loops gracefully
docs(readme): add installation instructions
test(config): add tests for env variable parsing
chore(ci): add Python 3.13 to test matrix
```

## Coding Standards

All code must follow the guidelines in [AGENTS.md](https://github.com/HermanKarlsson/statsvy/blob/main/AGENTS.md). Key points:

- **Formatting**: `ruff format` (88 char line length)
- **Linting**: `ruff check` with extensive rule set
- **Type checking**: `ty check` (all errors are fatal)
- **Test coverage**: minimum 90%
- **Docstrings**: Google style, required for all public APIs
- **Immutability**: `frozen=True` dataclasses by default
- **One class per file**
- **No global variables** — use dependency injection
- **Composition over inheritance**

## Pull Requests

1. Branch from `dev`, not `main`
2. Ensure `just check` passes locally
3. Write/update tests for your changes
4. Open a PR against `dev`
5. Provide a clear description of what and why
6. Link related issues

## Reporting Issues

Use the [issue tracker](https://github.com/HermanKarlsson/statsvy/issues) to report bugs or request features. Include:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Statsvy version (`statsvy --version`)
