# Statsvy Architecture

## Overview

**Statsvy** is a command-line tool for analyzing and tracking code metrics in projects. It scans directories, analyzes code statistics, and provides detailed insights about project size, language distribution, and other metrics. The tool supports multiple output formats and can store historical data for trend analysis.

## Architecture Principles

- **Separation of Concerns**: Each module handles a specific responsibility
- **Modularity**: Components are loosely coupled and can be developed/tested independently
- **Configuration-Driven**: Centralized configuration management for flexibility
- **Plugin Architecture**: Extensible formatter system for different output formats
- **Data/Logic Separation**: Data models (`@dataclass`) contain only data; logic resides in separate coordinator and processor classes
- **Core as Coordinator**: The `core/` module coordinates between domain logic; if a component violates SRP, it should be extracted to a separate module that `core/` orchestrates

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                CLI Layer (cli_main.py)                      │
│          User commands and argument parsing (Click)         │
│  ┌────────────────────────────────────────────────┐         │
│  │  CLI Handlers (cli/)                           │         │
│  │  • ScanHandler (scan orchestration)            │         │
│  │  • CompareHandler (comparison orchestration)   │         │
│  │  • CompareOptions (immutable options container) │        │
│  └────────────────────────────────────────────────┘         │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬──────────────┐
     │               │               │              │
     ▼               ▼               ▼              ▼
┌─────────────────────────────────────────────────────────┐
│    Configuration (config/)   │   Storage (storage/)     │
│  • ConfigLoader              │   • Storage              │
│  • ConfigFileReader          │   • HistoryStorage       │
│  • ConfigEnvReader           │   • ProjectMetadataStorage│
│  • ConfigValueConverter      │   • StoragePresenter     │
└──────────────────────────────┴──────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│    Core Layer (Coordination)                            │
│  • Scanner (filesystem)                                 │
│  • Analyzer (metrics)                                   │
│  • Formatter (coordinator for display)                  │
│  • ComparisonAnalyzer (project comparison)              │
│  • Project (tracking with strategy pattern)             │
│  • ProjectScanner (dependency scanning coordinator)     │
│  • GitStats (git metrics)                               │
│  • PerformanceTracker (memory profiling)                │
└─────────────────────────────────────────────────────────┘
     │
     ▼
   ┌──────────────────────────────────────────────┐
   │      Data Layer (data/)                      │
   │  • Config (@dataclass - data only)           │
   │  • Metrics (@dataclass - data only)          │
   │  • ScanResult (@dataclass)                   │
   │  • ProjectMeta (@dataclass)                  │
   │  • ComparisonResult (@dataclass)             │
   │  • GitInfo (@dataclass)                      │
   │  • PerformanceMetrics (@dataclass)           │
   │  • Dependency / DependencyInfo (@dataclass)  │
   │  • ProjectFileInfo (@dataclass)              │
   └──────────────────────────────────────────────┘
     │
     ▼
  ┌──────────────────────────────────────────────┐
  │   Formatters & Serializers                   │
  │   formatters/:                               │
  │   • JsonFormatter                            │
  │   • MarkdownFormatter                        │
  │   • TableFormatter                           │
  │   • HistoryFormatter                         │
  │   • SummaryFormatter                         │
  │   • CompareFormatter                         │
  │   • PerformanceMetricsFormatter              │
  │   serializers/:                              │
  │   • MetricsSerializer                        │
  │   • ProjectMetaSerializer                    │
  │   • GitInfoSerializer                        │
  │   • ProjectInfoSerializer                    │
  └──────────────────────────────────────────────┘
