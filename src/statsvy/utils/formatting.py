"""Utility functions for formatting metrics and comparisons.

This module provides reusable formatting utilities including delta string
generation for displaying differences between metrics.
"""

import re
from pathlib import Path


def delta_str(
    current: int | float, previous: int | float | None, color_pos: str = "spring_green3"
) -> str:
    """Format the difference between two numeric values as a coloured delta string.

    Args:
        current: The current (newer) value.
        previous: The previous (older) value, or ``None`` for the first entry.
        color_pos: Rich colour name to use for positive deltas.

    Returns:
        A Rich markup string such as ``[spring_green3]+42[/spring_green3]``
        or ``[red]-7[/red]``, or ``-`` when there is no previous value.

    Example:
        >>> delta_str(150, 100)
        '[spring_green3]+50[/spring_green3]'
        >>> delta_str(80, 100)
        '[red]-20[/red]'
        >>> delta_str(100, None)
        '-'
    """
    if previous is None:
        return "-"
    diff = current - previous
    if diff > 0:
        return f"[{color_pos}]+{diff:,}[/{color_pos}]"
    if diff < 0:
        return f"[red]{diff:,}[/red]"
    return "[grey50]±0[/grey50]"


def percent_delta_str(
    current: int | float,
    previous: int | float | None,
    color_pos: str = "spring_green3",
) -> str:
    """Format the percentage difference between two numeric values as a colored string.

    Args:
        current: The current (newer) value.
        previous: The previous (older) value, or ``None`` for the first entry.
        color_pos: Rich colour name to use for positive deltas.

    Returns:
        A Rich markup string showing percentage change, or ``-`` when no previous value.

    Raises:
        ZeroDivisionError: If previous is 0 and we can't calculate percentage.

    Example:
        >>> percent_delta_str(150, 100)
        '[spring_green3]+50.0%[/spring_green3]'
        >>> percent_delta_str(80, 100)
        '[red]-20.0%[/red]'
    """
    if previous is None or previous == 0:
        return "-"
    percent_change = ((current - previous) / previous) * 100
    if percent_change > 0:
        return f"[{color_pos}]+{percent_change:.1f}%[/{color_pos}]"
    if percent_change < 0:
        return f"[red]{percent_change:.1f}%[/red]"
    return "[grey50]±0.0%[/grey50]"


def truncate_path_display(path: Path | str, max_parts: int = 3) -> str:
    """Return a truncated path for display purposes.

    Uses a ``prefix/.../suffix`` format to keep the output compact while
    preserving recognisable path segments.

    Args:
        path: Path to truncate.
        max_parts: Minimum number of parts required before truncation.

    Returns:
        Truncated path string with forward slashes.
    """
    path_obj = Path(path)
    path_str = path_obj.as_posix()
    is_absolute = path_obj.is_absolute()
    parts = [part for part in path_str.split("/") if part]

    if len(parts) <= max_parts:
        return path_str

    prefix = parts[:2]
    suffix = parts[-1:]
    truncated = "/".join([*prefix, "...", *suffix])
    return f"/{truncated}" if is_absolute else truncated


def parse_size_to_mb(value: str) -> float:
    """Parse a human-readable size string into megabytes (MB).

    Supported inputs (case-insensitive):
    - bytes: "512b" or "512" (when suffix omitted numeric input is treated as MB)
    - kilobytes: "1kb", "1k"
    - megabytes: "1mb", "1m"

    Decimal values are accepted (e.g. "1.5MB"). Parsing uses 1024-based
    units (i.e. 1 KB = 1024 bytes, 1 MB = 1024*1024 bytes).

    Args:
        value: Human-readable size string.

    Returns:
        Size in megabytes (float).

    Raises:
        ValueError: If the string cannot be parsed.
    """
    if not isinstance(value, str):
        raise ValueError("size must be a string")

    s = value.strip().lower()
    if not s:
        raise ValueError("empty size string")

    m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*(b|kb|k|mb|m)?", s)
    if not m:
        raise ValueError(f"invalid size: {value}")

    num_str, unit = m.groups()
    num = float(num_str)

    # Default (no unit) treated as megabytes for backward compatibility
    if unit is None or unit in ("m", "mb"):
        return num
    if unit in ("k", "kb"):
        return num / 1024.0
    if unit == "b":
        return num / (1024.0 * 1024.0)

    raise ValueError(f"unsupported unit: {unit}")


def format_size(num_bytes: int | None, precision: int = 2) -> str:
    """Return a human-readable size string for *num_bytes*.

    Conversion uses 1024-based units and adapts the displayed unit based on
    magnitude (B, KB, MB, GB, ...). For `B` the value is shown as an
    integer; for larger units trailing zeros are trimmed (e.g. ``1 MB`` not
    ``1.00 MB``).

    Args:
        num_bytes: Size in bytes, or None to return '-'.
        precision: Maximum number of decimal places for non-byte units.

    Returns:
        Human-readable size string like "1.5 MB", or '-' if num_bytes is None.

    Raises:
        ValueError: If num_bytes is negative.

    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(1536)
        '1.5 KB'
        >>> format_size(1572864)
        '1.5 MB'
        >>> format_size(None)
        '-'
    """
    if num_bytes is None:
        return "-"
    if num_bytes < 0:
        raise ValueError("num_bytes must be non-negative")

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1

    unit = units[idx]
    if unit == "B":
        return f"{int(size)} B"

    # format with fixed precision then strip unnecessary zeros
    formatted = f"{size:.{precision}f}".rstrip("0").rstrip(".")
    return f"{formatted} {unit}"
