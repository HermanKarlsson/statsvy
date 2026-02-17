# Statsvy

A command-line tool for scanning projects and collecting comprehensive source code metrics. Statsvy analyzes file statistics, language distribution, line categories, dependencies, and git history — with output in table, JSON, or Markdown format.

## Key Features

- **Project Scanning** — Analyze source code metrics including total files, size, and line counts
- **Language Detection** — Automatically detects and categorizes source code by programming language
- **Code Analysis** — Counts production code, comments, and blank lines per language
- **Dependency Analysis** — Scans and aggregates dependencies across Python, Node.js, and Rust projects
- **Project Tracking** — Save projects and track metrics over time
- **Comparison** — Compare metrics side-by-side between two projects
- **Multiple Formats** — Display results as table, JSON, or Markdown
- **Git Integration** — Repository statistics including commits, branches, and contributors
- **Performance Profiling** — Optional memory usage tracking during scans
- **Configurable** — Settings via `pyproject.toml`, `statsvy.toml`, environment variables, or CLI flags

## Quick Example

```bash
# Install statsvy
pipx install git+https://github.com/HermanKarlsson/statsvy.git

# Scan a project
statsvy scan /path/to/project

# Compare two projects
statsvy compare /path/to/project1 /path/to/project2

# JSON output
statsvy scan . --format json
```

## Next Steps

- [Installation](installation.md) — Get statsvy installed
- [Quick Start](quickstart.md) — Learn the basics in 5 minutes
- [CLI Reference](cli-reference.md) — Full command documentation
- [Configuration](configuration.md) — Customize statsvy to your needs