```

## Directory Structure

```
src/statsvy/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point for module execution
├── cli_main.py              # Command-line interface (Click commands)
├── cli/                     # CLI command handlers
│   ├── __init__.py
│   ├── scan_handler.py      # Orchestrates scan command
│   ├── compare_handler.py   # Orchestrates compare command
│   └── compare_options.py   # Immutable options container for compare
├── config/                  # Configuration management
│   ├── __init__.py
│   ├── config_loader.py     # Coordinates config from multiple sources
│   ├── config_file_reader.py    # Reads TOML config files
│   ├── config_env_reader.py     # Reads environment variables
│   └── config_value_converter.py # Type conversion for config values
├── config_readers/          # Dependency file readers (Strategy pattern)
│   ├── __init__.py
│   ├── config_readers_factory.py  # Routes to appropriate reader
│   ├── project_config_reader.py   # Protocol for config readers
│   ├── pyproject_reader.py        # Reads pyproject.toml dependencies
│   ├── package_json_reader.py     # Reads package.json dependencies
│   ├── cargo_toml_reader.py       # Reads Cargo.toml dependencies
│   └── requirements_txt_reader.py # Reads requirements.txt dependencies
├── core/                    # Core coordinators (orchestrates logic)
│   ├── __init__.py
│   ├── analyzer.py          # Analyzes files and calculates metrics
│   ├── comparison.py        # Compares metrics between two projects
│   ├── formatter.py         # Formatter coordinator (routes to formatters)
│   ├── git_stats.py         # Git repository metrics
│   ├── performance_tracker.py # Memory profiling via tracemalloc
│   ├── project.py           # Project tracking (uses strategy pattern)
│   ├── project_config_readers.py # Strategy pattern for project name reading
│   ├── project_scanner.py   # Coordinates dependency scanning
│   └── scanner.py           # Directory scanning and file discovery
├── data/                    # Data structures (@dataclass models - data only)
│   ├── __init__.py
│   ├── comparison_result.py # Comparison result between two metrics snapshots
│   ├── config.py            # Configuration dataclass with defaults
│   ├── dependency.py        # Single dependency entry
│   ├── dependency_info.py   # Aggregated dependency information
│   ├── git_info.py          # Git repository metadata
│   ├── metrics.py           # Metrics dataclass
│   ├── performance_metrics.py # Performance metrics (peak memory)
│   ├── project_file_info.py # Project info from configuration files
│   ├── project_info.py      # Re-exports for backward compatibility
│   ├── project_meta.py      # Project metadata dataclass
│   └── scan_result.py       # Scan results dataclass
├── formatters/              # Specific formatter implementations
│   ├── __init__.py
│   ├── compare_formatter.py # Comparison output formatter (table/json/md)
│   ├── history_formatter.py # History analysis formatter
│   ├── json_formatter.py    # JSON output formatter
│   ├── markdown_formatter.py # Markdown output formatter
│   ├── performance_metrics_formatter.py # Performance metrics formatting
│   ├── summary_formatter.py # Project summary formatter
│   └── table_formatter.py   # Table/CLI output formatter
├── language_parsing/        # Language detection and analysis
│   ├── __init__.py
│   ├── language_analyzer.py # Analyzes lines by category (code/comment/blank)
│   └── language_detector.py # Detects programming language
├── serializers/             # Serialization of data classes
│   ├── __init__.py
│   ├── git_info_serializer.py     # Serialize GitInfo to dict
│   ├── metrics_serializer.py      # Serialize/deserialize Metrics
│   ├── project_info_serializer.py # Serialize/deserialize dependency data
│   └── project_meta_serializer.py # Serialize/deserialize ProjectMeta
├── storage/                 # Data persistence
│   ├── __init__.py
│   ├── storage.py           # Coordinates save operations
│   ├── history_storage.py   # Manages history.json
│   ├── project_metadata_storage.py # Manages project.json
│   └── storage_presenter.py # Presentation layer (show_* commands)
└── utils/                   # Utility functions and helpers
    ├── __init__.py
    ├── console.py           # Rich console wrapper
    ├── formatting.py        # Size formatting, delta strings, path truncation
    ├── output_handler.py    # Handles output to file or console
    ├── path_resolver.py     # Resolves target directory for scanning
    ├── project_info_merger.py # Merges dependencies and detects conflicts
    └── timeout_checker.py   # Timeout checking for scan operations
```

## Core Components

### 1. CLI Layer (`cli_main.py`)

**Responsibility**: Handles user interaction and command-line argument parsing

**Key Features**:
- Uses Click framework for command-line interface
- `scan` command: Primary command to analyze a directory (delegates to ScanHandler)
- `compare` command: Compare metrics between projects (delegates to CompareHandler)
- `track`/`untrack` commands: Project tracking management
- `latest`/`history`/`current` commands: Display stored data (delegates to StoragePresenter)
- `config` command: Display current configuration settings
- Configuration options: `--ignore`, `--format`, `--output`, `--verbose`, etc.
- Progress reporting and error handling

**Main Classes**:
- `ScanKwargs`: TypedDict defining all configurable scan parameters

**Command Handlers**:
- `ScanHandler` (cli/scan_handler.py): Orchestrates scan workflow
- `CompareHandler` (cli/compare_handler.py): Orchestrates comparison workflow
- `CompareOptions` (cli/compare_options.py): Frozen dataclass containing compare command options

**Flow**:
```
User Input (CLI args)
    ↓
