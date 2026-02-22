# Developer API

This guide is for developers integrating Statsvy as a Python library instead of using the CLI.

## Audience and Scope

Use the Developer API when you want to:

- run scans from Python code,
- compare scan snapshots programmatically,
- produce formatted output for your own pipelines.

The public entrypoint is the `StatsvyApi` class in `statsvy.api`.

## Stability Contract

Statsvy maintains API compatibility by exposing a narrow surface and stable DTOs:

- `StatsvyApi`
- `ApiScanResult`
- `ApiComparisonResult`

Compatibility follows the package versioning strategy. The API contract is validated by dedicated tests in `tests/api/`.

## Quick Start

```python
from statsvy.api import StatsvyApi

backend = StatsvyApi.scan("services/backend")
frontend = StatsvyApi.scan("services/frontend")
comparison = StatsvyApi.compare(backend, frontend)

json_output = StatsvyApi.format_result(comparison, output_format="json")
print(json_output)
```

## API Reference

### `StatsvyApi.scan(path, config=None) -> ApiScanResult`

Scans and analyzes a project directory.

- Delegates scanning to internal scanner modules.
- Delegates line/language analysis to internal analyzer modules.
- Optionally attaches dependency analysis based on configuration.

Raises:

- `ValueError` when the path is invalid.
- `TimeoutError` when scan/analysis exceeds configured timeout.

### `StatsvyApi.compare(project1, project2) -> ApiComparisonResult`

Compares two `ApiScanResult` snapshots and returns structured deltas.

### `StatsvyApi.format_result(result, output_format=None, config=None, include_css=None) -> str`

Formats either `ApiScanResult` or `ApiComparisonResult` into output text.

Supported `output_format` values:

- `table`
- `json`
- `markdown` / `md`
- `html`

## Configuration in API Usage

API usage is explicit: pass a `Config` object when you need overrides.

```python
from dataclasses import replace

from statsvy.api import StatsvyApi
from statsvy.data.config import Config

config = Config.default()
config = replace(
    config,
    core=replace(config.core, default_format="json", show_progress=False),
)

result = StatsvyApi.scan(".", config=config)
print(StatsvyApi.format_result(result, config=config))
```
