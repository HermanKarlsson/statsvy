"""Line-based comment and blank line analysis."""

from pathlib import Path

from pygments import lex
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer_for_filename
from pygments.lexers.special import TextLexer
from pygments.token import Token
from pygments.util import ClassNotFound
from rich.text import Text

from statsvy.data.config import Config
from statsvy.utils.console import console


class LanguageAnalyzer:
    """Analyzes source code files to extract line-based statistics.

    This class leverages the Pygments library to identify programming languages
    and accurately distinguish between functional code, comments
    and empty lines regardless of the specific syntax.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the analyzer with configuration.

        Args:
            config: Config instance controlling verbosity.
        """
        self.config = config or Config.default()

    def analyze(self, file: Path, code: str) -> tuple[int, int]:
        """Analyzes the provided source code to count comments and blank lines.

        Attempts to automatically detect the programming language based on the
        filename. If detection fails, it falls back to a basic text lexer.

        Args:
            file: A Path object representing the
                    file (used for language detection).
            code: The raw string content of the source code.

        Returns:
            A tuple containing (comment_line_count, blank_line_count).
        """
        try:
            lexer = guess_lexer_for_filename(file.name, code)
        except (ClassNotFound, ValueError):
            lexer = TextLexer()
            if self.config.core.verbose:
                console.print(
                    Text("Language detection failed for ")
                    + Text(f"{file.name}", style="cyan")
                    + Text(" — falling back to TextLexer", style="dim")
                )

        if self.config.core.verbose:
            console.print(
                Text("Using ")
                + Text(f"{lexer}", style="magenta")
                + Text(" for ")
                + Text(f"{file.name}", style="cyan")
            )

        blank_lines = self._count_blank_lines(code)
        comment_lines = self._count_comment_lines(code, lexer)

        return (comment_lines, blank_lines)

    @staticmethod
    def _count_blank_lines(code: str) -> int:
        """Counts the total number of empty or whitespace-only lines.

        Args:
            code: The source code string to evaluate.

        Returns:
            The number of blank lines.
        """
        return sum(1 for line in code.splitlines() if not line.strip())

    @staticmethod
    def _count_comment_lines(code: str, lexer: Lexer) -> int:
        """Identifies unique lines containing comment tokens.

        Iterates through the token stream provided by the lexer.
        It tracks unique line indices to ensure that multi-line block comments
        and single-line comments are counted correctly based on the
        lines they occupy.

        Args:
            code: The source code string to tokenize.
            lexer: The Pygments lexer used for tokenization.

        Returns:
            The total number of unique lines that contain at least
            one comment token.
        """
        if isinstance(lexer, TextLexer):
            return sum(
                1
                for line in code.splitlines()
                if line.lstrip().startswith("#") or line.lstrip().startswith("//")
            )

        tokens = lex(code, lexer)
        comment_line_indices: set[int] = set()
        current_line = 1

        for token_type, token_value in tokens:
            parts = token_value.split("\n")
            if token_type in Token.Comment:
                for i in range(len(parts)):
                    if i == len(parts) - 1 and parts[i] == "":
                        continue
                    comment_line_indices.add(current_line + i)

            if len(parts) > 1:
                current_line += len(parts) - 1

        return len(comment_line_indices)