Click parses arguments
    ↓
ConfigLoader merges from multiple sources
    ↓
Handler (ScanHandler/CompareHandler) orchestrates
    ↓
Scanner, Analyzer, Formatter execute
    ↓
Storage saves results (optional)
    ↓
Output to console or file
```

### 2. Scanner (`core/scanner.py`)

**Responsibility**: Recursively scans directories and discovers files

**Key Features**:
- Traverses directory tree efficiently
- Respects `.gitignore` patterns by default
- Supports custom ignore patterns
- Calculates file statistics (count, total size)
- Optional progress bar visualization

**Main Class**: `Scanner`
- `__init__()`: Validates path, parses gitignore
- `scan()`: Returns ScanResult with file list and statistics
- `_parse_gitignore()`: Extracts patterns from .gitignore

**Output**:
- `ScanResult`: Contains list of all discovered files, total count, total bytes

### 3. Analyzer (`core/analyzer.py`)

**Responsibility**: Processes scanned files and calculates detailed metrics

**Key Features**:
- Detects programming language for each file
- Counts total lines per file and per language
- Categorizes lines as code, comments, or blank
- Supports verbose analysis output
- Integrates with LanguageDetector and LanguageAnalyzer

**Main Class**: `Analyzer`
- `__init__()`: Sets up language detection with optional config file
- `analyze()`: Takes ScanResult, returns Metrics
- Delegates language parsing to specialized modules

**Output**:
- `Metrics`: Contains aggregated statistics (total lines, lines by language, etc.)

### 3a. ComparisonAnalyzer (`core/comparison.py`)

**Responsibility**: Compares metrics from two projects and computes deltas

**Key Features**:
- Computes overall deltas (total files, lines, size)
- Computes per-language deltas (lines, comments, blanks)
- Computes per-category deltas
- Handles languages present in only one project

**Main Class**: `ComparisonAnalyzer` (all static methods)
- `compare()`: Entry point — returns `ComparisonResult`
- `_compute_deltas()`: Orchestrates delta computation across categories

### 3b. PerformanceTracker (`core/performance_tracker.py`)

**Responsibility**: Tracks memory usage during scan operations via `tracemalloc`

**Main Class**: `PerformanceTracker`
- `start()`: Begins memory tracking
- `stop()`: Stops tracking and returns `PerformanceMetrics` with peak memory usage
- `is_active()`: Checks if tracker is currently running

### 3c. ProjectScanner (`core/project_scanner.py`)

**Responsibility**: Coordinates dependency scanning across multiple configuration file formats

**Main Class**: `ProjectScanner`
- `scan()`: Finds config files, reads them via factory, merges via `ProjectInfoMerger`
- `_find_config_files()`: Discovers supported config files in the project root
- `_read_config_files()`: Delegates to `config_readers_factory` for each file

**Supported Files**: `pyproject.toml`, `package.json`, `Cargo.toml`, `requirements.txt`

#### ConfigLoader (`config/config_loader.py`)

**Responsibility**: Coordinates configuration from multiple sources with priority

**Configuration Sources** (in priority order):
1. CLI arguments (highest priority)
2. Environment variables (via ConfigEnvReader)
3. Configuration file - pyproject.toml (via ConfigFileReader)
4. Default values in Config class

**Architecture**:
- Follows coordinator pattern
- Delegates file reading to ConfigFileReader
- Delegates environment variable reading to ConfigEnvReader
- Delegates type conversion to ConfigValueConverter

**Main Classes**:
- `ConfigLoader`: Coordinates the entire config loading process
- `ConfigFileReader`: Reads TOML configuration files
- `ConfigEnvReader`: Extracts STATSVY_* environment variables
- `ConfigValueConverter`: Handles type conversion and validation

#### Config (`data/config.py`)

**Responsibility**: Defines default configuration values

**Configuration Sections**:
- `core`: General app settings (format, verbosity, color, progress)
- `scan`: File system scanning (depth, symlinks, gitignore, file size limits)
- `language`: Language detection and line analysis
- `storage`: History and data persistence
- `git`: Git repository analysis settings
- `display`: Terminal output formatting (themes, tables)
- `reporting`: Report generation settings
- `comparison`: Time-based comparison logic
- `dependencies`: Dependency analysis
- `files`: File-level analysis (duplicates, large files)
- `projects`: Project metadata

### 5. Display/Formatting System

#### Formatter (`core/formatter.py`)

**Responsibility**: Coordinates output formatting (Strategy pattern)

**Supported Formats**:
- `table`: Human-readable table format (default)
- `json`: Machine-readable JSON format
- `markdown` / `md`: Markdown document format
- `history`: Historical data and trends

**Main Class**: `Formatter`
- `format()`: Static method that routes to appropriate formatter based on format_type
- Raises ValueError for unknown formats
- Acts as a coordinator/orchestrator between core and specific formatters

#### Formatter Implementations (`formatters/`)

Each formatter takes a `Metrics` object and produces formatted output:

- **TableFormatter**: CLI-friendly table with Rich styling
- **JsonFormatter**: JSON serialization for programmatic consumption
- **MarkdownFormatter**: Markdown with tables and sections
- **HistoryFormatter**: Processes historical metrics for trend analysis
- **CompareFormatter**: Comparison output in table, JSON, or Markdown format
- **PerformanceMetricsFormatter**: Formats `PerformanceMetrics` for display (peak memory, text summary, serialization)

### 6. Language Parsing Module

#### LanguageDetector (`language_parsing/language_detector.py`)

**Responsibility**: Detects programming language of files

**Detection Methods**:
- File extension matching
- Filename matching (e.g., `Dockerfile`, `Makefile`)
- Language mapping from YAML configuration file

**Input**:
- `languages.yml`: YAML file with language definitions, ex:
  ```yaml
    Python:
    type: programming
    tm_scope: source.python
    ace_mode: python
    codemirror_mode: python
    codemirror_mime_type: text/x-python
    color: "#3572A5"
    extensions:
    - ".py"
    - ".cgi"
    - ".fcgi"
    - ".gyp"
    - ".gypi"
    - ".lmi"
    - ".py3"
    - ".pyde"
    - ".pyi"
    - ".pyp"
    - ".pyt"
    - ".pyw"
    - ".rpy"
    - ".spec"
    - ".tac"
    - ".wsgi"
    - ".xpy"
    filenames:
    - ".gclient"
    - DEPS
    - SConscript
    - SConstruct
    - wscript
    interpreters:
    - python
    - python2
    - python3
    - py
    - pypy
    - pypy3
    - uv
    aliases:
    - python3
    - rusthon
    language_id: 303
    JavaScript:
    type: programming
    tm_scope: source.js
    ace_mode: javascript
    codemirror_mode: javascript
    codemirror_mime_type: text/javascript
    color: "#f1e05a"
    aliases:
    - js
    - node
    extensions:
    - ".js"
    - "._js"
    - ".bones"
    - ".cjs"
    - ".es"
    - ".es6"
    - ".frag"
    - ".gs"
    - ".jake"
    - ".javascript"
    - ".jsb"
    - ".jscad"
    - ".jsfl"
    - ".jslib"
    - ".jsm"
    - ".jspre"
    - ".jss"
    - ".jsx"
    - ".mjs"
    - ".njs"
    - ".pac"
    - ".sjs"
    - ".ssjs"
    - ".xsjs"
    - ".xsjslib"
    filenames:
    - Jakefile
    interpreters:
    - chakra
    - d8
    - gjs
    - js
    - node
    - nodejs
    - qjs
    - rhino
    - v8
    - v8-shell
    language_id: 183
    ```

#### LanguageAnalyzer (`language_parsing/language_analyzer.py`)

**Responsibility**: Analyzes line categories within files

**Line Categories**:
- **Code**: Actual source code lines
- **Comments**: Lines with comments (depends on language)
- **Blank**: Empty or whitespace-only lines

**Detection Logic**:
- Language-specific comment patterns
- Multiline comment handling
- String literal exclusion to avoid false positives

### 7. Data Models (`data/`)

All data models are frozen dataclasses (`@dataclass(frozen=True, slots=True)`) containing only data — no business logic, I/O, or serialization methods.

#### Config (`data/config.py`)
- **Purpose**: Dataclass holding all configuration settings
- **Structure**: Nested sub-dataclasses by functional area (`CoreConfig`, `ScanConfig`, etc.)
- **Usage**: Accessed via `Config.section.field` (e.g., `config.core.color`)

#### Metrics (`data/metrics.py`)
- **Purpose**: Aggregated statistics about analyzed code
- **Fields**:
  - `total_lines`: Sum of all lines
  - `lines_by_language`: Dictionary mapping language → line count
  - `files_by_language`: Count of files per language
  - Timestamp information

#### ScanResult (`data/scan_result.py`)
- **Purpose**: Results from directory scan
- **Fields**:
  - `file_paths`: List of discovered files
  - `total_files`: Count of files
  - `total_bytes`: Total size in bytes

#### ProjectMeta (`data/project_meta.py`)
- **Purpose**: Project metadata for storage and tracking
- **Fields**:
  - Project name and path
  - Scan timestamp
  - Metrics snapshot

#### ComparisonResult (`data/comparison_result.py`)
- **Purpose**: Result of comparing two metric snapshots
- **Fields**:
  - `project1`: Metrics from the first project
  - `project2`: Metrics from the second project
  - `deltas`: Dictionary of computed differences
  - `timestamp`: When the comparison was performed

#### GitInfo (`data/git_info.py`)
- **Purpose**: Git repository metadata for tracked projects
- **Fields**: `is_git_repo`, `remote_url`, `current_branch`, `commit_count`, `contributors`, `last_commit_date`, `branches`, `commits_per_month_all_time`, `commits_last_30_days`

#### PerformanceMetrics (`data/performance_metrics.py`)
- **Purpose**: Performance metrics collected during scan operations
- **Fields**: `peak_memory_bytes`

#### Dependency (`data/dependency.py`)
- **Purpose**: Single dependency entry
- **Fields**: `name`, `version`, `category` (prod/dev/optional), `source_file`

#### DependencyInfo (`data/dependency_info.py`)
- **Purpose**: Aggregated dependency information for a project
- **Fields**: `dependencies` (tuple), `prod_count`, `dev_count`, `optional_count`, `total_count`, `sources`, `conflicts`

#### ProjectFileInfo (`data/project_file_info.py`)
- **Purpose**: Project info extracted from configuration files
- **Fields**: `name`, `dependencies` (DependencyInfo | None), `source_files`

### 8. Storage (`storage/`)

**Responsibility**: Persists and presents scan results for historical tracking

**Architecture**: Separated into persistence and presentation layers

**Persistence Classes**:
- `Storage` (`storage/storage.py`): Coordinates save operations
- `HistoryStorage` (`storage/history_storage.py`): Manages history.json file
- `ProjectMetadataStorage` (`storage/project_metadata_storage.py`): Manages project.json file

**Presentation Classes**:
- `StoragePresenter` (`storage/storage_presenter.py`): Displays stored data (show_* methods)

**Features**:
- Saves metrics to history.json
- Updates project metadata in project.json
- Retrieves historical data for display
- Supports historical trend analysis
- Clean separation of persistence logic from display logic

### 9. Serializers (`serializers/`)

**Responsibility**: Convert data objects to/from dictionary representations

**Classes**:
- `MetricsSerializer`: Serializes/deserializes Metrics dataclass
- `ProjectMetaSerializer`: Serializes/deserializes ProjectMeta dataclass
- `GitInfoSerializer`: Serializes GitInfo to a plain dictionary
- `ProjectInfoSerializer`: Bidirectional serialization for the `Dependency` → `DependencyInfo` → `ProjectFileInfo` hierarchy

**Benefits**:
- Centralized serialization logic
- Removes serialization methods from data classes (maintains SRP)
- Used by storage, comparison, and formatter components

### 10. Dependency Scanning Architecture

**Responsibility**: Analyzes project dependencies across multiple configuration formats and detects version conflicts

**Overview**:
The dependency scanning feature provides cross-format dependency analysis for projects. It scans multiple dependency sources (PyProject, package.json, Cargo.toml, requirements.txt), merges their results, and reports version conflicts.

**Architecture Diagram**:
```
┌────────────────────────────────────────────────────────────────┐
│                    ProjectScanner (core)                       │
│              Orchestrates entire dependency scan               │
└────────────────────┬───────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────────────────────────────────────────────────────┐
    │   Config Readers (config_readers/)                    │
    │   Strategy Pattern for multi-format support           │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ PyProjectReader                              │   │
    │   │ • Reads pyproject.toml                       │   │
    │   │ • Extracts [project.dependencies]            │   │
    │   │ • Extracts optional-dependencies             │   │
    │   │ • Manages version specifications             │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ PackageJsonReader                            │   │
    │   │ • Reads package.json                         │   │
    │   │ • Extracts dependencies                      │   │
    │   │ • Extracts devDependencies                   │   │
    │   │ • Manages version ranges                     │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ CargoTomlReader                              │   │
    │   │ • Reads Cargo.toml                           │   │
    │   │ • Extracts [dependencies]                    │   │
    │   │ • Extracts [dev-dependencies]                │   │
    │   │ • Manages Rust version specs                 │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ RequirementsTxtReader                        │   │
    │   │ • Reads requirements.txt                     │   │
    │   │ • Handles comments and continuations         │   │
    │   │ • Parses complex version specifiers          │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ ConfigReaderFactory                          │   │
    │   │ • Routes to appropriate reader               │   │
    │   │ • Handles reader instantiation               │   │
    │   └──────────────────────────────────────────────┘   │
    └────────────────┬───────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────────┐
    │   ProjectInfoMerger (utils/)                           │
    │   Merges and deduplicates dependencies                 │
    │                                                        │
    │   • Combines dependencies from all sources             │
    │   • Detects version conflicts                          │
    │   • Groups by dependency name                          │
    │   • Categorizes (prod/dev/optional)                    │
    │   • Formats conflict information                       │
    └────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┼────────────────────────────┐
        │            │                            │
        ▼            ▼                            ▼
    ┌────────────────────────────────────────────────────────┐
    │   Data Models (data/)                                  │
    │   Immutable dependency data structures                 │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ Dependency (@dataclass frozen)               │   │
    │   │ • name: str                                  │   │
    │   │ • version: str                               │   │
    │   │ • source_file: str                           │   │
    │   │ • category: "prod"|"dev"|"optional"          │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ DependencyInfo (@dataclass frozen)           │   │
    │   │ • dependencies: tuple[Dependency, ...]       │   │
    │   │ • source_files: tuple[str, ...]              │   │
    │   │ • conflicts: tuple[str, ...]                 │   │
    │   └──────────────────────────────────────────────┘   │
    │                                                        │
    │   ┌──────────────────────────────────────────────┐   │
    │   │ ProjectFileInfo (@dataclass frozen)          │   │
    │   │ • file_path: Path                            │   │
    │   │ • project_name: str | None                   │   │
    │   │ • dependencies: DependencyInfo               │   │
    │   └──────────────────────────────────────────────┘   │
    └────────────────┬───────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────────┐
    │   Formatters (formatters/)                             │
    │   Display dependencies in multiple formats             │
    │                                                        │
    │   • table_formatter.py                                 │
    │     - _create_dependencies_table()                     │
    │     - Displays counts in Rich Table                    │
    │                                                        │
    │   • json_formatter.py                                  │
    │     - Includes "dependencies" key                      │
    │     - Full conflict information preserved              │
    │                                                        │
    │   • markdown_formatter.py                              │
    │     - _format_dependencies()                           │
    │     - Markdown table with source files                 │
    │                                                        │
    │   • summary_formatter.py                               │
    │     - _print_dependencies_info()                       │
    │     - Summary with conflict indicator                  │
    └────────────────────────────────────────────────────────┘
