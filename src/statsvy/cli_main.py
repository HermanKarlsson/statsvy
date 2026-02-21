"""Command-line interface for the statsvy application.

This module provides CLI commands for scanning directories and analyzing
file statistics.
"""

from dataclasses import replace
from pathlib import Path
from typing import TypedDict, Unpack, cast

import click
from rich import inspect

from statsvy import __version__
from statsvy.cli.compare_handler import CompareHandler
from statsvy.cli.scan_handler import ScanHandler
from statsvy.config.config_loader import ConfigLoader
from statsvy.core.project import Project
from statsvy.storage.storage_presenter import StoragePresenter
from statsvy.utils.console import _AppConsole, console


class ScanKwargs(TypedDict, total=False):
    """Configuration options for the scan command.

    Attributes:
        dir: The target directory path to scan.
        ignore: A tuple of glob patterns to exclude from the scan.
        verbose: If True, enables detailed logging and inspection output.
        format: The desired output format (e.g., 'table', 'json', 'md').
        output: A Path object specifying where to save the results.
        no_color: If True, disables ANSI color codes in the console output.
        no_progress: If True, hides the progress bar during the scan.
        follow_symlinks: If True, the scanner will traverse symbolic links.
        max_depth: The maximum directory depth to recurse into.
        max_file_size: The maximum file size in MB to include in analysis.
        include_hidden: If True, includes hidden files and directories.
        no_gitignore: If True, ignores rules defined in .gitignore files.
        git: Whether to include or exclude git-specific statistics.
        no_save: If True, doesn't save scan results to history.
        truncate_paths: Whether to truncate displayed paths.
        percentages: Whether to show percentage columns.
        show_contributors: Whether to show contributors in git statistics.
        max_contributors: Maximum number of contributors to display.
        track_performance: If True, enables performance metric tracking.
        track_io: If True, enables I/O throughput measurement.
        track_mem: If True, enables memory profiling.
        track_cpu: If True, enables CPU profiling.
        scan_timeout: Maximum scan duration in seconds.
        min_lines_threshold: Minimum number of lines for a file to be included.
        no_deps: If True, skips dependency analysis.
        no_deps_list: If True, shows only dep counts, not individual package names.
    """

    dir: str | None
    ignore: tuple[str, ...]
    verbose: bool
    format: str | None
    output: Path | None
    no_color: bool
    no_progress: bool
    follow_symlinks: bool
    max_depth: int | None
    max_file_size: int | None
    min_file_size: int | None
    include_hidden: bool
    no_gitignore: bool
    git: bool | None
    no_save: bool
    truncate_paths: bool | None
    percentages: bool | None
    show_contributors: bool | None
    max_contributors: int | None
    track_performance: bool
    track_io: bool
    track_mem: bool
    track_cpu: bool
    scan_timeout: int | None
    min_lines_threshold: int | None
    no_deps: bool
    no_deps_list: bool


