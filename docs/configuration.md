# Configuration

Statsvy is highly configurable. Settings can come from multiple sources, with a clear priority order.

## Priority Order

Settings from higher-priority sources override lower ones:

1. **CLI flags** — `--verbose`, `--format json`, etc.
2. **Environment variables** — `STATSVY_CORE_FORMAT=json`
3. **Config file** — `pyproject.toml` or `statsvy.toml`
4. **Built-in defaults**

When both `pyproject.toml` and `statsvy.toml` exist, `pyproject.toml` takes precedence. The `--config` flag overrides both.

## Config File

Add a `[tool.statsvy]` section to your `pyproject.toml`:

```toml
[tool.statsvy.core]
default_format = "json"
verbose = false
color = true

[tool.statsvy.scan]
max_depth = 5
max_file_size_mb = 50.0
ignore_patterns = [".git", "node_modules", "__pycache__"]

[tool.statsvy.git]
enabled = true
show_contributors = true
max_contributors = 10
```

Or use a standalone `statsvy.toml` with the same structure.

## Environment Variables

Pattern: `STATSVY_<SECTION>_<KEY>` (uppercase, underscores).

```bash
export STATSVY_CORE_VERBOSE=true
export STATSVY_CORE_DEFAULT_FORMAT=json
export STATSVY_SCAN_MAX_DEPTH=5
export STATSVY_GIT_ENABLED=false
```

Values are automatically coerced to the correct type (bool, int, float, tuple, mapping).

## View Current Configuration

```bash
statsvy config
```

---

## Configuration Sections

### `[tool.statsvy.core]`

General application settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `name` | `str` | `"statsvy-projekt"` | Project name |
| `path` | `str` | current directory | Project root path |
| `default_format` | `str` | `"table"` | Output format (`table`, `json`, `md`) |
| `out_dir` | `str` | `"./"` | Output directory for generated files |
| `verbose` | `bool` | `false` | Enable verbose logging |
| `color` | `bool` | `true` | Enable colored output |
| `show_progress` | `bool` | `true` | Show progress indicators |
| `track_performance` | `bool` | `false` | Track and display performance metrics |

### `[tool.statsvy.scan]`

File scanning behavior.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `follow_symlinks` | `bool` | `false` | Follow symbolic links |
| `max_depth` | `int` | `-1` | Max directory depth (`-1` = unlimited) |
| `min_file_size_mb` | `float` | `0.0` | Minimum file size (MB) to include |
| `max_file_size_mb` | `float` | `100.0` | Maximum file size (MB) to include |
| `respect_gitignore` | `bool` | `true` | Honor `.gitignore` patterns |
| `include_hidden` | `bool` | `false` | Include hidden files/directories |
| `timeout_seconds` | `int` | `300` | Scan timeout in seconds |
| `ignore_patterns` | `list[str]` | `[".git"]` | Glob patterns to exclude |
| `binary_extensions` | `list[str]` | *(see note)* | File extensions treated as binary |

!!! note "Binary extensions"
    Default binary extensions: `.exe`, `.dll`, `.so`, `.dylib`, `.jpg`, `.png`, `.gif`, `.pdf`, `.zip`, `.tar`, `.gz`, `.pyc`

    User-provided `binary_extensions` are **merged** with the defaults, not replaced.

### `[tool.statsvy.language]`

Language detection and analysis.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `custom_language_mapping` | `dict` | `{}` | Map file extensions to language names |
| `exclude_languages` | `list[str]` | `[]` | Languages to exclude from analysis |
| `min_lines_threshold` | `int` | `0` | Minimum lines for a language to be reported |
| `count_comments` | `bool` | `true` | Include comment lines in counts |
| `count_blank_lines` | `bool` | `true` | Include blank lines in counts |
| `count_docstrings` | `bool` | `true` | Include docstring lines in counts |

### `[tool.statsvy.git]`

Git integration settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable Git integration |
| `include_stats` | `bool` | `true` | Include Git statistics |
| `include_branches` | `list[str]` | `[]` | Branches to include (empty = all) |
| `detect_authors` | `bool` | `true` | Detect file authors via Git blame |
| `show_contributors` | `bool` | `true` | Show contributor information |
| `max_contributors` | `int` | `5` | Max number of contributors to display |

### `[tool.statsvy.display]`

Output display options.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `truncate_paths` | `bool` | `true` | Truncate long file paths in output |
| `show_percentages` | `bool` | `true` | Show percentage columns |

### `[tool.statsvy.storage]`

Persistence settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `auto_save` | `bool` | `true` | Automatically save scan results |

### `[tool.statsvy.dependencies]`

Dependency analysis settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `include_dependencies` | `bool` | `true` | Analyze project dependencies |
| `exclude_dev_dependencies` | `bool` | `false` | Exclude dev dependencies |

### `[tool.statsvy.comparison]`

Comparison command settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `show_unchanged` | `bool` | `false` | Show unchanged items in comparisons |

### `[tool.statsvy.files]`

File analysis settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `duplicate_threshold_bytes` | `int` | `1024` | Min file size for duplicate detection |
| `find_large_files` | `bool` | `true` | Detect large files |
| `large_file_threshold_mb` | `int` | `10` | Size threshold (MB) to flag as "large" |

---

## Full Example

```toml
[tool.statsvy.core]
name = "my-project"
default_format = "json"
verbose = true
color = true
show_progress = true
track_performance = false

[tool.statsvy.scan]
max_depth = 5
max_file_size_mb = 50.0
respect_gitignore = true
include_hidden = false
timeout_seconds = 120
ignore_patterns = [".git", "node_modules", "__pycache__"]
binary_extensions = [".wasm", ".bin"]

[tool.statsvy.language]
exclude_languages = ["Markdown"]
min_lines_threshold = 10
count_comments = true
count_blank_lines = false

[tool.statsvy.storage]
auto_save = true

[tool.statsvy.git]
enabled = true
include_stats = true
show_contributors = true
max_contributors = 10

[tool.statsvy.display]
truncate_paths = true
show_percentages = true

[tool.statsvy.comparison]
show_unchanged = false

[tool.statsvy.dependencies]
include_dependencies = true
exclude_dev_dependencies = true

[tool.statsvy.files]
duplicate_threshold_bytes = 2048
find_large_files = true
large_file_threshold_mb = 25
```

## Type Coercion (Environment Variables)

| Target Type | String Format | Example |
|---|---|---|
| `bool` | `"true"`, `"1"`, `"yes"`, `"on"` = True | `STATSVY_CORE_VERBOSE=true` |
| `int` | Numeric string | `STATSVY_SCAN_MAX_DEPTH=5` |
| `float` | Numeric string | `STATSVY_SCAN_MAX_FILE_SIZE_MB=50.0` |
| `list[str]` | Comma-delimited | `STATSVY_SCAN_IGNORE_PATTERNS=.git,node_modules` |
| `dict` | JSON string | `STATSVY_LANGUAGE_CUSTOM_LANGUAGE_MAPPING='{"rs": "Rust"}'` |
