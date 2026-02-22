# Quick Start

Get started with statsvy in 5 minutes.

## Scan a Project

Navigate to any project directory and run:

```bash
statsvy scan .
```

This produces a table with file counts, sizes, line counts, and language distribution.

You can also pass a path directly:

```bash
statsvy scan /path/to/my/project
```

## Choose an Output Format

Statsvy supports three output formats:

=== "Table (default)"

    ```bash
    statsvy scan .
    ```

=== "JSON"

    ```bash
    statsvy scan . --format json
    ```

=== "Markdown"

    ```bash
    statsvy scan . --format markdown
    ```

=== "HTML"

    ```bash
    statsvy scan . --format html
    ```

You can disable the small embedded stylesheet by adding `--no-css`:

    ```bash
    statsvy scan . --format html --no-css
    ```

Save output to a file:

```bash
statsvy scan . --format json --output stats.json
```

## Include Git Statistics

Add repository information like commit count, branches, and contributors:

```bash
statsvy scan . --git
```

## Track Projects Over Time

Save and track projects to compare metrics across scans:

```bash
# Start tracking the current project
statsvy track

# Run a scan (results are saved automatically)
statsvy scan .

# View the latest saved results
statsvy latest

# View full scan history
statsvy history

# See current project info
statsvy current
```

## Compare Projects

Compare metrics between two projects side by side:

```bash
statsvy compare /path/to/project1 /path/to/project2
```

## Common Options

```bash
# Skip dependency analysis (faster scans)
statsvy scan . --no-deps

# Limit scan depth
statsvy scan . --max-depth 3

# Include hidden files
statsvy scan . --include-hidden

# Set a scan timeout
statsvy scan . --timeout 60

# Verbose output
statsvy scan . --verbose
```

## Configuration

Statsvy reads settings from multiple sources (highest to lowest priority):

1. CLI flags (`--format json`)
2. Environment variables (`STATSVY_CORE_FORMAT=json`)
3. Config file (`pyproject.toml` under `[tool.statsvy]` or `statsvy.toml`)

View your current configuration:

```bash
statsvy config
```

See the [Configuration guide](configuration.md) for full details.

## Next Steps

- [CLI Reference](cli-reference.md) — Full list of commands and options
- [Configuration](configuration.md) — Customize defaults and behavior