```

**Key Components**:

#### 1. Config Readers (Strategy Pattern)
Each reader implements the same interface for different file formats:

```python
class ConfigReader(Protocol):
    """Base protocol for configuration readers."""
    def read_project_info(self, file_path: Path) -> ProjectFileInfo:
        """Read dependencies from configuration file."""
        ...
```

**Readers**:
- **PyProjectReader**: Parses `pyproject.toml` using `tomllib`
  - Handles PEP 508 version specifiers
  - Separates standard and optional dependencies
  - Caches language definitions for performance

- **PackageJsonReader**: Parses `package.json` using `json`
  - Handles npm/yarn/pnpm formats
  - Separates dependencies and devDependencies
  - Extracts project name from "name" field

- **CargoTomlReader**: Parses `Cargo.toml` using `tomllib`
  - Handles Rust dependency format
  - Separates dependencies and dev-dependencies
  - Extracts project name from package section

- **RequirementsTxtReader**: Parses `requirements.txt` using regex
  - Handles comments and line continuations
  - Parses complex PEP 440 version specifiers
  - Handles extras syntax: `package[extra]>=1.0`

**Factory Pattern**:
```python
class ConfigReaderFactory:
    """Creates appropriate reader based on file type."""
    @staticmethod
    def create_reader(file_path: Path) -> ConfigReader:
        """Route to correct reader based on filename."""
        if file_path.name == "pyproject.toml":
            return PyProjectReader()
        elif file_path.name == "package.json":
            return PackageJsonReader()
        # ... etc
