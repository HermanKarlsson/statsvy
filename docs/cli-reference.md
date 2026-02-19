# CLI Reference

Complete reference for all statsvy commands and options.

## Global Options

```
statsvy [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--version` | Show the version and exit |
| `--config PATH` | Path to config file (pyproject.toml, statsvy.toml, etc.) |
| `--help` | Show help message and exit |

---

## `statsvy scan`

Scan a directory and display detailed file statistics.

```
statsvy scan [OPTIONS] [TARGET]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `TARGET` | Directory to scan (optional, defaults to current directory or tracked project) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--dir PATH` | | Directory to scan (alternative to positional TARGET) |
| `--ignore PATTERN` | `-i`, `-e` | Glob patterns to ignore (repeatable). Alias: `--exclude` |
| `--verbose` | `-v` | Enable verbose output |
| `--format FORMAT` | `-f` | Output format: `table`, `json`, `md`, `markdown` |
| `--output PATH` | `-o` | Save output to file |
| `--no-color` | | Disable colored output |
| `--no-progress` | | Disable progress bar |
| `--follow-symlinks` | | Follow symbolic links |
| `--max-depth N` | | Maximum directory depth to recurse into |
| `--max-file-size SIZE` | | Skip files larger than SIZE (e.g., `512b`, `1kb`, `1.5MB`) |
| `--min-file-size SIZE` | | Skip files smaller than SIZE |
| `--include-hidden` | | Include hidden files and directories |
| `--no-gitignore` | | Don't respect .gitignore rules |
| `--git / --no-git` | | Include/exclude git statistics |
| `--show-contributors / --no-show-contributors` | | Show/hide contributors in git stats |
| `--max-contributors N` | | Maximum number of contributors to display (default: 5) |
| `--no-save` | | Don't save scan results to history |
| `--truncate-paths / --no-truncate-paths` | | Truncate displayed file paths |
| `--percentages / --no-percentages` | | Show/hide percentage columns |
| `--track-io / --no-track-io` | | Enable/disable I/O profiling (application-level I/O accounting: total bytes read, elapsed time, files read) |
| `--track-mem / --no-track-mem` | | Enable/disable memory profiling (tracemalloc — peak memory) |
| `--track-performance / --no-track-performance` | | Enable/disable combined profiling (runs both I/O and memory passes)
| `--profile / --no-profile` | | Run both I/O and memory profiling (dual-pass: I/O pass first for accurate I/O metrics, then memory pass) |
| `--scan-timeout N` | `--timeout` | Maximum scan duration in seconds (default: 300) |
| `--min-lines-threshold N` | `--min-lines` | Skip files with fewer lines than N |
| `--no-deps` | | Skip dependency analysis |
| `--quiet` | `-q` | Suppress console output |

**Examples:**

```bash
# Basic scan
statsvy scan .

# Scan with multiple ignore patterns
statsvy scan . --ignore "venv/*" --ignore "*.pyc"

# JSON output saved to file
statsvy scan . --format json --output stats.json

# Scan with git stats and limited depth
statsvy scan . --git --max-depth 3

# Fast scan (no deps, no git)
statsvy scan . --no-deps --no-git
```

---

## `statsvy compare`

Compare metrics between two projects side by side.

```
statsvy compare [OPTIONS] PROJECT1 PROJECT2
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT1` | Path to the first project directory |
| `PROJECT2` | Path to the second project directory |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--format FORMAT` | `-f` | Output format: `table`, `json`, `md`, `markdown` |
| `--output PATH` | `-o` | Save output to file |
| `--verbose` | `-v` | Enable verbose output |
| `--no-color` | | Disable colored output |
| `--truncate-paths / --no-truncate-paths` | | Truncate displayed paths |
| `--percentages / --no-percentages` | | Show/hide percentage columns |

**Examples:**

```bash
# Compare two projects
statsvy compare /path/to/project1 /path/to/project2

# Compare with markdown output
statsvy compare proj1/ proj2/ --format markdown --output comparison.md
```

---

## `statsvy config`

Display the current configuration settings.

```
statsvy config
```

Shows all loaded configuration from config files, environment variables, and defaults.

---

## `statsvy track`

Start tracking the current project.

```
statsvy track
```

Creates a `.statsvy/project.json` file to store project metadata and scan history.

---

## `statsvy untrack`

Stop tracking the current project.

```
statsvy untrack
```

Removes the `.statsvy` directory, deleting all tracking data and scan history.

---

## `statsvy latest`

Display results from the most recent scan.

```
statsvy latest
```

---

## `statsvy history`

Display the full scan history for the tracked project.

```
statsvy history
```

---

## `statsvy current`

Display information about the currently tracked project.

```
statsvy current
```
