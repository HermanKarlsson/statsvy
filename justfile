# List available commands
default:
    @just --list

# Install pre-commit hooks (run once after cloning)
setup:
    @echo "Setting up development environment..."
    uv run pre-commit install --hook-type commit-msg --hook-type pre-commit
    @echo "Pre-commit hooks installed!"

# Run all checks (non-modifying, mirrors pre-commit)
check: format-check lint-check pre-commit-check type test
    @echo "All checks passed!"

# Check formatting (no modifications)
format-check:
    @echo "Checking formatting..."
    uv run ruff format --check .

# Check linting (no modifications)
lint-check:
    @echo "Checking linting..."
    uv run ruff check .

# Run pre-commit hooks in read-only mode (mirrors commit-time hooks)
pre-commit-check:
    @echo "Running pre-commit hooks (read-only)..."
    uv run pre-commit run --all-files --hook-stage pre-commit

# Auto-fix formatting and lint issues
fix:
    @echo "Fixing formatting..."
    uv run ruff format .
    @echo "Fixing lint issues..."
    uv run ruff check . --fix

# Type check
type:
    @echo "Type checking..."
    uv run ty check .

# Run tests
test:
    @echo "Running tests..."
    uv run pytest -n auto -v --cov=statsvy --cov-report=term-missing

# Run with checks
run: check
    @echo "Running statsvy..."
    uv run statsvy scan --dir . --verbose

# Quick run (no checks)
dev *ARGS:
    uv run statsvy {{ARGS}}

# Preview documentation locally
docs:
    uv run mkdocs serve

# Build documentation
docs-build:
    uv run mkdocs build

# Build package (sdist + wheel)
build:
    uv run python -m build

# Clean artifacts
clean:
    @echo "Cleaning..."
    rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov dist build site
    find . -type f -name "*.pyc" -delete