```

#### 2. ProjectScanner (Orchestrator)
Coordinates the entire dependency scanning process:

```python
class ProjectScanner:
    """Scans project for dependencies across all config formats."""

    def scan(self, root_path: Path) -> ProjectFileInfo | None:
        """Scan project and return merged dependency info."""
        # 1. Find all config files
        config_files = self._find_config_files(root_path)

        # 2. Read each file with appropriate reader
        file_infos = self._read_config_files(config_files)

        # 3. Merge results and detect conflicts
        return ProjectInfoMerger.merge(file_infos)
```

**Methods**:
- `_find_config_files()`: Discovers configuration files recursively
- `_read_config_files()`: Applies correct reader to each file
- Uses `ConfigReaderFactory.create_reader()` for routing

#### 3. ProjectInfoMerger (Deduplication & Conflict Detection)
Combines dependencies from multiple sources:

```python
class ProjectInfoMerger:
    """Merges project information and detects conflicts."""

    @staticmethod
    def merge(infos: list[ProjectFileInfo]) -> ProjectFileInfo | None:
        """Combine dependencies and detect conflicts."""
        # 1. Select project name (prefer pyproject.toml)
        project_name = self._select_project_name(infos)

        # 2. Collect all dependencies with deduplication
        all_deps, all_sources = self._collect_all_deps(infos)

        # 3. Detect version conflicts
        conflicts = self._detect_conflicts(all_deps)

        # 4. Build merged DependencyInfo
        return self._build_dep_info(all_deps, all_sources, conflicts)
