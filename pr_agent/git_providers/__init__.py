from typing import Type, TypeVar, cast

from pr_agent.git_providers.base import GitProvider
from pr_agent.git_providers.github import GithubProvider
from pr_agent.git_providers.gitlab import GitlabProvider


T = TypeVar("T", bound=GitProvider)


# extract git provider name from repo_url
def parse_repo_url(repo_url: str) -> str:
    """
    Extract the git provider name from a repository URL.

    Args:
        repo_url: The repository URL

    Returns:
        The git provider name (github or gitlab)

    Raises:
        ValueError: If the git provider cannot be determined from the URL
    """
    repo_url = repo_url.lower()

    if "github" in repo_url:
        return "github"
    elif "gitlab" in repo_url:
        return "gitlab"
    else:
        raise ValueError(f"Could not determine git provider from URL: {repo_url}")


def get_git_provider(
    repo_url: str, include: list[str] | None, exclude: list[str] | None
) -> GitProvider:
    provider = parse_repo_url(repo_url)
    match provider:
        case "github":
            return GithubProvider(repo_url, include, exclude)
        case "gitlab":
            return GitlabProvider(repo_url, include, exclude)
        case _:
            raise ValueError(f"Unknown git provider: {provider}")
