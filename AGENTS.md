# Development Agent Guidelines

This document outlines the strict coding standards and programming rules required for all contributions to the Statsvy project. Any code written for this project—whether by human developers, AI assistants, or automated tools—must adhere to these guidelines.

## Table of Contents

1. [General Programming Best Practices](#general-programming-best-practices)
2. [Architecture & Module Design](#architecture--module-design)
3. [Python Version & Environment](#python-version--environment)
4. [Code Style & Formatting](#code-style--formatting)
5. [Type Checking & Annotations](#type-checking--annotations)
6. [Documentation & Comments](#documentation--comments)
7. [Testing Requirements](#testing-requirements)
8. [Code Complexity & Performance](#code-complexity--performance)
9. [Import Organization](#import-organization)
10. [Error Handling](#error-handling)
11. [Security Practices](#security-practices)
12. [Git & Commit Practices](#git--commit-practices)

---

## General Programming Best Practices

These principles apply universally across all programming languages and are fundamental to writing maintainable, robust, and secure code.

### 1. Immutability as Default

**Principle**: Data should be immutable by default unless mutability is explicitly necessary.

**Benefits**:
- Easier to reason about code (values don't change unexpectedly)
- Thread-safe without locks
- Enables functional programming patterns
- Reduces bugs from unexpected state changes

**Python Implementation**:

```python
# ✅ CORRECT - Use immutable types as default
from dataclasses import dataclass

@dataclass(frozen=True)  # Make dataclass immutable
class ScanResult:
    """Immutable result object."""
    file_paths: tuple[str, ...]  # Use tuple, not list
    total_files: int
    total_bytes: int

# For mutable collections, prefer copying and returning new instances
def add_config_option(config: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Return new config dict instead of modifying original."""
    new_config = config.copy()
    new_config[key] = value
    return new_config

# ❌ WRONG - Mutating input parameters
def add_config_option(config: dict[str, Any], key: str, value: Any) -> None:
    """Don't modify input parameters."""
    config[key] = value  # Side effect on caller's data
```

**Guidelines**:
- Use `dataclass(frozen=True)` for immutable data objects
- Use `tuple` instead of `list` when content shouldn't change
- Use `frozenset` instead of `set` when set shouldn't change
- Prefer returning new objects over mutating inputs
- Document when functions intentionally mutate state

---

## Architecture & Module Design

### 1. Data and Logic Separation

**Principle**: Data models and logic should be strictly separated. Data classes (`@dataclass`) should contain only data; business logic should reside in separate classes or modules.

**Benefits**:
- Clear distinction between data structures and behavior
- Easier to understand and reason about code
- Simple serialization and transformation of data
- Better testability (test data independently from logic)
- Reduced coupling between components

**Python Implementation**:

```python
# ❌ WRONG - Mixing data and logic in dataclass
@dataclass
class Metrics:
    """Data mixed with logic."""
    total_lines: int
    lines_by_language: dict[str, int]

    def calculate_percentage(self, language: str) -> float:
        """Logic embedded in data class."""
        return (self.lines_by_language[language] / self.total_lines) * 100

    def to_json(self) -> str:
        """Serialization logic in data class."""
        return json.dumps(asdict(self))

# ❌ WRONG - Data class doing analysis
@dataclass
class Config:
    debug: bool
    verbose: bool

    def load_from_file(self, path: str) -> None:
        """Loading logic in data class."""
        with open(path) as f:
            data = json.load(f)
        # mutate self

# ✅ CORRECT - Data class holds only data
@dataclass(frozen=True)
class Metrics:
    """Pure data structure - immutable."""
    total_lines: int
    lines_by_language: dict[str, int]
    timestamp: datetime

# ✅ CORRECT - Logic in separate class
class MetricsAnalyzer:
    """Handles logic and transformations of metrics."""

    @staticmethod
    def calculate_percentage(metrics: Metrics, language: str) -> float:
        """Logic separate from data."""
        return (metrics.lines_by_language[language] / metrics.total_lines) * 100

# ✅ CORRECT - Serialization in separate class
class MetricsSerializer:
    """Handles conversion of Metrics to different formats."""

    @staticmethod
    def to_json(metrics: Metrics) -> str:
        return json.dumps(asdict(metrics))

    @staticmethod
    def to_dict(metrics: Metrics) -> dict[str, Any]:
        return asdict(metrics)

# ✅ CORRECT - Configuration loading separate from data
@dataclass(frozen=True)
class Config:
    """Pure configuration data."""
    debug: bool
    verbose: bool
    max_size: int

class ConfigLoader:
    """Handles loading and merging configuration from multiple sources."""

    def load_from_file(self, path: str) -> Config:
        """Loads config and returns new Config instance."""
        with open(path) as f:
            data = json.load(f)
        return Config(**data)
```

**Guidelines**:
- `@dataclass` should only define fields and use `__init__`, `__repr__`, `__eq__` (auto-generated)
- No business logic methods in data classes
- No I/O operations in data classes (file/network access)
- No state mutation methods in data classes
- Create separate classes with names ending in `...Processor`, `...Analyzer`, `...Formatter`, `...Loader` to handle logic
- Prefer immutable dataclasses with `frozen=True`

### 2. Core Module as Coordinator

**Principle**: The `core/` module contains orchestrators/coordinators that delegate to specialized modules. If a component violates Single Responsibility Principle (SRP), it should be extracted to a separate module that `core/` coordinates.

**Benefits**:
- Clear orchestration of workflow
- Prevents core from becoming a monolith
- Easier to add new functionality by creating new modules
- Maintains clean dependency flow

**Structure**:
```
cli/                               # Command handlers and orchestrators
├── scan_handler.py                # Orchestrates scan command workflow
└── compare_handler.py             # Orchestrates compare command workflow

config/                            # Configuration management (decomposed)
├── config_loader.py               # Coordinates config from multiple sources
├── config_file_reader.py          # Reads TOML configuration files
├── config_env_reader.py           # Reads STATSVY_* environment variables
└── config_value_converter.py     # Converts and validates config values

core/                              # Core coordinators (orchestrates logic)
├── analyzer.py                    # Coordinates language detection & analysis
├── formatter.py                   # Coordinates output formatting
├── git_stats.py                   # Git repository metrics
├── project.py                     # Project tracking (with strategy pattern)
├── project_config_readers.py      # Strategy pattern for project configs
└── scanner.py                     # Coordinates file discovery

storage/                           # Persistence and presentation (decomposed)
├── storage.py                     # Coordinates save operations
├── history_storage.py             # Manages history.json file
├── project_metadata_storage.py   # Manages project.json file
└── storage_presenter.py           # Presentation layer (show_* commands)

serializers/                       # Serialization logic (separated from data/)
├── metrics_serializer.py          # Serializes/deserializes Metrics
└── project_meta_serializer.py    # Serializes/deserializes ProjectMeta

language_parsing/                  # Specialized logic (coordinated by analyzer)
├── language_analyzer.py           # Analyzes line categories
└── language_detector.py           # Detects language

formatters/                        # Specific formatters (coordinated by core/formatter.py)
├── json_formatter.py
├── markdown_formatter.py
├── table_formatter.py
├── history_formatter.py
└── summary_formatter.py

utils/                             # Utilities extracted from other modules
├── console.py                     # Rich console wrapper
├── output_handler.py              # Handles output to file or console
└── path_resolver.py               # Resolves target directory for scanning
```

**When to Extract**:
If you add functionality to `core/` that:
1. Has its own specialized logic not needed by coordinators
2. Could be reused independently
3. Would be easier to test in isolation
4. Makes the coordinator file grow significantly

→ Extract it to a separate module and have `core/` coordinate it.

**Example**:
```python
# ❌ WRONG - Core module with too many responsibilities
class Analyzer:
    def analyze(self, scan_result: ScanResult) -> Metrics:
        # Detects language
        language = self._detect_language(file_path)  # Gets mixed in
        # Counts lines
        code_lines = self._count_code_lines(content)  # Gets mixed in
        # Calculates percentages
        percentage = self._calculate_percentage(...)  # Gets mixed in
        # Much more logic...

# ✅ CORRECT - Core orchestrates specialized modules
class Analyzer:
    """Orchestrates language detection and analysis."""

    def __init__(self, language_detector: LanguageDetector, language_analyzer: LanguageAnalyzer):
        self.language_detector = language_detector
        self.language_analyzer = language_analyzer

    def analyze(self, scan_result: ScanResult) -> Metrics:
        """Coordinates detection and analysis."""
        metrics = {}
        for file_path in scan_result.file_paths:
            language = self.language_detector.detect(file_path)  # Delegate
            analysis = self.language_analyzer.analyze(file_path, language)  # Delegate
            metrics[language] = analysis
        return Metrics(metrics)
```

---

### 3. File Organization and Class Boundaries

**Principle**: Each file should contain at most one class. Helper classes or "private" classes should be extracted to their own files. The rule of thumb is that each file should be named after the class it contains.

**Benefits**:
- Clear file-to-class mapping makes navigation intuitive
- Easier to locate and understand class responsibilities
- Prevents files from becoming bloated with multiple concerns
- Encourages proper separation of concerns
- Simplifies imports and dependency tracking
- Better granularity for version control

**Python Implementation**:

```python
# ❌ WRONG - Multiple classes in one file
# file: metrics.py
@dataclass(frozen=True)
class Metrics:
    """Main metrics data."""
    total_lines: int
    lines_by_language: dict[str, int]

class _MetricsHelper:  # "Private" helper class
    """Helper for metrics calculations."""
    @staticmethod
    def calculate_percentage(total: int, part: int) -> float:
        return (part / total) * 100

class MetricsCache:  # Another class in same file
    """Cache for metrics."""
    def __init__(self) -> None:
        self._cache: dict[str, Metrics] = {}

# ✅ CORRECT - One class per file
# file: metrics.py
@dataclass(frozen=True)
class Metrics:
    """Main metrics data."""
    total_lines: int
    lines_by_language: dict[str, int]

# file: metrics_calculator.py
class MetricsCalculator:
    """Handles metrics calculations."""
    @staticmethod
    def calculate_percentage(total: int, part: int) -> float:
        """Calculate percentage of part from total."""
        return (part / total) * 100

# file: metrics_cache.py
class MetricsCache:
    """Cache for storing and retrieving metrics."""
    def __init__(self) -> None:
        self._cache: dict[str, Metrics] = {}
```

**Naming Convention**:
- File name should match class name in snake_case: `MetricsCalculator` → `metrics_calculator.py`
- Class name should be in PascalCase: `LanguageDetector`, `FileScanner`
- Avoid generic names like `helpers.py` or `utils.py` with multiple classes

**Exceptions**:
While the one-class-per-file rule is strongly preferred, there are rare acceptable exceptions:
- **Tightly coupled error classes**: Custom exception classes that are only used by one specific class may reside in the same file
  ```python
  # file: scanner.py
  class ScanError(Exception):
      """Error specific to Scanner operations."""
      pass

  class Scanner:
      """Main scanner class."""
      def scan(self, path: str) -> ScanResult:
          if not path:
              raise ScanError("Path cannot be empty")
  ```
- **Type aliases and protocols**: Type definitions used only within one class may stay in the same file
  ```python
  # file: formatter.py
  from typing import Protocol

  class Formattable(Protocol):
      """Protocol for objects that can be formatted."""
      def to_dict(self) -> dict[str, Any]: ...

  class Formatter:
      """Formats objects that implement Formattable."""
      def format(self, obj: Formattable) -> str: ...
  ```

**Guidelines**:
- When you find a "helper" class, ask: "Does this have its own responsibility?" If yes, extract it
- If a class is only used by one other class, consider if it should be composed into the main class or extracted
- Prefer descriptive file names over generic ones (`language_detector.py` not `utils.py`)
- Keep the file organization flat when possible; don't create nested helper modules unnecessarily

---

### 4. Avoid Global Variables

**Principle**: Global variables should be avoided. Use dependency injection, class attributes, or function parameters instead.

**Problems with globals**:
- Hidden dependencies (hard to understand what a function needs)
- Difficult to test (can't isolate state)
- Thread-safety issues
- Name collisions and namespace pollution
- Hard to track where variables are modified

**Python Implementation**:

```python
# ❌ WRONG - Global variable
config = {}  # Global state

def scan(path: str) -> None:
    """This function secretly depends on global config."""
    ignore_patterns = config.get("ignore_patterns", [])
    # ... rest of implementation

# ❌ WRONG - Global state modified in functions
CACHE = {}

def get_data(key: str) -> Any:
    if key in CACHE:
        return CACHE[key]
    result = expensive_operation(key)
    CACHE[key] = result  # Modifying global
    return result

# ✅ CORRECT - Dependency injection
class Scanner:
    """Scanner with explicit configuration dependency."""

    def __init__(self, config: Config) -> None:
        """Accept configuration as parameter."""
        self.config = config

    def scan(self, path: str) -> ScanResult:
        """Use instance configuration, not global state."""
        ignore_patterns = self.config.scan["ignore_patterns"]
        # ... rest of implementation

# ✅ CORRECT - Function parameters
def scan_directory(path: str, config: Config) -> ScanResult:
    """Explicit parameters make dependencies clear."""
    ignore_patterns = config.scan["ignore_patterns"]
    # ... rest of implementation

# ✅ CORRECT - Class-based caching
class DataCache:
    """Encapsulate cache state in a class."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def get(self, key: str, loader: Callable[[str], Any]) -> Any:
        """Get data, loading if not cached."""
        if key not in self._cache:
            self._cache[key] = loader(key)
        return self._cache[key]
```

**Exceptions**:
- Configuration constants (but prefer dependency injection over globals)
- Logger instances (standard practice)
- Module-level imports are preferred

### 5. Static Methods for Pure Functions

**Principle**: If a method doesn't use `self` or `cls`, it should be a `@staticmethod` or a module-level function.

**Benefits**:
- Signals that the function is stateless and pure
- Can be called without instantiating the class
- Easier to test and understand
- Better for functional composition

**Python Implementation**:

```python
# ❌ WRONG - Method that doesn't use self
class FileAnalyzer:
    def is_valid_extension(self, path: str) -> bool:
        """This method doesn't use self but is still an instance method."""
        return path.endswith((".py", ".js", ".ts"))

# ❌ WRONG - Better as a module function
def is_valid_extension(path: str) -> bool:
    return path.endswith((".py", ".js", ".ts"))
analyzer = FileAnalyzer()
result = analyzer.is_valid_extension("file.py")  # Weird API

# ✅ CORRECT - Use @staticmethod for utility functions within class
class FileAnalyzer:
    VALID_EXTENSIONS = (".py", ".js", ".ts")

    @staticmethod
    def is_valid_extension(path: str) -> bool:
        """Static method for pure utility function."""
        return path.endswith(FileAnalyzer.VALID_EXTENSIONS)

# Use without instantiation
if FileAnalyzer.is_valid_extension("file.py"):
    # ... process file

# ✅ CORRECT - Module-level function (often better than @staticmethod)
def is_valid_extension(path: str) -> bool:
    """Pure function at module level."""
    return path.endswith((".py", ".js", ".ts"))

if is_valid_extension("file.py"):
    # ... process file

# ✅ CORRECT - Use @classmethod when needing class context
class Config:
    _instance: Config | None = None

    @classmethod
    def get_instance(cls) -> Config:
        """Factory method using class context."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### 6. Single Responsibility Principle (SRP)

**Principle**: Each function/class should have exactly one reason to change.

**Benefits**:
- Easier to understand
- Easier to test
- Easier to modify
- Reduces code coupling

```python
# ❌ WRONG - Multiple responsibilities
class FileProcessor:
    """Does too much: reading, parsing, analyzing, formatting, storing."""

    def process_file(self, path: str, output_format: str) -> None:
        # Read from disk
        with open(path) as f:
            content = f.read()

        # Parse file
        lines = content.split("\n")

        # Analyze
        metrics = self._calculate_metrics(lines)

        # Format
        formatted = self._format_output(metrics, output_format)

        # Store
        self._save_output(formatted, output_format)

# ✅ CORRECT - Separate concerns
class FileReader:
    """Responsibility: Read files from disk."""
    def read(self, path: str) -> str:
        with open(path) as f:
            return f.read()

class FileAnalyzer:
    """Responsibility: Analyze file content."""
    def analyze(self, content: str) -> Metrics:
        lines = content.split("\n")
        return self._calculate_metrics(lines)

class MetricsFormatter:
    """Responsibility: Format metrics for output."""
    def format(self, metrics: Metrics, format_type: str) -> str:
        # Delegation to specific formatters
        return self._get_formatter(format_type).format(metrics)

class MetricsStorage:
    """Responsibility: Store metrics persistently."""
    def save(self, metrics: Metrics, path: str) -> None:
        # Save to storage
        pass
```

### 7. Fail Fast

**Principle**: Detect and report errors as early as possible.

**Benefits**:
- Easier debugging (error occurs near root cause)
- Prevents invalid state propagation
- Clearer error messages

```python
# ❌ WRONG - Fails silently or late
def process_config(config: dict[str, Any]) -> None:
    max_size = config.get("max_size", 100)  # Could be wrong type
    timeout = config.get("timeout", 30)  # Could be wrong type
    # ... much later might fail when used

# ✅ CORRECT - Validate inputs early
def process_config(config: dict[str, Any]) -> None:
    _validate_config(config)
    max_size = config["max_size"]
    timeout = config["timeout"]
    # ...

def _validate_config(config: dict[str, Any]) -> None:
    """Validate configuration is correct."""
    if "max_size" not in config:
        raise ValueError("config missing required key: max_size")
    if not isinstance(config["max_size"], int):
        raise TypeError(f"max_size must be int, got {type(config['max_size'])}")
    if config["max_size"] <= 0:
        raise ValueError(f"max_size must be positive, got {config['max_size']}")
```

### 8. Don't Repeat Yourself (DRY)

**Principle**: Every piece of knowledge should exist in exactly one place.

**Problems with repetition**:
- Bugs fixed in one place are not fixed everywhere
- Changes require updating multiple locations
- Harder to maintain consistency

```python
# ❌ WRONG - Repeated validation logic
def create_user(name: str) -> User:
    if not name or len(name) < 3:
        raise ValueError("Name too short")
    if not name or len(name) > 100:
        raise ValueError("Name too long")
    return User(name)

def update_user(user: User, new_name: str) -> User:
    if not new_name or len(new_name) < 3:
        raise ValueError("Name too short")
    if not new_name or len(new_name) > 100:
        raise ValueError("Name too long")
    user.name = new_name
    return user

# ✅ CORRECT - Extract common logic
def _validate_name(name: str) -> None:
    """Validate name meets requirements."""
    if not name:
        raise ValueError("Name cannot be empty")
    if len(name) < 3:
        raise ValueError("Name too short (min 3 characters)")
    if len(name) > 100:
        raise ValueError("Name too long (max 100 characters)")

def create_user(name: str) -> User:
    _validate_name(name)
    return User(name)

def update_user(user: User, new_name: str) -> User:
    _validate_name(new_name)
    user.name = new_name
    return user
```

### 9. Composition Over Inheritance

**Principle**: Prefer object composition over class inheritance.

**Benefits**:
- More flexible (can combine behaviors dynamically)
- Avoids deep inheritance hierarchies
- Easier to understand (explicit over implicit)
- Avoids fragile base class problem

```python
# ❌ WRONG - Deep inheritance hierarchy (fragile)
class Analyzer(LanguageDetector, LineCounter, MetricsCalculator):
    """Multiple inheritance creates coupling and complexity."""
    pass

# ✅ CORRECT - Composition
class Analyzer:
    """Analyzer composed of focused components."""

    def __init__(
        self,
        language_detector: LanguageDetector,
        line_counter: LineCounter,
        metrics_calculator: MetricsCalculator,
    ) -> None:
        self.language_detector = language_detector
        self.line_counter = line_counter
        self.metrics_calculator = metrics_calculator

    def analyze(self, content: str) -> Metrics:
        """Use composed components."""
        language = self.language_detector.detect(content)
        lines = self.line_counter.count(content, language)
        return self.metrics_calculator.calculate(lines)
```

### 10. Explicit Over Implicit

**Principle**: Code should be clear and obvious. Don't rely on magic or hidden behavior.

```python
# ❌ WRONG - Implicit behavior
class Result:
    def __bool__(self) -> bool:
        """Implicit conversion makes it unclear."""
        return len(self.data) > 0

if result:  # What does this mean? Not clear without reading implementation
    process(result)

# ✅ CORRECT - Explicit
class Result:
    def has_data(self) -> bool:
        """Explicit and clear."""
        return len(self.data) > 0

if result.has_data():
    process(result)
```

### 11. YAGNI - You Aren't Gonna Need It

**Principle**: Don't add functionality until it's actually needed.

**Problems with over-engineering**:
- Unnecessary complexity
- Code that's never used
- Harder to maintain
- Slower development

```python
# ❌ WRONG - Over-engineered for potential future use
class Scanner:
    def scan(self, path: str, strategy: ScanStrategy = None) -> ScanResult:
        """Supports multiple scan strategies (never used)."""
        if strategy is None:
            strategy = DefaultScanStrategy()
        # ... complex implementation

# ✅ CORRECT - Simple and focused
class Scanner:
    def scan(self, path: str) -> ScanResult:
        """Simple implementation for current needs."""
        # ... straightforward implementation
```

---

## Python Version & Environment

### Version Requirements

- **Minimum Python**: 3.12 or higher
- **Target Version**: Python 3.12 (as specified in `pyproject.toml`)
- All code must be compatible with Python 3.12+ features and syntax

### Dependencies

- Only use dependencies listed in `pyproject.toml`
- Do not add new dependencies without explicit justification and approval
- Keep dependencies up-to-date but compatible with the project's constraint strategy
- For development/type-checking tools: use the versions specified in `[project.optional-dependencies.dev]`

---

## Code Style & Formatting

### Formatter: Ruff

All Python code **must** be formatted using [Ruff](https://github.com/astral-sh/ruff).

**Configuration** (from `pyproject.toml`):
```toml
[tool.ruff]
line-length = 88
target-version = "py312"
exclude = ["typings"]
```

### Line Length

- **Maximum line length**: 88 characters
- This applies to code, strings, comments, and documentation
- Long imports, URLs, or strings that cannot be split are acceptable exceptions

### Formatting Rules

**Command to apply formatting**:
```bash
uv run ruff format .
```

**Automatic Formatting Includes**:
- Consistent indentation (4 spaces, never tabs)
- Consistent quote style (double quotes preferred)
- Whitespace normalization
- Import sorting (see [Import Organization](#import-organization))
- Trailing comma and parenthesis formatting

### Blank Lines

- Two blank lines between top-level class and function definitions
- One blank line between method definitions
- One blank line after imports block
- No trailing blank lines at end of file

---

## Linting & Code Quality

### Enabled Ruff Rules

The following rule categories are **strictly enforced**:

```
E    - PEP 8 errors (all)
F    - PyFlakes (all)
I    - isort (import sorting)
N    - PEP 8 naming conventions
W    - PEP 8 warnings
B    - flake8-bugbear
C90  - McCabe complexity
PL   - Pylint
SIM  - flake8-simplify
ARG  - flake8-unused-arguments
ANN  - flake8-annotations (type hints)
D    - pydocstyle (docstring style)
S    - bandit (security)
T20   - flake8-print (no raw print statements)
UP   - pyupgrade
ERA   - eradicate (dead code removal)
RUF  - Ruff-specific rules
```

### Ignored Rules (Exceptions)

The following rules are explicitly ignored:

| Rule | Reason |
|------|--------|
| `D104` | Package init docstrings not required |
| `S101` | Assert statements allowed in tests |
| `S105` | Test credentials in test files acceptable |

**Command to run linting with auto-fixes**:
```bash
uv run ruff check . --fix
```

### Manual Code Review

Before commits, verify:
- No unused imports
- No unused variables (`ARG` rule)
- No shadowing of built-in names
- All `print()` statements justified with comments explaining why logging isn't used
- Complexity levels within limits (see [Code Complexity](#code-complexity--performance))

---

## Type Checking & Annotations

### Type Annotation Standards

**All functions must have complete type annotations**:

```python
# ✅ CORRECT
def analyze_file(path: Path, verbose: bool = False) -> Metrics:
    """Analyze a file and return metrics."""
    ...

# ❌ WRONG - missing return type
def analyze_file(path: Path, verbose: bool = False):
    ...

# ❌ WRONG - missing parameter type
def analyze_file(path, verbose: bool = False) -> Metrics:
    ...
```

### Type Checker: ty

**Configuration**:
```toml
[tool.ty.rules]
all = "error"

[tool.ty.src]
exclude = ["typings"]
```

**Command to run type checking**:
```bash
uv run ty check
```

**Rules**:
- All errors reported by ty must be fixed (no `type: ignore` without justification)
- Use `type: ignore` comments sparingly, with explanatory comments
- Generic types must be properly parameterized: `dict[str, int]` not `dict`
- Use `Optional[T]` or `T | None` (Python 3.10+ style preferred)
- Return type must never be missing (use `None` if function returns nothing)

### Type Hints Checklist

- [x] All function parameters have types
- [x] All function returns have types
- [x] Class attributes have types (or are inferred)
- [x] Variables have types (or are inferred)
- [x] Function/method arguments use proper type hints
- [x] Complex types use type aliases: `type ScanResult = dict[str, Any]`
- [x] Union types: prefer `T | U` syntax over `Union[T, U]`

---

## Documentation & Comments

### Docstring Style: Google

All public classes, functions, and methods **must** have docstrings in english following the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

**Ruff Configuration**:
```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

### Module-Level Docstrings

**Required** for all modules:

```python
"""Core scanning functionality for directory analysis.

This module provides the Scanner class which recursively traverses
directories and collects file statistics.
"""

import os
from pathlib import Path
```

### Class Docstrings

**Required** for all public classes:

```python
class Scanner:
    """Recursively scans directories for file statistics.

    This class traverses directory trees, respects .gitignore patterns,
    and calculates file and size statistics.

    Attributes:
        root_path (Path): The root directory to scan.
        ignore (tuple[str, ...]): Glob patterns to exclude.
    """
```

### Function/Method Docstrings

**Required** for all public functions and methods:

```python
def scan(self, max_depth: int = -1) -> ScanResult:
    """Scan the directory tree and return statistics.

    Recursively traverses the directory structure, respecting ignore
    patterns and .gitignore rules.

    Args:
        max_depth: Maximum directory depth to traverse.
            Defaults to -1 (unlimited).

    Returns:
        ScanResult: Object containing file list, count, and total bytes.

    Raises:
        ValueError: If root_path is not a valid directory.
        TimeoutError: If scan takes longer than configured timeout.
    """
```

### Docstring Sections

Use these sections in this order:
1. **Summary**: One-line description
2. **Longer description** (if needed): Additional context
3. **Args**: Parameter descriptions with types
4. **Returns**: Return value description
5. **Raises**: Exceptions that may be raised
6. **Examples** (if appropriate):
   ```python
   Example:
       >>> scanner = Scanner("/path/to/project")
       >>> result = scanner.scan()
       >>> print(result.total_files)
   ```

### Inline Comments

- Use inline comments to explain **why**, not **what**
- Keep comments short and clear
- Update comments when code changes

```python
# ✅ CORRECT - explains reasoning
# Skip binary files as they don't contain readable source code
if file.suffix in BINARY_EXTENSIONS:
    continue

# ❌ WRONG - just restates the code
# Check if file is binary
if file.suffix in BINARY_EXTENSIONS:
```

### TODO Comments

Mark work-in-progress with structured TODO comments:

```python
# TODO: Implement parallel file processing for performance
# See issue #42 for requirements
def analyze_files(files: list[Path]) -> Metrics:
    ...
```

---

## Testing Requirements

### Coverage Minimum

- **Code coverage minimum**: 90%
- **Command**: `uv run pytest -v --cov=statsvy --cov-report=term-missing --cov-fail-under=90`
- Coverage must not decrease with new code

### Test File Organization

- One folder per source file
- Tests with multiple classes are split: one class per file
- Ex:
```
tests/
├── analyzer/          # Analyzer class tests
├── cli/               # CLI command tests
├── config_loader/     # Configuration loading tests
├── formatters/        # Output formatter tests
├── language_parsing/  # Language detection tests
├── scanner/           # Scanner functionality tests
└── storage/           # Storage and persistence tests
```

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality_description>()`
- Test classes (if organizing): `Test<ClassName>`

```python
# ✅ CORRECT
def test_scanner_respects_gitignore_patterns():
    """Scanner should skip files matching .gitignore patterns."""
    ...

def test_analyzer_calculates_total_lines_correctly():
    """Metrics should contain accurate line counts."""
    ...

# ❌ WRONG
def test_scanner():
    """Test scanner."""
    ...
```

### Test Quality Standards

- Each test should test **one thing**
- Use descriptive assertion messages
- Use fixtures from `conftest.py` to reduce duplication
- Mock external dependencies (file I/O, network calls)
- Include both happy path and failure cases

```python
def test_scanner_raises_on_invalid_path():
    """Scanner should raise ValueError for non-existent paths."""
    with pytest.raises(ValueError, match="does not exist"):
        Scanner("/invalid/path/that/does/not/exist")
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=statsvy --cov-report=term-missing

# Run specific test file
uv run pytest tests/scanner/test_basic_scanning.py

# Run specific test
uv run pytest tests/scanner/test_basic_scanning.py::test_scanner_finds_files

# Run tests matching pattern
uv run pytest -k "scanner"
```

---

## Code Complexity & Performance

### McCabe Complexity

**Maximum cyclomatic complexity**: 7

**Configuration**:
```toml
[tool.ruff.lint.mccabe]
max-complexity = 7
```

**What counts as complexity**:
- `if` / `elif` / `else` statements
- `for` / `while` loops
- `try` / `except` / `finally` blocks
- Boolean operators (`and`, `or`) in conditionals

**Refactoring strategies**:
- Extract methods for complex conditional logic
- Use early returns to reduce nesting
- Consider strategy or state patterns for multiple branches

```python
# ❌ TOO COMPLEX (complexity > 7)
def process_file(file: Path) -> str:
    if file.exists():
        if file.is_file():
            if file.suffix in VALID_EXTENSIONS:
                if file.stat().st_size < MAX_SIZE:
                    content = file.read_text()
                    if content:
                        if is_source_file(content):
                            return analyze(content)
    return ""

# ✅ REFACTORED (complexity = 3)
def process_file(file: Path) -> str:
    """Process a single file with validation."""
    if not _is_valid_file(file):
        return ""
    content = file.read_text()
    return analyze(content) if is_source_file(content) else ""

def _is_valid_file(file: Path) -> bool:
    """Check if file meets all validation criteria."""
    return (
        file.exists()
        and file.is_file()
        and file.suffix in VALID_EXTENSIONS
        and file.stat().st_size < MAX_SIZE
    )
```

### Pylint Configuration

```toml
[tool.ruff.lint.pylint]
max-args = 5          # Functions should take 5 or fewer arguments
max-branches = 10     # 10 or fewer branches per function
max-returns = 5       # 5 or fewer return statements per function
max-statements = 30   # 30 or fewer statements per function
```

Violation strategy: Refactor rather than attempt workarounds.

---

## Import Organization

### Import Order

Imports must be organized in this order (enforced by Ruff):

1. **Standard library imports**
2. **Third-party imports**
3. **Local imports** (from this package)

```python
# ✅ CORRECT
from pathlib import Path
from typing import Any

import click
from rich import inspect

from statsvy.data.metrics import Metrics
from statsvy.utils.console import console
```

```python
# ❌ WRONG - mixed order
from statsvy.data.metrics import Metrics
from pathlib import Path
import click
from rich import inspect
```

### Import Style

- Use absolute imports: `from statsvy.core import Analyzer`
- No relative imports: ✅ `from statsvy.core.analyzer import Analyzer` vs ❌ `from .analyzer import Analyzer`
- Import specific items, not modules: ✅ `from Click import command` vs ❌ `import click` (unless needed)
- Use `as` for clarity when needed:
  ```python
  from rich.progress import Progress as RichProgress
  ```

### Unused Imports

- **All unused imports must be removed** (ARG rule enforced)
- No import statements that aren't used in the file

```python
# ❌ WRONG - Path not used
from pathlib import Path
from typing import Any

def process(data: Any) -> str:
    return str(data)

# ✅ CORRECT
from typing import Any

def process(data: Any) -> str:
    return str(data)
```

---

## Error Handling

### Exception Types

Use specific exceptions, not generic `Exception`:

```python
# ✅ CORRECT
raise ValueError("Path must be a directory")
raise FileNotFoundError(f"Config file not found: {path}")
raise TimeoutError("Scan exceeded maximum duration")

# ❌ WRONG
raise Exception("Invalid input")
```

### Error Messages

- Use descriptive, actionable messages
- Include relevant context (values, paths, etc.)
- Use f-strings for message formatting

```python
# ✅ GOOD
raise ValueError(
    f"Max file size '{max_size_mb}' must be positive. "
    f"Got: {provided_value}"
)

# ❌ POOR
raise ValueError("Invalid file size")
```

### Exception Handling

- Catch specific exceptions, not `Exception` or `BaseException`
- Re-raise with context when appropriate
- Use `except ... as e:` only when you need the exception object

```python
# ✅ CORRECT
try:
    return self._parse_yaml(config_path)
except FileNotFoundError:
    console.print(f"Config file not found: {config_path}")
    return None
except yaml.YAMLError as e:
    raise ValueError(f"Invalid YAML in {config_path}: {e}") from e

# ❌ WRONG
try:
    return self._parse_yaml(config_path)
except:  # Catches everything
    return None
```

---

## Security Practices

### Bandit Rules (Security Scanning)

The project uses Bandit (enabled in Ruff) to catch security issues.

**Exceptions** are allowed only for tests:
- `S101`: Assert statements in tests
- `S105`: Test credentials in test files

**Common violations to avoid**:

1. **Hardcoded Passwords/Tokens**
   ```python
   # ❌ WRONG
   API_KEY = "sk-1234567890abcdef"

   # ✅ CORRECT
   API_KEY = os.getenv("API_KEY")
   ```

2. **SQL Injection / Command Injection**
   ```python
   # ❌ WRONG
   os.system(f"git {user_input}")

   # ✅ CORRECT
   subprocess.run(["git", user_input], check=True)
   ```

3. **Deserialization of Untrusted Data**
   ```python
   # ❌ WRONG
   import pickle
   data = pickle.loads(untrusted_bytes)

   # ✅ CORRECT
   import json
   data = json.loads(untrusted_string)
   ```

### Input Validation

- Validate all user input and external data
- Validate file paths to prevent directory traversal
- Validate configuration values against expected types/ranges

```python
def __init__(self, max_size_mb: int) -> None:
    if max_size_mb <= 0:
        raise ValueError(f"max_size_mb must be positive, got {max_size_mb}")
    self.max_size_mb = max_size_mb
```

---

## Git & Commit Practices

### Branching Strategy

- `main`: Production-ready code, releases only — never commit directly
- `develop`: Integration branch — all feature branches merge here
- Feature branches: branch from `develop`, merge back to `develop` via PR
- Branch naming: `feat/<short-description>`, `fix/<short-description>`, `refactor/<short-description>` etc.

**Example**:
```bash
git checkout develop
git checkout -b feat/add-rust-language-support
# ... do work ...
# Open PR targeting develop
```

### Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or modifications
- `chore`: Build, dependency, or tooling changes

**Example**:
```
feat(analyzer): add support for Rust language detection

- Extend language_detector.py to recognize .rs files
- Add Rust to language mappings in assets/languages.yml
- Add test coverage for Rust file analysis

Closes #123
```

### Commit Best Practices

- Make atomic commits (one logical change per commit)
- Keep commit messages clear and descriptive
- Reference issue numbers when applicable: `Closes #42`
- Don't mix formatting and functional changes in one commit
- Verify all checks pass before committing

---

## Development Workflow Summary

### Before Committing

```bash
# 1. Format code
uv run ruff format .

# 2. Lint and auto-fix issues
uv run ruff check . --fix

# 3. Run type checking
uv run ty check

# 4. Run tests with coverage
uv run pytest -v --cov=statsvy --cov-report=term-missing

# Or use the convenience command:
just check
```

### Quick Development Loop

```bash
# Quick run without checks (during development)
just dev

# Full run with all checks
just run
```

---

## Checklist for Code Review

Use this checklist for all code submissions:

### Code Quality
- [ ] All code formatted with `ruff format`
- [ ] All linting issues fixed with `ruff check --fix`
- [ ] Type annotations complete (no missing `:` or `->`)
- [ ] Type checker passes (`ty`) with no errors
- [ ] All public classes/functions have docstrings
- [ ] Docstrings follow Google style
- [ ] No unused imports or variables
- [ ] No complexity violations (max 7)

### Testing
- [ ] Test coverage >= 90%
- [ ] All tests pass
- [ ] New tests added for new functionality

### General Programming Principles
- [ ] No global variables (use dependency injection instead)
- [ ] Methods that don't use `self` are `@staticmethod` or module functions
- [ ] Data is immutable by default (use `frozen=True`, `tuple`, etc.)
- [ ] Each function/class has single responsibility
- [ ] No repeated code (DRY principle)
- [ ] Prefers composition over inheritance
- [ ] Input validation happens early (fail fast)
- [ ] Behavior is explicit, not implicit
- [ ] No over-engineering for hypothetical future needs (YAGNI)

### Security & Reliability
- [ ] Commit message follows conventional format
- [ ] No print() statements (use logging if needed)
- [ ] No hardcoded credentials or secrets
- [ ] No unhandled exceptions
- [ ] Appropriate error messages with context

---

## Continuous Integration

These rules are automatically enforced in CI/CD:

1. **Formatting**: `ruff format --check .` fails if code is not formatted
2. **Linting**: `ruff check .` fails if linting issues exist
3. **Type Checking**: `ty check` fails if type errors exist
4. **Testing**: `pytest --cov=statsvy --cov-fail-under=90` fails if coverage < 90%
5. **All checks must pass** before code can be merged

---

## References

### Python Style & Tooling
- [PEP 8 - Style Guide for Python Code](https://pep8.org)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Type Hints PEP 484](https://peps.python.org/pep-0484/)

### Programming Principles & Patterns
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [DRY - Don't Repeat Yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [YAGNI - You Aren't Gonna Need It](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it)
- [Composition vs Inheritance](https://en.wikipedia.org/wiki/Composition_over_inheritance)
- [Fail Fast Principle](https://en.wikipedia.org/wiki/Fail-fast)
- [Immutability in Python](https://docs.python.org/3/library/dataclasses.html#immutable-dataclasses)

---

**Last Updated**: February 21, 2026

## Summary

These guidelines establish a comprehensive framework for writing production-quality code. The **General Programming Best Practices** section provides universal principles applicable across all programming languages, while the remaining sections provide Python-specific implementations and tooling configuration.

All contributors must adhere to these standards. Violations will result in review comments requesting changes before merge.
