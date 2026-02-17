"""Git repository detection utilities."""

from datetime import datetime
from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from rich.text import Text

from statsvy.data.config import Config
from statsvy.data.git_info import GitInfo
from statsvy.utils.console import console


class GitStats:
    """Provides basic Git repository detection and analysis."""

    @staticmethod
    def detect_repository(path: Path, config: Config | None = None) -> GitInfo:
        """Detect Git metadata for the given path.

        Args:
            path: Path to the project root directory.
            config: Optional Config instance for verbose logging.

        Returns:
            GitInfo: Basic Git metadata for the directory, including
                commit count and contributors when available.
        """
        config = config or Config.default()

        try:
            repo = Repo(path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError):
            if config.core.verbose:
                console.print("No git repository found")
            return GitInfo(
                is_git_repo=False,
                remote_url=None,
                current_branch=None,
                commit_count=None,
                contributors=None,
                last_commit_date=None,
                branches=None,
                commits_per_month_all_time=None,
                commits_last_30_days=None,
            )

        if repo.bare:
            if config.core.verbose:
                console.print("Repository is bare, skipping detailed analysis")
            return GitInfo(
                is_git_repo=False,
                remote_url=None,
                current_branch=None,
                commit_count=None,
                contributors=None,
                last_commit_date=None,
                branches=None,
                commits_per_month_all_time=None,
                commits_last_30_days=None,
            )

        return GitStats._extract_git_metadata(repo, config)

    @staticmethod
    def _extract_git_metadata(repo: Repo, config: Config) -> GitInfo:
        """Extract metadata from a git repository.

        Args:
            repo: GitPython Repo object.
            config: Config instance for verbose logging.

        Returns:
            GitInfo object with extracted metadata.
        """
        remote_url = None
        if repo.remotes:
            remote_url = repo.remotes[0].url

        current_branch = None
        try:
            current_branch = repo.active_branch.name
        except (TypeError, ValueError, GitCommandError):
            current_branch = None

        commit_count = None
        try:
            commit_count = int(repo.git.rev_list("--count", "HEAD"))
        except (GitCommandError, ValueError):
            commit_count = None

        contributors = GitStats._get_contributors(repo, config.git.max_contributors)
        last_commit_date = GitStats._get_last_commit_date(repo)
        branches = GitStats._get_branches(repo)
        commits_per_month = GitStats._get_commits_per_month(repo)
        commits_last_30 = GitStats._get_commits_last_30_days(repo)

        if config.core.verbose:
            console.print(
                Text("Git repository detected: ")
                + Text("branch=", style="dim")
                + Text(current_branch or "unknown", style="cyan")
                + Text(", commits=", style="dim")
                + Text(str(commit_count) if commit_count else "unknown", style="cyan")
            )
            if contributors is None:
                console.print(
                    Text("Warning: contributors not available", style="yellow")
                )
            if commit_count is None:
                console.print(Text("Warning: commit count unavailable", style="yellow"))

        return GitInfo(
            is_git_repo=True,
            remote_url=remote_url,
            current_branch=current_branch,
            commit_count=commit_count,
            contributors=contributors,
            last_commit_date=last_commit_date,
            branches=branches,
            commits_per_month_all_time=commits_per_month,
            commits_last_30_days=commits_last_30,
        )

    @staticmethod
    def _get_contributors(repo: Repo, max_contributors: int = 5) -> list[str] | None:
        """Extract unique contributors from git repository.

        Args:
            repo: GitPython Repo object.
            max_contributors: Maximum number of contributors to return.

        Returns:
            Sorted list of unique contributor names (limited to max_contributors),
            or None if retrieval fails.
        """
        try:
            authors_output = repo.git.log("--format=%an")
            if not authors_output:
                return None
            authors = authors_output.split("\n")
            unique_authors = sorted(set(a.strip() for a in authors if a.strip()))
            return unique_authors[:max_contributors] if unique_authors else None
        except (GitCommandError, ValueError):
            return None

    @staticmethod
    def _get_last_commit_date(repo: Repo) -> str | None:
        """Extract the date of the most recent commit in ISO 8601 format.

        Args:
            repo: GitPython Repo object.

        Returns:
            ISO 8601 formatted date string, or None if retrieval fails.
        """
        try:
            commit_date = repo.git.log("-1", "--format=%cI")
            return commit_date if commit_date else None
        except (GitCommandError, ValueError):
            return None

    @staticmethod
    def _get_branches(repo: Repo, max_branches: int = 5) -> list[str] | None:
        """Extract branch names from the repository.

        Args:
            repo: GitPython Repo object.
            max_branches: Maximum number of branches to return.

        Returns:
            Sorted list of branch names (limited to max_branches), or None if fails.
        """
        try:
            branches_output = repo.git.branch("-a").strip()
            if not branches_output:
                return None
            branches = []
            for line in branches_output.split("\n"):
                branch = line.strip()
                if branch.startswith("* "):
                    branch = branch[2:].strip()
                if branch.startswith("remotes/"):
                    continue
                if branch:
                    branches.append(branch)
            unique_branches = sorted(set(branches))
            return unique_branches[:max_branches] if unique_branches else None
        except (GitCommandError, ValueError):
            return None

    @staticmethod
    def _get_commits_per_month(repo: Repo) -> float | None:
        """Calculate average commits per month across repo lifetime.

        Args:
            repo: GitPython Repo object.

        Returns:
            Average commits per month, or None if calculation fails.
        """
        try:
            commit_count = int(repo.git.rev_list("--count", "HEAD"))
            if commit_count == 0:
                return None

            first_commit_date = repo.git.log(
                "--diff-filter=A", "--follow", "-p", "--format=%cI"
            )
            if not first_commit_date:
                return None

            first_date_str = first_commit_date.strip().split("\n")[-1]
            first_date = datetime.fromisoformat(first_date_str)
            last_date = datetime.now(first_date.tzinfo)
            days_diff = (last_date - first_date).days
            months_diff = max(days_diff / 30.0, 1.0)

            return round(commit_count / months_diff, 2)
        except (GitCommandError, ValueError, IndexError):
            return None

    @staticmethod
    def _get_commits_last_30_days(repo: Repo) -> int | None:
        """Count commits in the last 30 days.

        Args:
            repo: GitPython Repo object.

        Returns:
            Number of commits in last 30 days, or None if retrieval fails.
        """
        try:
            count_str = repo.git.rev_list("--since=30 days ago", "--count", "HEAD")
            return int(count_str) if count_str else 0
        except (GitCommandError, ValueError):
            return None
