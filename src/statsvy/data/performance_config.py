"""Performance configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerformanceConfig:
    """Performance-related flags grouped together.

    - track_mem: measure memory (tracemalloc)
    - track_io: measure I/O throughput (MB/s)
    """

    track_mem: bool
    track_io: bool
