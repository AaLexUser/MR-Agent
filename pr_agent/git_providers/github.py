from typing import Optional
import os
from pr_agent.git_providers.base import GitProvider
from github import Auth, Github

class GithubProvider(GitProvider):
    def __init__(self, pr_url: Optional[str] = None):
        self.repo_obj = None
        self.max_comment_chars = 65000
        self.pr_obj = None
        self.base_url = "https://github.com"
        
    def _get_github_client(self):
        try:
            token = os.getenv("GITHUB_TOKEN")
        except AttributeError as e:
            raise ValueError(
                "GitHub token is required when using user deployment.")
        self.auth = Auth.Token(token)
        if self.auth:
            return Github(auth=self.auth, base_url=self.base_url)
        else:
            raise ValueError("Could not authenticate to GitHub")
    