```

**Conflict Detection**:
- Groups dependencies by name: `dict[str, list[Dependency]]`
- For each group, checks if versions differ
- Formats conflicts as: `"package: version1 (file1.toml) vs version2 (file2.toml)"`
- Returns empty list if no conflicts detected

#### 4. Data Models (Immutable)
All dependency data structures use frozen dataclasses:

```python
@dataclass(frozen=True)
class Dependency:
    """Single dependency entry (immutable)."""
    name: str
    version: str
    source_file: str  # Path to config file
    category: Literal["prod", "dev", "optional"]

@dataclass(frozen=True)
class DependencyInfo:
    """Aggregated dependency information (immutable)."""
    dependencies: tuple[Dependency, ...]
    source_files: tuple[str, ...]  # Unique source files
    conflicts: tuple[str, ...]      # Version conflict descriptions

@dataclass(frozen=True)
class ProjectFileInfo:
    """Project info from single config file (immutable)."""
    file_path: Path
    project_name: str | None
    dependencies: DependencyInfo | None
```

**Benefits**:
- Thread-safe (no mutable state)
- Prevents accidental modification
- Clear data contracts
- Serializable to JSON/YAML

#### 5. Integration with Metrics & Formatters

**Data Flow**:
```
ProjectScanner
    ↓
