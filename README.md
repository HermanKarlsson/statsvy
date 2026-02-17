# statsvy

[![CI](https://github.com/HermanKarlsson/statsvy/actions/workflows/ci.yml/badge.svg)](https://github.com/HermanKarlsson/statsvy/actions/workflows/ci.yml)
[![GitHub Release](https://img.shields.io/github/v/release/HermanKarlsson/statsvy)](https://github.com/HermanKarlsson/statsvy/releases)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://readthedocs.org/projects/statsvy/badge/?version=latest)](https://statsvy.readthedocs.io)

A command-line tool for scanning projects and collecting comprehensive source code metrics. Statsvy analyzes file statistics, language distribution, line categories, dependencies, and git history — with output in table, JSON, or Markdown format.

## Key Features

- **Project Scanning**: Analyze source code metrics including total files, size, and line counts
- **Language Detection**: Automatically detects and categorizes source code by programming language
- **Code Analysis**: Counts production code, comments, and blank lines per language
- **Dependency Analysis**: Scans and aggregates dependencies across formats:
  - Python: `pyproject.toml`, `requirements.txt`
  - Node.js: `package.json`
  - Rust: `Cargo.toml`
  - Detects version conflicts when the same package appears with different versions
- **Project Tracking**: Save projects and track metrics over time
- **Comparison**: Compare metrics side-by-side between two projects
- **Multiple Formats**: Display results as table, JSON, or Markdown
- **Git Integration**: Repository statistics including commits, branches, and contributors
- **Performance Profiling**: Optional memory usage tracking during scans
- **Configurable**: Settings via `pyproject.toml`, `statsvy.toml`, environment variables, or CLI flags

## Installation

### Recommended: pipx (from GitHub)

```bash
pipx install git+https://github.com/HermanKarlsson/statsvy.git
```

To install a specific version:

```bash
pipx install git+https://github.com/HermanKarlsson/statsvy.git@v1.0.0
```

### pip

```bash
pip install git+https://github.com/HermanKarlsson/statsvy.git
```

### From a GitHub Release

Download the `.whl` file from the [Releases page](https://github.com/HermanKarlsson/statsvy/releases) and install it:

```bash
pipx install ./statsvy-1.0.0-py3-none-any.whl
```

### From Source

```bash
git clone https://github.com/HermanKarlsson/statsvy.git
cd statsvy
uv sync --all-extras
uv run statsvy --help
```

For full installation instructions see the [documentation](https://statsvy.readthedocs.io/installation/).

## Usage

### Scanning a Project

```bash
# Scan the current directory
statsvy scan .

# Scan a specific path
statsvy scan /path/to/project

# Scan with ignore patterns
statsvy scan . --ignore "venv/*" --exclude "*.pyc"
```

### Output Formats

```bash
# Table format (default)
statsvy scan .

# JSON format
statsvy scan . --format json

# Markdown format
statsvy scan . --format markdown

# Save output to a file
statsvy scan . --format json --output stats.json
```

### Scan Options

```bash
# Skip dependency analysis
statsvy scan . --no-deps

# Include git statistics
statsvy scan . --git

# Limit scan depth
statsvy scan . --max-depth 3

# Skip large files
statsvy scan . --max-file-size 1mb

# Include hidden files
statsvy scan . --include-hidden

# Ignore .gitignore rules
statsvy scan . --no-gitignore

# Enable performance profiling
statsvy scan . --track-performance

# Set a scan timeout (seconds)
statsvy scan . --timeout 60

# Skip files with fewer than N lines
statsvy scan . --min-lines 5

# Suppress console output
statsvy scan . --quiet

# Don't save results to history
statsvy scan . --no-save
```

### Project Tracking

```bash
# Start tracking the current project
statsvy track

# Stop tracking the current project
statsvy untrack
```

### Viewing Results

```bash
# Show the latest scan results
statsvy latest

# Show full scan history
statsvy history

# Show current project info
statsvy current
```

### Comparing Projects

```bash
# Compare two projects
statsvy compare /path/to/project1 /path/to/project2

# Compare with JSON output
statsvy compare /path/to/project1 /path/to/project2 --format json

# Save comparison to file
statsvy compare /path/to/project1 /path/to/project2 --output comparison.md --format markdown
```

### Configuration

```bash
# Show current configuration
statsvy config

# Use a specific config file
statsvy --config path/to/pyproject.toml scan .
```

Configuration can be provided under `[tool.statsvy]` in `pyproject.toml` or in a dedicated `statsvy.toml` file. When both are present, `pyproject.toml` takes precedence. The `--config` flag always wins.

Settings are also available as environment variables prefixed with `STATSVY_` (e.g., `STATSVY_CORE_FORMAT=json`).

### Help

```bash
statsvy --help
statsvy scan --help
statsvy compare --help
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and contribution guidelines.

## Documentation

Full documentation is available at [statsvy.readthedocs.io](https://statsvy.readthedocs.io).

## License

MIT — see [LICENSE](LICENSE) for details.
