"""Git repository metadata for tracked projects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitInfo:
    """Represents basic Git repository details.

    Attributes:
        is_git_repo: Whether the path is a Git repository.
        remote_url: Remote URL for the repository, if available.
        current_branch: Active branch name, if available.
        commit_count: Total number of commits, if available.
        contributors: List of unique contributor names, if available.
        last_commit_date: ISO 8601 formatted date of most recent commit.
        branches: List of branch names, limited by max configuration.
        commits_per_month_all_time: Average commits per month across repo lifetime.
        commits_last_30_days: Number of commits in the last 30 days.
    """

    is_git_repo: bool
    remote_url: str | None
    current_branch: str | None
    commit_count: int | None
    contributors: list[str] | None
    last_commit_date: str | None
    branches: list[str] | None
    commits_per_month_all_time: float | None
    commits_last_30_days: int | None
