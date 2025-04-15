from pr_agent.git_providers.base import GitProvider

class GitlabProvider(GitProvider):
    def __init__(self, pr_url: str, include: list[str] | None, exclude: list[str] | None):
        pass

    def get_pr_url(self) -> str:
        pass

