from typing import Type, TypeVar, cast

from pr_agent.git_providers.base import GitProvider
from pr_agent.git_providers.github import GithubProvider
from pr_agent.git_providers.gitlab import GitlabProvider


T = TypeVar("T", bound=GitProvider)


def get_git_provider(provider: str, pr_url: str, include: list[str] | None, exclude: list[str] | None) -> T:
    match provider:
        case "github":
            return cast(T, GithubProvider(pr_url, include, exclude))
        case "gitlab":
            return cast(T, GitlabProvider(pr_url, include, exclude))
        case _:
            raise ValueError(f"Unknown git provider: {provider}")