def _setup_scan_config(loader: ConfigLoader, **kwargs: Unpack[ScanKwargs]) -> None:
    """Update the configuration based on CLI arguments for scan command.

    Args:
        loader: The ConfigLoader instance to update.
        **kwargs: Keyword arguments containing CLI options.
    """
    output = kwargs.get("output")
    no_color = kwargs.get("no_color")
    no_progress = kwargs.get("no_progress")
    no_gitignore = kwargs.get("no_gitignore")
    no_save = kwargs.get("no_save")

    loader.update_from_cli(
        core_verbose=kwargs.get("verbose"),
        core_default_format=kwargs.get("format"),
        core_out_dir=str(output.parent) if output else None,
        core_color=not no_color if no_color else None,
        core_show_progress=not no_progress if no_progress else None,
        core_performance_track_mem=kwargs.get("track_mem")
        if kwargs.get("track_mem") is not None
        else kwargs.get("track_performance"),
        core_performance_track_io=kwargs.get("track_io"),
        core_performance_track_cpu=kwargs.get("track_cpu"),
        scan_follow_symlinks=kwargs.get("follow_symlinks"),
        scan_max_depth=kwargs.get("max_depth"),
        scan_min_file_size_mb=kwargs.get("min_file_size"),
        scan_max_file_size_mb=kwargs.get("max_file_size"),
        scan_include_hidden=kwargs.get("include_hidden"),
        scan_respect_gitignore=not no_gitignore if no_gitignore else None,
        scan_timeout_seconds=kwargs.get("scan_timeout"),
        language_min_lines_threshold=kwargs.get("min_lines_threshold"),
        git_enabled=kwargs.get("git"),
        git_show_contributors=kwargs.get("show_contributors"),
        git_max_contributors=kwargs.get("max_contributors"),
        storage_auto_save=not no_save if no_save else None,
        display_truncate_paths=kwargs.get("truncate_paths"),
        display_show_percentages=kwargs.get("percentages"),
        display_show_deps_list=(
            not no_deps_list if (no_deps_list := kwargs.get("no_deps_list")) else None
        ),
    )


def _setup_compare_config(
    loader: ConfigLoader,
    verbose: bool,
    format: str | None,
    output: Path | None,
    no_color: bool,
    truncate_paths: bool | None,
    percentages: bool | None,
) -> None:
    """Update the configuration based on CLI arguments for compare command.

    Args:
        loader: The ConfigLoader instance to update.
        verbose: Enable verbose output.
        format: Output format.
        output: Path to save output file.
        no_color: Disable colored output.
        truncate_paths: Whether to truncate displayed paths.
        percentages: Whether to show percentage columns.
    """
    loader.update_from_cli(
        core_verbose=verbose,
        core_default_format=format,
        core_out_dir=str(output.parent) if output else None,
        core_color=not no_color if no_color else None,
        display_truncate_paths=truncate_paths,
        display_show_percentages=percentages,
    )


def _apply_profile_alias(kwargs: dict) -> None:
    """Apply `--profile` alias to explicit tracking flags.

    Only set values that the user hasn't explicitly provided (i.e. `None`).
    """
    profile_val = kwargs.get("profile")
    if profile_val is None:
        return

    if kwargs.get("track_performance") is None:
        kwargs["track_performance"] = profile_val
    if kwargs.get("track_io") is None:
        kwargs["track_io"] = profile_val
    if kwargs.get("track_mem") is None:
        kwargs["track_mem"] = profile_val
    if kwargs.get("track_cpu") is None:
        kwargs["track_cpu"] = profile_val


def _apply_track_performance_mapping(kwargs: dict) -> None:
    """When legacy `--track-performance` is used, enable both trackers.

    Respect explicit user overrides for `--track-io`/`--track-mem`.
    """
    tp = kwargs.get("track_performance")
    if tp is None:
        return

    if kwargs.get("track_io") is None:
        kwargs["track_io"] = tp
    if kwargs.get("track_mem") is None:
        kwargs["track_mem"] = tp
    if kwargs.get("track_cpu") is None:
        kwargs["track_cpu"] = tp


def _normalize_scan_profile_flags(kwargs: dict) -> None:
    """Normalize legacy/profile CLI flags into explicit tracking flags.

    Mutates *kwargs* in-place to ensure consistent downstream handling.
    """
    _apply_profile_alias(kwargs)
    _apply_track_performance_mapping(kwargs)


@click.group(
    help="Show project source statistics (supports pyproject.toml, statsvy.toml)"
)
@click.version_option(version=__version__)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help=(
        "Path to pyproject.toml / statsvy.toml / project.json / Cargo.toml "
        "configuration file"
    ),
)
@click.pass_context
def main(ctx: click.Context, config: Path | None) -> None:
    """Initialize the main CLI group for statsvy (user-facing summary).

    The detailed implementation notes and developer documentation are
    intentionally omitted from the user-facing help text.
    """
    loader = ConfigLoader(config_path=config)
    loader.load()
    ctx.obj = loader


