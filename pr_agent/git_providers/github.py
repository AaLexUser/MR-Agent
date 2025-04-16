import os
import traceback
from typing import Optional, Tuple, List, Iterator
from datetime import datetime
from urllib.parse import urlparse
import re

from github import Auth, Github

from pr_agent.git_providers.base import MAX_FILES_ALLOWED_FULL, GitProvider
from pr_agent.log import get_logger
from pr_agent.types import EDIT_TYPE, FilePatchInfo
from pr_agent.algo.utils import load_large_diff


class GithubProvider(GitProvider):
    def __init__(
        self,
        repo_url: str,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ):
        self.max_comment_chars = 65000
        self.base_url = "https://api.github.com"
        self.exclude = exclude or []
        self.include = include or []

        self.client = self._create_client(self.base_url)
        self.repo_name = self._parse_repo_url(repo_url)
        self.repo = self.client.get_repo(self.repo_name)

    def get_pr_url(self) -> str:
        return self.pr.html_url

    @staticmethod
    def _create_client(base_url: str = "https://api.github.com"):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token is required when using user deployment.")
        auth = Auth.Token(token)
        if auth:
            return Github(auth=auth, base_url=base_url)
        else:
            raise ValueError("Could not authenticate to GitHub")

    @staticmethod
    def _parse_repo_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)

        if parsed_url.path.startswith("/api/v3"):
            parsed_url = urlparse(pr_url.replace("/api/v3", ""))

        path_parts = parsed_url.path.strip("/").split("/")
        print(path_parts)
        if len(path_parts) < 2:
            raise ValueError("The provided URL does not appear to be a GitHub URL")

        repo_name = "/".join(path_parts[:2])
        return repo_name

    @staticmethod
    def _parse_pr_url(pr_url: str) -> Tuple[str, int]:
        parsed_url = urlparse(pr_url)

        if parsed_url.path.startswith("/api/v3"):
            parsed_url = urlparse(pr_url.replace("/api/v3", ""))

        path_parts = parsed_url.path.strip("/").split("/")
        if "api.github.com" in parsed_url.netloc or "/api/v3" in pr_url:
            if len(path_parts) < 5 or path_parts[3] != "pulls":
                raise ValueError(
                    "The provided URL does not appear to be a GitHub PR URL"
                )
            repo_name = "/".join(path_parts[1:3])
            try:
                pr_number = int(path_parts[4])
            except ValueError as e:
                raise ValueError("Unable to convert PR number to integer") from e
            return repo_name, pr_number

        if len(path_parts) < 4 or path_parts[2] != "pull":
            raise ValueError("The provided URL does not appear to be a GitHub PR URL")

        repo_name = "/".join(path_parts[:2])
        try:
            pr_number = int(path_parts[3])
        except ValueError as e:
            raise ValueError("Unable to convert PR number to integer") from e

        return repo_name, pr_number

    def _get_file_content_at_commit(self, filepath, commit_sha):
        try:
            file_content = str(
                self.repo.get_contents(
                    filepath, ref=commit_sha
                ).decoded_content.decode()
            )
        except Exception:
            get_logger().error(f"Failed to get content for file: {filepath}")
            file_content = ""
        return file_content

    def get_diff_files(self, pr_url: str) -> list[FilePatchInfo]:
        repo_name, pr_number = self._parse_pr_url(pr_url)
        if repo_name != self.repo_name:
            raise ValueError(
                "The provided URL does not appear to be a GitHub PR URL for this repository"
            )
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        files = list(pr.get_files())
        try:
            diff_files = []
            try:
                compare = repo.compare(pr.base.sha, pr.head.sha)
                merge_base_commit = compare.merge_base_commit
            except Exception as e:
                get_logger().error(f"Failed to get merge base commit: {e}")
                merge_base_commit = pr.base
            if merge_base_commit.sha != pr.base.sha:
                get_logger().info(
                    f"Using merge base commit {merge_base_commit.sha} instead of base commit "
                )
            processed_file_count = 0
            filtered_files = [
                file
                for file in files
                if (
                    not self.include
                    or any(
                        re.search(pattern, file.filename) for pattern in self.include
                    )
                )
                and not any(
                    re.search(pattern, file.filename) for pattern in self.exclude
                )
            ]
            for file in filtered_files:
                patch = file.patch

                processed_file_count += 1
                skip_full_content = False
                if processed_file_count >= MAX_FILES_ALLOWED_FULL and patch:
                    skip_full_content = True
                    if processed_file_count == MAX_FILES_ALLOWED_FULL:
                        get_logger().info(
                            "Too many files in PR, will avoid loading full content for rest of files"
                        )

                if skip_full_content:
                    new_file_content = ""
                else:
                    new_file_content = self._get_file_content_at_commit(
                        file.filename, self.pr.head.sha
                    )
                if skip_full_content:
                    original_file_content = ""
                else:
                    original_file_content = self._get_file_content_at_commit(
                        file.filename, merge_base_commit.sha
                    )

                if not patch:
                    patch = load_large_diff(new_file_content, original_file_content)

                if file.status == "added":
                    edit_type = EDIT_TYPE.ADDED
                elif file.status == "removed":
                    edit_type = EDIT_TYPE.DELETED
                elif file.status == "renamed":
                    edit_type = EDIT_TYPE.RENAMED
                elif file.status == "modified":
                    edit_type = EDIT_TYPE.MODIFIED
                else:
                    get_logger().error(f"Unknown edit type: {file.status}")
                    edit_type = EDIT_TYPE.UNKNOWN

                # count number of lines added and removed
                if hasattr(file, "additions") and hasattr(file, "deletions"):
                    num_plus_lines = file.additions
                    num_minus_lines = file.deletions
                else:
                    patch_lines = patch.splitlines(keepends=True)
                    num_plus_lines = len(
                        [line for line in patch_lines if line.startswith("+")]
                    )
                    num_minus_lines = len(
                        [line for line in patch_lines if line.startswith("-")]
                    )
                diff_files.append(
                    FilePatchInfo(
                        base_file=original_file_content,
                        head_file=new_file_content,
                        patch=patch,
                        filename=file.filename,
                        edit_type=edit_type,
                        num_plus_lines=num_plus_lines,
                        num_minus_lines=num_minus_lines,
                    )
                )
            self.diff_files = diff_files
            return diff_files

        except Exception as e:
            get_logger().error(
                f"Failed to get diff files: {e}",
                artifact={"traceback": traceback.format_exc()},
            )
            raise e

    def get_closed_prs(
        self,
        author: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Iterator[str]:
        """Get closed PRs for a repository, optionally filtered by author and date range.

        Args:
            author: Optional GitHub username to filter PRs by
            since: Optional datetime to get PRs closed after this time
            until: Optional datetime to get PRs closed before this time

        Returns:
            List of PR URLs
        """
        prs = list(self.repo.get_pulls(state="closed", head=author, sort="updated", direction="desc"))
        for pr in prs:
            if pr.closed_at:
                if since and pr.closed_at < since:
                    continue
                if until and pr.closed_at > until:
                    continue
                yield pr.html_url
