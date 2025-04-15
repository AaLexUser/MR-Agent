import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Tuple

from pr_agent.log import get_logger
from pr_agent.types import FilePatchInfo

MAX_FILES_ALLOWED_FULL = 50


class GitProvider(ABC):
    """
    Abstract base class for Git providers (GitHub, GitLab, BitBucket, etc.).

    This class defines the interface that all git provider implementations
    must adhere to. It provides methods to interact with repositories, PRs,
    and issues across different git hosting platforms.

    Implementations should handle the specifics of each git provider's API
    and authentication mechanisms.
    """

    # @abstractmethod
    # def is_supported(self, capability: str) -> bool:
    #     """
    #     Check if a specific capability is supported by this git provider.

    #     Args:
    #         capability: String identifier of the capability to check.
    #                     Examples might include 'pull_requests', 'issues', etc.

    #     Returns:
    #         bool: True if the capability is supported, False otherwise.
    #     """
    #     pass

    def get_git_repo_url(self, issues_or_pr_url: str) -> str:
        """
        Given a URL from an issue or pull request/merge request, extracts and returns the corresponding Git repository URL.

        Args:
            issues_or_pr_url (str): URL of an issue or pull/merge request from the repository

        Returns:
            str: The .git URL of the repository. Returns empty string if not implemented.

        Notes:
            This is an abstract method that needs to be implemented by specific Git provider classes.
        """

        get_logger().warning("Not implemented! Returning empty url")
        return ""

    def get_canonical_url_parts(
        self, repo_git_url: str, desired_branch: str
    ) -> Tuple[str, str]:
        """
        Get the canonical URL prefix and suffix for viewing files in a given repository.

        This method splits a repository URL into prefix and suffix components needed to construct
        canonical URLs for viewing files in that repository.

        Args:
            repo_git_url (str): The Git repository URL (e.g. https://git_provider.com/MY_PROJECT/MY_REPO.git)
            desired_branch (str): The branch name to use in the URL

        Returns:
            Tuple[str, str]: A tuple containing:
                - prefix (str): The URL prefix before the file path
                - suffix (str): The URL suffix after the file path

        Example:
            For inputs:
                repo_git_url = "https://git_provider.com/MY_PROJECT/MY_REPO.git"
                desired_branch = "main"

            Returns:
                ("https://git_provider.com/projects/MY_PROJECT/repos/MY_REPO/browse/main", "?raw")

            Which allows constructing file URLs like:
            {prefix}/docs/readme.md{suffix}
        """

        get_logger().warning("Not implemented! Returning empty prefix and suffix")
        return ("", "")

    # Clone related API
    # An object which ensures deletion of a cloned repo, once it becomes out of scope.
    # Example usage:
    #    with TemporaryDirectory() as tmp_dir:
    #            returned_obj: GitProvider.ScopedClonedRepo = self.git_provider.clone(self.repo_url, tmp_dir, remove_dest_folder=False)
    #            print(returned_obj.path) #Use returned_obj.path.
    #    #From this point, returned_obj.path may be deleted at any point and therefore must not be used.
    class ScopedClonedRepo(object):
        def __init__(self, dest_folder):
            self.path = dest_folder

        def __del__(self):
            if self.path and os.path.exists(self.path):
                shutil.rmtree(self.path, ignore_errors=True)

    # Method to allow implementors to manipulate the repo url to clone (such as embedding tokens in the url string). Needs to be implemented by the provider.
    def _prepare_clone_url_with_token(self, repo_url_to_clone: str) -> str | None:
        get_logger().warning("Not implemented! Returning None")
        return None

    # Does a shallow clone, using a forked process to support a timeout guard.
    # In case operation has failed, it is expected to throw an exception as this method does not return a value.
    def _clone_inner(
        self, repo_url: str, dest_folder: str, operation_timeout_in_seconds: int = None
    ) -> None:
        # The following ought to be equivalent to:
        # #Repo.clone_from(repo_url, dest_folder)
        # , but with throwing an exception upon timeout.
        # Note: This can only be used in context that supports using pipes.
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--depth",
                "1",
                repo_url,
                dest_folder,
            ],
            check=True,  # check=True will raise an exception if the command fails
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=operation_timeout_in_seconds,
        )

    CLONE_TIMEOUT_SEC = 20

    # Clone a given url to a destination folder. If successful, returns an object that wraps the destination folder,
    # deleting it once it is garbage collected. See: GitProvider.ScopedClonedRepo for more details.
    def clone(
        self,
        repo_url_to_clone: str,
        dest_folder: str,
        remove_dest_folder: bool = True,
        operation_timeout_in_seconds: int = CLONE_TIMEOUT_SEC,
    ) -> ScopedClonedRepo | None:
        returned_obj = None
        clone_url = self._prepare_clone_url_with_token(repo_url_to_clone)
        if not clone_url:
            get_logger().error("Clone failed: Unable to obtain url to clone.")
            return returned_obj
        try:
            if (
                remove_dest_folder
                and os.path.exists(dest_folder)
                and os.path.isdir(dest_folder)
            ):
                shutil.rmtree(dest_folder)
            self._clone_inner(clone_url, dest_folder, operation_timeout_in_seconds)
            returned_obj = GitProvider.ScopedClonedRepo(dest_folder)
        except Exception as e:
            get_logger().exception(
                "Clone failed: Could not clone url.",
                artifact={
                    "error": str(e),
                    "url": clone_url,
                    "dest_folder": dest_folder,
                },
            )
        finally:
            return returned_obj

    # @abstractmethod
    # def get_files(self) -> list:
    #     pass

    # @abstractmethod
    # def get_diff_files(self) -> list[FilePatchInfo]:
    #     pass

    # @abstractmethod
    # def publish_description(self, pr_title: str, pr_body: str):
    #     pass

    # @abstractmethod
    # def publish_code_suggestions(self, code_suggestions: list) -> bool:
    #     pass

    # @abstractmethod
    # def get_languages(self):
    #     pass

    # @abstractmethod
    # def get_pr_branch(self):
    #     pass

    # @abstractmethod
    # def get_user_id(self):
    #     pass

    # @abstractmethod
    # def get_pr_description_full(self) -> str:
    #     pass

    # @abstractmethod
    # def edit_comment(self, comment, body: str):
    #     pass

    # @abstractmethod
    # def edit_comment_from_comment_id(self, comment_id: int, body: str):
    #     pass

    # @abstractmethod
    # def get_comment_body_from_comment_id(self, comment_id: int) -> str:
    #     pass

    # @abstractmethod
    # def reply_to_comment_from_comment_id(self, comment_id: int, body: str):
    #     pass