@main.command()
@click.argument(
    "target",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--dir",
    type=click.Path(exists=True, file_okay=False),
    help="Directory to scan (use positional <target> or --dir)",
)
@click.option(
    "--ignore",
    "-i",
    "--exclude",
    "-e",
    multiple=True,
    help="Glob patterns to ignore (alias: --exclude, -e)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "md", "markdown", "html"]),
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save output to file",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--no-progress", is_flag=True, help="Disable progress bar")
@click.option("--follow-symlinks", is_flag=True, help="Follow symbolic links")
@click.option("--max-depth", type=int, help="Maximum directory depth")
@click.option(
    "--max-file-size",
    type=str,
    help="Skip files larger than X (supports B/KB/MB — e.g. 512b, 1kb, 1.5MB)",
)
@click.option(
    "--min-file-size",
    type=str,
    help="Skip files smaller than X (supports B/KB/MB — e.g. 512b, 1kb, 1.5MB)",
)
@click.option("--include-hidden", is_flag=True, help="Include hidden files")
@click.option("--no-gitignore", is_flag=True, help="Don't respect .gitignore")
@click.option(
    "--git/--no-git",
    default=None,
    help="Include/exclude git statistics",
    show_default=False,
)
@click.option(
    "--show-contributors/--no-show-contributors",
    default=None,
    show_default=False,
    help="Show or hide contributors in git statistics",
)
@click.option(
    "--max-contributors",
    type=int,
    help="Maximum number of contributors to display (default: 5)",
)
@click.option("--no-save", is_flag=True, help="Don't save scan results to history")
@click.option(
    "--truncate-paths/--no-truncate-paths",
    default=None,
    show_default=False,
    help="Truncate displayed paths (e.g., src/.../module.py)",
)
@click.option(
    "--percentages/--no-percentages",
    default=None,
    show_default=False,
    help="Show or hide percentage columns in output",
)
@click.option(
    "--track-performance/--no-track-performance",
    default=None,
    help=(
        "Enable or disable profiling (I/O, memory, and CPU). "
        "Performs separate runs per enabled metric. "
        "(omit to use config file)"
    ),
)
@click.option(
    "--profile/--no-profile",
    default=None,
    help="Alias for --track-performance (runs I/O + memory + CPU profiling)",
)
@click.option(
    "--track-io/--no-track-io",
    default=None,
    help="Enable or disable I/O throughput measurement (MiB/s).",
)
@click.option(
    "--track-mem/--no-track-mem",
    default=None,
    help="Enable or disable memory profiling.",
)
@click.option(
    "--track-cpu/--no-track-cpu",
    default=None,
    help="Enable or disable CPU profiling.",
)
@click.option(
    "--scan-timeout",
    "--timeout",
    type=int,
    help="Maximum scan duration in seconds (default: 300)",
)
@click.option(
    "--min-lines-threshold",
    "--min-lines",
    type=int,
    help="Skip files with fewer lines than this threshold (default: 0)",
)
@click.option(
    "--no-deps",
    is_flag=True,
    help="Skip dependency analysis (dependencies analyzed by default)",
)
@click.option(
    "--no-deps-list",
    is_flag=True,
    help="Show only dependency counts, not individual package names",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress console output")
@click.pass_obj
def scan(
    loader: ConfigLoader, target: Path | None = None, **kwargs: Unpack[ScanKwargs]
) -> None:
    """Scan a directory and display detailed file statistics.

    Scans the specified directory (or current directory/tracked project),
    analyzes file statistics, formats the results, and optionally saves
    them to a file or history.

    Args:
        loader: The ConfigLoader instance containing configuration settings.
        target: Optional positional directory to scan. If provided, this takes
            precedence over the `--dir` option.
        **kwargs: Command-line options.
    """
    # Normalize profile/alias flags (kept in helper for readability).
    _normalize_scan_profile_flags(kwargs)

    # Honor --quiet by silencing the shared console for this invocation
    prev_quiet = console.quiet
    if kwargs.get("quiet"):
        console.quiet = True

    try:
        _setup_scan_config(loader, **kwargs)

        # Apply color setting to runtime console immediately so output
        # produced after this point respects --no-color / core.color.
        cast(_AppConsole, console).set_color_enabled(loader.config.core.color)

        # Override dependencies config if --no-deps flag is set
        if kwargs.get("no_deps"):
            loader.config = replace(
                loader.config,
                dependencies=replace(
                    loader.config.dependencies, include_dependencies=False
                ),
            )

        handler = ScanHandler(loader.config)

        # positional `target` takes precedence over --dir option
        effective_target: str | None = str(target) if target else kwargs.get("dir")

        handler.execute(
            target_dir=effective_target,
            ignore_patterns=kwargs.get("ignore", ()),
            output_format=kwargs.get("format"),
            output_path=kwargs.get("output"),
        )
    finally:
        # Restore prior console state so tests and callers are not affected.
        console.quiet = prev_quiet


@main.command()
@click.pass_obj
def config(loader: ConfigLoader) -> None:
    """Display the current configuration.

    Prints all configuration settings from the currently loaded config
    in a structured format.
    """
    inspect(loader.config)


@main.command()
def track() -> None:
    """Start tracking the current project.

    Initializes project tracking by creating a .statsvy/project.json file
    with project metadata.
    """
    Project.track()


@main.command()
def untrack() -> None:
    """Stop tracking the current project.

    Removes the .statsvy directory, effectively untracking the project.
    """
    Project.untrack()


@main.command()
def latest() -> None:
    """Display the results from the latest scan.

    Retrieves and displays information about the most recent scan,
    including scan time and key metrics.
    """
    StoragePresenter.show_latest()


@main.command()
def history() -> None:
    """Display the full scan history.

    Retrieves all stored scan results from the history file and displays
    them in a formatted list.
    """
    StoragePresenter.show_history()


@main.command()
def current() -> None:
    """Display detailed information about the current tracked project.

    Retrieves project metadata and latest scan details and presents
    them as a project summary.
    """
    StoragePresenter.show_current()


@main.command()
@click.argument("project1", type=click.Path(exists=True, file_okay=False))
@click.argument("project2", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "md", "markdown", "html"]),
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Save output to file"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option(
    "--truncate-paths/--no-truncate-paths",
    default=None,
    show_default=False,
    help="Truncate displayed paths (e.g., src/.../module.py)",
)
@click.option(
    "--percentages/--no-percentages",
    default=None,
    show_default=False,
    help="Show or hide percentage columns in output",
)
@click.pass_obj
def compare(
    loader: ConfigLoader,
    project1: str,
    project2: str,
    format: str | None,
    output: Path | None,
    verbose: bool,
    no_color: bool,
    truncate_paths: bool | None,
    percentages: bool | None,
) -> None:
    """Compare metrics between two projects.

    Loads the latest scan results from two projects and displays a detailed
    comparison including absolute and percentage deltas for all metrics.

    Args:
        loader: The ConfigLoader instance.
        project1: Path to the first project directory.
        project2: Path to the second project directory.
        format: Output format (table, json, md, markdown).
        output: Path to save output file.
        verbose: Enable verbose output.
        no_color: Disable colored output.
        truncate_paths: Whether to truncate displayed paths.
        percentages: Whether to show percentage columns.
    """
    _setup_compare_config(
        loader,
        verbose,
        format,
        output,
        no_color,
        truncate_paths,
        percentages,
    )

    # Apply runtime color setting
    cast(_AppConsole, console).set_color_enabled(loader.config.core.color)

    handler = CompareHandler(loader.config)
    handler.execute(project1, project2, format, output)
