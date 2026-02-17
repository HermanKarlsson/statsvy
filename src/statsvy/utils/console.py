"""Shared Rich console wrapper for app output.

This module exposes a stable `console` object used across the application.
The object is a thin wrapper around Rich's `Console` so we can toggle
colour output at runtime (used by the CLI `--no-color` flag) without
requiring all consumers to re-import anything.
"""

from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, cast

from rich.console import Console, RenderableType

if TYPE_CHECKING:
    # Import types used only for static checking
    from rich.console import Capture as _RichCapture


class _AppConsole:
    """Minimal wrapper that delegates to a Rich Console instance.

    Consumers import `console` from this module and keep a reference to
    the same wrapper object. The wrapper recreates its internal Rich
    Console when `set_color_enabled()` is called so the colour behaviour
    can be changed at runtime without rebinding the `console` symbol.
    """

    def __init__(self, color_enabled: bool = True) -> None:
        """Create a new wrapper around a Rich Console.

        Args:
            color_enabled: Whether ANSI colour output is enabled by default.
        """
        self._color_enabled = color_enabled
        self.quiet = False
        self._recreate()

    def _recreate(self) -> None:
        color_system = "auto" if self._color_enabled else None
        # force_terminal left as default; disabling colour is sufficient
        self._console: Console = Console(color_system=color_system, log_time=False)

    def set_color_enabled(self, enabled: bool) -> None:
        """Enable or disable ANSI colour output at runtime.

        This recreates the underlying Rich Console so subsequent output
        uses the new colour setting.
        """
        self._color_enabled = enabled
        self._recreate()

    # Delegate a small surface area used in the codebase
    def print(self, *objects: object, **kwargs: object) -> None:
        """Print objects to the underlying Rich Console unless `quiet`.

        Behaves the same as `rich.console.Console.print` and forwards all
        positional and keyword arguments.
        """
        if self.quiet:
            return
        # Forward arguments to Rich Console.print — cast to satisfy type checking
        return self._console.print(*objects, **cast(dict[str, Any], kwargs))

    def capture(
        self, *args: object, **kwargs: object
    ) -> AbstractContextManager["_RichCapture"]:
        r"""Return a context manager that captures console output as text.

        Example:
            with console.capture() as c:
                console.print("hello")
            assert c.get() == "hello\n"
        """
        # Forward to Rich API (cast for compatible kwarg types)
        return self._console.capture(*args, **cast(dict[str, Any], kwargs))

    def status(
        self, status: "RenderableType", *args: object, **kwargs: object
    ) -> AbstractContextManager[object]:
        """Return a Rich `Status` context manager for transient messages.

        Args:
            status: A renderable status message (string or Text).
            *args: Additional positional arguments forwarded to Rich.
            **kwargs: Keyword arguments forwarded to Rich's API.

        Forwards remaining arguments to `rich.console.Console.status`.
        """
        # Forward to Rich API (cast for compatible kwarg types)
        return self._console.status(status, *args, **cast(dict[str, Any], kwargs))

    # Fallback attr access to the underlying Console for other usages
    def __getattr__(self, name: str) -> object:
        """Forward attribute access to the internal Rich Console."""
        return getattr(self._console, name)

    # Support context-manager protocol because Rich uses ``with console:`` in
    # several helpers (e.g. Live / Progress). Delegate to the underlying
    # Console but return the wrapper so callers continue to receive the
    # shared object.
    def __enter__(self) -> "_AppConsole":
        """Enter context and return the wrapper (delegates to Console)."""
        self._console.__enter__()
        return self

    def __exit__(
        self, exc_type: type | None, exc: BaseException | None, tb: object | None
    ) -> None:
        """Exit context by delegating to the underlying Console."""
        return self._console.__exit__(exc_type, exc, tb)


# Single shared wrapper instance used throughout the codebase
console: Console = cast(Console, _AppConsole())
