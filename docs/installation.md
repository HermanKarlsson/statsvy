# Installation

## Recommended: pipx

[pipx](https://pipx.pypa.io/) installs Python CLI tools in isolated environments. This is the recommended way to install statsvy — it keeps your system Python clean and avoids dependency conflicts.

```bash
# Install pipx (if you don't have it)
python3 -m pip install --user pipx
pipx ensurepath

# Install statsvy from GitHub
pipx install git+https://github.com/HermanKarlsson/statsvy.git
```

To install a specific version:

```bash
pipx install git+https://github.com/HermanKarlsson/statsvy.git@v1.0.0
```

!!! tip "Don't have Python?"
    On **macOS**: `brew install python` or `brew install pipx`

    On **Ubuntu/Debian**: `sudo apt install python3 python3-pip pipx`

    On **Windows**: Install Python from [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12`

## pip

If you prefer a standard pip install (into your current environment):

```bash
pip install git+https://github.com/HermanKarlsson/statsvy.git
```

## From a GitHub Release

You can also download a pre-built wheel from the [Releases page](https://github.com/HermanKarlsson/statsvy/releases) and install it directly:

```bash
# Download the .whl file from the latest release, then:
pipx install ./statsvy-1.0.0-py3-none-any.whl
```

This works offline — no network access needed after downloading.

## From Source

For development or to get the latest unreleased changes:

```bash
git clone https://github.com/HermanKarlsson/statsvy.git
cd statsvy

# Using uv (recommended for development)
uv sync --all-extras
uv run statsvy --help

# Or using pip
pip install -e .
statsvy --help
```

## Verify Installation

```bash
statsvy --version
```

## Requirements

- Python 3.12 or higher
- Git (for installation from GitHub, and for git statistics features)

## Updating

=== "pipx"

    ```bash
    pipx upgrade statsvy
    ```

=== "pip"

    ```bash
    pip install --upgrade git+https://github.com/HermanKarlsson/statsvy.git
    ```

## Uninstalling

=== "pipx"

    ```bash
    pipx uninstall statsvy
    ```

=== "pip"

    ```bash
    pip uninstall statsvy
    ```
