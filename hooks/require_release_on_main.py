#!/usr/bin/env python3
"""Pre-commit "commit-msg" hook.

Reject commits made on branch `main` unless the commit subject starts with
`release`.

This script is intended to be used via `pre-commit` (stage: commit-msg). It
accepts a single argument: the path to the temporary commit message file that
Git provides to commit-msg hooks.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _current_branch() -> str | None:
    """Return current branch name, or None on error/detached HEAD."""
    git_exe = shutil.which("git")
    if git_exe is None:
        return None

    try:
        # Use the absolute path to the `git` executable to satisfy linters
        out = subprocess.run(
            [git_exe, "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S603
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _read_subject(commit_msg_path: Path) -> str:
    """Return the first non-empty line (subject) from the commit message."""
    text = commit_msg_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def main(argv: list[str]) -> int:
    """Main entrypoint for pre-commit hook.

    Args:
        argv: command-line arguments (pre-commit passes commit message file
            path as the first argument).

    Returns:
        Exit code (0 = success, non-zero = reject commit).
    """
    if not argv:
        # pre-commit should always provide the commit-msg file, but don't fail hard
        return 0

    commit_msg_file = Path(argv[0])
    branch = _current_branch()

    # Only enforce when committing on main (safe default otherwise)
    if branch != "main":
        return 0

    subject = _read_subject(commit_msg_file)
    if not subject.lower().startswith("release"):
        sys.stderr.write(
            "ERROR: Commits on branch 'main' must have a subject "
            "starting with 'release'.\n"
        )
        sys.stderr.write(f"Found subject: '{subject}'\n")
        sys.stderr.write(
            "Amend the commit (git commit --amend) or use a release "
            "commit message.\n"
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
