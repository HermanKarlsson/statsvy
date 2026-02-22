"""Public programmatic API for Statsvy.

This module exposes a stable, minimal API surface intended for integrations
that want to use Statsvy without invoking the CLI.
"""

from statsvy.api.api_comparison_result import ApiComparisonResult
from statsvy.api.api_scan_result import ApiScanResult
from statsvy.api.public_api import StatsvyApi

__all__ = ["ApiComparisonResult", "ApiScanResult", "StatsvyApi"]
