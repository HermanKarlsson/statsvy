"""Directory scanning utilities for Statsvy."""

from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.text import Text

from statsvy.data.config import Config
from statsvy.data.scan_result import ScanResult
from statsvy.utils.console import console
from statsvy.utils.formatting import format_size
from statsvy.utils.timeout_checker import TimeoutChecker


class Scanner:
    """A utility class to scan a directory and calculate file statistics.

    Attributes:
        root_path (Path): The validated directory path to be scanned.
        ignore (tuple[str, ...]): Glob patterns to exclude from the scan.
    """

    def __init__(
        self,
        path: Path | str,
        ignore: tuple[str, ...] = (),
        no_gitignore: bool = False,
        config: Config | None = None,
    ) -> None:
        """Initialize the Scanner.

        Args:
            path: The path to the directory to scan.
            ignore: Optional tuple of glob patterns to ignore.
                Defaults to an empty tuple.
            no_gitignore: If True, don't parse .gitignore file.
            config: Optional configuration controlling scan behavior.

        Raises:
            ValueError: If the path does not exist or is not a directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            raise ValueError(f"Path '{path}' does not exist")
        if not path.is_dir():
            raise ValueError(f"Path '{path}' is not a directory")

        self.root_path = path
        self.no_gitignore = no_gitignore
        self.config = config or Config.default()

        if not no_gitignore:
            gitignore_patterns = self._parse_gitignore()
            self.ignore = ignore + gitignore_patterns
        else:
            self.ignore = ignore

        if self.config.core.verbose:
            console.print("Initialized Scanner")

    def scan(self, timeout_checker: TimeoutChecker | None = None) -> ScanResult:
        """Recursively scan the directory and calculate totals.

        Args:
            timeout_checker: Optional timeout checker to enforce scan time limits.

        Returns:
            ScanResult: Object containing total file count, total size
                in bytes, and a list of all scanned file paths.

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        if self.config.core.verbose:
            console.print("Start scanning...")

        all_files = list(self.root_path.rglob("*"))
        show_progress = self.config.core.show_progress

        if show_progress:
            scan_data = self._scan_with_progress(all_files, timeout_checker)
        else:
            scan_data = self._scan_without_progress(all_files, timeout_checker)

        # Provide a short summary for non-verbose users so they are aware of
        # skipped files and duplicate detection without needing -v.
        if not self.config.core.verbose:
            skipped_by_dir = scan_data.get("skipped_by_dir", {})
            total_skipped = sum(skipped_by_dir.values()) if skipped_by_dir else 0
            if total_skipped:
                console.print(
                    Text("Info: ")
                    + Text(str(total_skipped), style="cyan")
                    + Text(" files skipped by filters (use -v to list)", style="yellow")
                )

            dup_count = len(scan_data.get("duplicate_files", []))
            if dup_count:
                console.print(
                    Text(
                        f"Info: {dup_count} duplicate files detected (use -v to list)",
                        style="yellow",
                    )
                )

        if self.config.core.verbose:
            self._log_scan_complete(scan_data)

        return ScanResult(
            scan_data["total_files"],
            scan_data["total_size_bytes"],
            tuple(scan_data["scanned_files"]),
            tuple(scan_data.get("duplicate_files", [])),
            scan_data.get("bytes_read", 0),
            scan_data.get("file_data", None),
        )

    def _scan_with_progress(
        self, all_files: list[Path], timeout_checker: TimeoutChecker | None
    ) -> dict[str, Any]:
        """Scan files with progress bar display.

        Args:
            all_files: All filesystem paths to scan.
            timeout_checker: Optional timeout checker to enforce scan time limits.

        Returns:
            Collected scan data including totals and scanned paths.

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        scan_data = self._initialize_scan_data()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Scanning files...", total=len(all_files))

            for path in all_files:
                if timeout_checker:
                    timeout_checker.check("file discovery")
                progress.update(task, advance=1)
                self._process_path(path, scan_data)

        return scan_data

    def _scan_without_progress(
        self, all_files: list[Path], timeout_checker: TimeoutChecker | None
    ) -> dict[str, Any]:
        """Scan files without progress bar display.

        Args:
            all_files: All filesystem paths to scan.
            timeout_checker: Optional timeout checker to enforce scan time limits.

        Returns:
            Collected scan data including totals and scanned paths.

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        scan_data = self._initialize_scan_data()

        for path in all_files:
            if timeout_checker:
                timeout_checker.check("file discovery")
            self._process_path(path, scan_data)

        return scan_data

    @staticmethod
    def _initialize_scan_data() -> dict[str, Any]:
        """Initialize empty scan data structure.

        Returns:
            Dictionary with zeroed counters and an empty file list.
        """
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "scanned_files": [],
            "skipped_by_dir": {},
            # For duplicate detection (hash -> first seen path)
            "_hash_index": {},
            "duplicate_files": [],
            # Total bytes actually read from disk by the scanner
            "bytes_read": 0,
            # Optional per-file metadata to avoid re-reading files later
            "file_data": {},
        }

    def _process_path(self, path: Path, scan_data: dict[str, Any]) -> None:
        """Process a single path and update scan data if it's a valid file.

        This method performs validation (ignore rules, file/size checks),
        updates aggregate counters, and delegates per-file metadata
        collection to a helper so the method remains concise.
        """
        if self._should_ignore(path):
            self._record_skipped_path(path, scan_data)
            return

        if not path.is_file():
            return

        size = path.stat().st_size
        if not self._within_size_bounds(size):
            self._record_skipped_path(path, scan_data)
            return

        if self.config.core.verbose:
            console.print(Text(f"Processing: {path}", style="cyan"))

        # Update totals (always counted)
        scan_data["total_files"] += 1
        scan_data["total_size_bytes"] += size

        # Gather and persist per-file metadata (separated to reduce
        # complexity of this method). _gather_file_data will increment
        # bytes_read when it actually reads file content.
        file_data = self._gather_file_data(path, size, scan_data)
        scan_data.setdefault("file_data", {})[path] = file_data

        # Duplicate detection and scanned_files append remain simple and
        # delegated to their helpers.
        self._maybe_record_duplicate(path, size, scan_data)
        scan_data["scanned_files"].append(path)

    def _log_scan_complete(self, scan_data: dict[str, Any]) -> None:
        """Log scan completion summary in verbose mode.

        Args:
            scan_data: Scan totals used for the summary output.
        """
        console.print(
            Text("Scan complete!\n")
            + Text("Total files - ")
            + Text(f"{scan_data['total_files']}\n", style="cyan")
            + Text("Total size - ")
            + Text(f"{format_size(scan_data['total_size_bytes'])}\n", style="cyan")
        )

        skipped_by_dir = scan_data["skipped_by_dir"]
        if skipped_by_dir:
            for directory, count in self._sorted_skip_groups(skipped_by_dir):
                console.print(
                    Text(f"Skipped {count} files in {directory}", style="dim")
                )

        # Inform about detected duplicates (always logged when present)
        if scan_data.get("duplicate_files"):
            console.print(Text("Duplicate files detected:", style="dim"))
            for dup in scan_data["duplicate_files"][:10]:
                console.print(Text(f"  - {dup}", style="dim"))
            if len(scan_data["duplicate_files"]) > 10:
                console.print(
                    Text(
                        f"  ... and {len(scan_data['duplicate_files']) - 10} more",
                        style="dim",
                    )
                )

    def _record_skipped_path(self, path: Path, scan_data: dict[str, Any]) -> None:
        """Record a skipped path grouped by directory.

        Args:
            path: Path that was skipped.
            scan_data: Mutable scan accumulator to update.
        """
        group_key = self._get_skip_group_key(path)
        skipped_by_dir: dict[str, int] = scan_data["skipped_by_dir"]
        skipped_by_dir[group_key] = skipped_by_dir.get(group_key, 0) + 1

    def _get_skip_group_key(self, path: Path) -> str:
        """Determine the directory label for a skipped path.

        Args:
            path: Path that was skipped.

        Returns:
            Directory label relative to the scan root, with trailing slash.
        """
        match = self._find_ignore_match(path)
        if match is None:
            match = path.parent

        if match.is_file():
            match = match.parent

        try:
            relative = match.relative_to(self.root_path)
        except ValueError:
            relative = match

        if relative == Path("."):
            return "./"

        return f"{relative.as_posix().rstrip('/')}/"

    def _find_ignore_match(self, path: Path) -> Path | None:
        """Find the first path in the chain that matches ignore patterns.

        Args:
            path: Path that was skipped.

        Returns:
            Matching path or None if no match is found.
        """
        candidates = [path, *path.parents]
        for candidate in candidates:
            # Check the candidate (including the root path) and stop after
            # the root has been inspected. Previously the loop broke before
            # checking ``root_path`` which could miss patterns that target
            # the repository root.
            if any(candidate.match(pattern) for pattern in self.ignore):
                return candidate
            if candidate == self.root_path:
                break

        return None

    @staticmethod
    def _file_hash(path: Path) -> str:
        """Compute SHA-256 hash of a file's contents.

        Reads the file in chunks to avoid high memory usage for large files.

        Args:
            path: File path to hash.

        Returns:
            Hex digest string of the file content hash.
        """
        h = sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _gather_file_data(
        self, path: Path, size: int, scan_data: dict[str, object]
    ) -> dict[str, object]:
        """Collect per-file metadata used by Analyzer to avoid re-reading files.

        Returns a small dict containing: is_binary (bool), lines (int),
        text (str | None) and bytes (bytes | None).

        Also increments the running "bytes_read" counter in *scan_data* when
        file contents are actually read from disk so callers can compute I/O
        throughput (MB/s) accurately.
        """
        file_data: dict[str, object] = {
            "is_binary": False,
            "lines": 0,
            "text": None,
            "bytes": None,
        }

        suffix = path.suffix.lower()
        is_binary_ext = suffix in getattr(self.config.scan, "binary_extensions", ())

        needs_hash = size >= self.config.files.duplicate_threshold_bytes

        if not is_binary_ext:
            if needs_hash:
                b = path.read_bytes()
                # Track bytes actually read
                prev = cast(int, scan_data.get("bytes_read", 0))
                scan_data["bytes_read"] = prev + len(b)
                file_data["bytes"] = b
                text = b.decode("utf-8", errors="ignore")
                file_data["text"] = text
                file_data["lines"] = len(text.splitlines())
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
                # Count bytes read based on filesystem size for simplicity
                prev = cast(int, scan_data.get("bytes_read", 0))
                scan_data["bytes_read"] = prev + size
                file_data["text"] = text
                file_data["lines"] = len(text.splitlines())
        else:
            file_data["is_binary"] = True
            if needs_hash:
                b = path.read_bytes()
                prev = cast(int, scan_data.get("bytes_read", 0))
                scan_data["bytes_read"] = prev + len(b)
                file_data["bytes"] = b

        return file_data

    def _within_size_bounds(self, size: int) -> bool:
        """Return True if `size` (bytes) is within configured min/max bounds.

        Uses MB-to-bytes conversion based on the ScanConfig values.
        """
        min_bytes = int(self.config.scan.min_file_size_mb * 1024 * 1024)
        max_bytes = int(self.config.scan.max_file_size_mb * 1024 * 1024)
        return min_bytes <= size <= max_bytes

    @staticmethod
    def _sorted_skip_groups(skipped_by_dir: dict[str, int]) -> list[tuple[str, int]]:
        """Sort skipped groups for stable verbose output.

        Args:
            skipped_by_dir: Mapping of directory labels to skip counts.

        Returns:
            Sorted list of (directory, count) pairs.
        """
        return sorted(
            skipped_by_dir.items(),
            key=lambda item: (-item[1], item[0]),
        )

    def _maybe_record_duplicate(
        self, path: Path, size: int, scan_data: dict[str, Any]
    ) -> None:
        """Record duplicate files when they match size + hash.

        This helper encapsulates the duplicate-detection mutation so the
        main path-processing method remains simple and testable.
        """
        if size < self.config.files.duplicate_threshold_bytes:
            return

        content_bytes: bytes | None = None
        fd = scan_data.get("file_data")
        info = fd.get(path) if fd is not None else None
        if info is not None:
            content_bytes = info.get("bytes")

        if content_bytes is not None:
            h = sha256(content_bytes).hexdigest()
        else:
            h = self._file_hash(path)

        key = f"{size}:" + h
        first = scan_data["_hash_index"].get(key)
        if first is None:
            scan_data["_hash_index"][key] = path
        else:
            scan_data["duplicate_files"].append(path)

    def _should_ignore(self, path: Path) -> bool:
        """Determine if a given path should be ignored based on patterns.

        Checks both the path itself and all its parent directories up to
        and including the root path against the ignore patterns.

        Args:
            path: The filesystem path to check.

        Returns:
            True if the path or any of its parents match an ignore pattern,
            False otherwise.
        """
        if any(path.match(pattern) for pattern in self.ignore):
            return True

        for parent in path.parents:
            # Inspect the parent (including the repository root) and stop
            # after the root has been checked. Previously the loop stopped
            # before checking the root path which could allow root-level
            # ignore patterns to be missed.
            if any(parent.match(pattern) for pattern in self.ignore):
                return True
            if parent == self.root_path:
                break

        return False

    def _parse_gitignore(self) -> tuple[str, ...]:
        """Parse .gitignore file in the root path.

        Returns:
            Tuple of glob patterns from .gitignore.
        """
        gitignore_path = self.root_path / ".gitignore"

        if not gitignore_path.exists():
            if self.config.core.verbose:
                console.print("No .gitignore file found")
            return ()

        patterns = self._extract_gitignore_patterns(gitignore_path)

        if self.config.core.verbose and patterns:
            self._log_gitignore_patterns(patterns)

        return tuple(patterns)

    @staticmethod
    def _extract_gitignore_patterns(gitignore_path: Path) -> list[str]:
        """Extract ignore patterns from .gitignore file.

        Args:
            gitignore_path: Path to the .gitignore file.

        Returns:
            List of glob patterns.
        """
        patterns: list[str] = []
        for line in gitignore_path.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                continue

            pattern = stripped_line.rstrip("/")
            patterns.append(pattern)

        return patterns

    @staticmethod
    def _log_gitignore_patterns(patterns: list[str]) -> None:
        """Log loaded gitignore patterns in verbose mode.

        Args:
            patterns: List of glob patterns from .gitignore.
        """
        console.print(Text(f"Loaded {len(patterns)} ignore pattern(s) from .gitignore"))
        for pattern in patterns[:5]:  # Show first 5
            console.print(Text(f"  - {pattern}", style="dim"))
        if len(patterns) > 5:
            console.print(Text(f"  ... and {len(patterns) - 5} more", style="dim"))