ProjectFileInfo (if config found)
    ↓
ScanHandler stores in context
    ↓
Formatter receives dependencies
    ↓
Display: table/json/markdown/summary
```

**Formatter Integration**:
Each formatter checks `if metrics.dependencies is not None`:
- **TableFormatter**: Creates Rich Table with dependency counts
- **JsonFormatter**: Adds "dependencies" key to output
- **MarkdownFormatter**: Adds "Dependencies" section with details
- **SummaryFormatter**: Shows brief dependency summary with conflicts

**CLI Flag**:
```bash
statsvy scan /path --no-deps  # Disable dependency scanning
```

---

## Data Flow

### Typical Scan Operation

```
1. User runs: statsvy scan /path --format json

2. CLI Layer (cli_main.py)
   ├─ Parse arguments via Click
   ├─ Load configuration (ConfigLoader)
   │  ├─ ConfigFileReader reads pyproject.toml
   │  ├─ ConfigEnvReader reads STATSVY_* env vars
   │  └─ ConfigValueConverter converts types
   ├─ Create ScanHandler with config
   └─ Delegate to ScanHandler.execute()

3. ScanHandler Orchestration (cli/scan_handler.py)
   ├─ Resolve target directory (PathResolver)
   ├─ Initialize Scanner with path
   └─ Coordinate workflow:

