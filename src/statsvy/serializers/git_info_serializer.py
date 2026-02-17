"""Serialization logic for GitInfo data structures."""

from typing import Any

from statsvy.data.git_info import GitInfo


class GitInfoSerializer:
    """Handles conversion of GitInfo to dictionary representations.

    Separates serialization logic from the immutable GitInfo dataclass
    to maintain the data/logic boundary.
    """

    @staticmethod
    def to_dict(git_info: GitInfo) -> dict[str, Any]:
        """Return a JSON-serializable representation of the git info.

        Args:
            git_info: The GitInfo instance to serialize.

        Returns:
            A dictionary with git metadata fields.
        """
        return {
            "is_git_repo": git_info.is_git_repo,
            "remote_url": git_info.remote_url,
            "current_branch": git_info.current_branch,
            "commit_count": git_info.commit_count,
            "contributors": git_info.contributors,
            "last_commit_date": git_info.last_commit_date,
            "branches": git_info.branches,
            "commits_per_month_all_time": git_info.commits_per_month_all_time,
            "commits_last_30_days": git_info.commits_last_30_days,
        }