4. Scanner Phase (core/scanner.py)
   ├─ Traverse directory tree
   ├─ Apply .gitignore rules
   └─ Return ScanResult (files list, totals)

5. Analyzer Phase (core/analyzer.py)
   ├─ For each file in ScanResult:
   │  ├─ Detect language (LanguageDetector)
   │  ├─ Analyze line categories (LanguageAnalyzer)
   │  └─ Accumulate statistics
   └─ Return Metrics

6. Optional Git Stats (core/git_stats.py)
   ├─ If enabled: Calculate git-specific metrics
   └─ Merge into main Metrics

7. Storage Phase (storage/)
   ├─ If not --no-save: Storage.save()
   │  ├─ HistoryStorage appends to history.json
   │  ├─ ProjectMetadataStorage updates project.json
   │  └─ Uses MetricsSerializer for serialization
   └─ Creates timestamped entry

8. Formatting Phase (core/formatter.py → formatters/)
   ├─ Formatter.format(metrics, "json")
   ├─ Route to JsonFormatter
   └─ Serialize Metrics to JSON string

9. Output Phase (utils/output_handler.py)
   ├─ OutputHandler.handle(formatted_output)
   ├─ Write to console or file
   └─ If --output: Save to specified path
```

## Extension Points

### Adding a New Output Format

1. Create new formatter in `formatters/new_formatter.py`:
   ```python
   class NewFormatter:
       def format(self, metrics: Metrics) -> str:
           # Implementation
           return formatted_string
   ```

2. Register in `core/formatter.py`:
   ```python
   elif format_type == "new_format":
       return NewFormatter().format(metrics)
   ```

### Adding Language Support

1. Update `assets/languages.yml`:
   ```yaml
   MyLanguage:
     extensions: ['.ml', '.mli']
     filenames: []
   ```

2. Add line-counting logic to `LanguageAnalyzer` if needed

### Adding Configuration Options

1. Add to appropriate section in `data/config.py`:
   ```python
   my_section: ClassVar[dict] = {
       "my_option": default_value
   }
   ```

2. CLI args are auto-discovered and merged by `ConfigLoader`

## Testing Strategy

**Test Organization**:
- `tests/analyzer/`: Analyzer class tests
- `tests/cli/`: CLI command and argument tests
- `tests/comparison/`: Comparison analyzer and formatter tests
- `tests/config_loader/`: Config loading and merging
- `tests/config_readers/`: Dependency config reader tests
- `tests/core/`: Core component tests
- `tests/data/`: Data model tests
- `tests/formatter/`: Formatter coordinator tests
- `tests/formatters/`: Individual formatter tests
- `tests/language_parsing/`: Language detection tests
- `tests/project/`: Project tracking tests
- `tests/scanner/`: Scanner functionality
- `tests/serializers/`: Serializer tests
- `tests/storage/`: Storage and persistence
- `tests/utils/`: Utility function tests

**Test Coverage**:
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Configuration priority tests
- Format validation tests

**Running Tests**:
```bash
pytest                                      # Run all tests
pytest --cov=statsvy --cov-report=html    # With coverage report
just test                                   # Using justfile
```

## Dependencies

**Core Dependencies**:
- `click`: CLI framework
- `rich`: Terminal styling and progress bars
- `pyyaml`: Configuration parsing
- `gitpython`: Git integration
- `pygments`: Syntax highlighting support

**Development Dependencies**:
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `ruff`: Linting and formatting
- `mypy`: Type checking (via `ty`)
- `pre-commit`: Git hooks

## Performance Considerations

1. **Progress Reporting**: Rich progress bars provide feedback for large scans
2. **Lazy Loading**: Language detection happens per-file efficiently
3. **Gitignore Parsing**: Cached and reused across all files
4. **Memory Efficiency**: Files streamed and aggregated rather than loaded entirely
5. **Configurable Limits**: Max file size and scan depth prevent runaway analysis

## Future Architecture Improvements

- [ ] Plugin system for custom analyzers
- [ ] Parallel file processing for large codebases
- [ ] Database backend for historical data (currently file-based)
- [ ] Web UI for visualization and comparison
- [ ] Advanced metrics (cyclomatic complexity, duplication detection)
- [ ] Incremental scanning for faster re-scans
- [ ] Language-specific AST analysis for more accurate metrics
