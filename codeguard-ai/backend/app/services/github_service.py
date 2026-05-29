import os
import subprocess
from github import Github
from app.core.config import settings

class GitHubService:
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.github_client = Github(self.access_token) if self.access_token else None

    def clone_repository(self, repo_url: str, dest_dir: str) -> str:
        """
        Clones a repository to a local directory for scanning.
        """
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        try:
            # Using subprocess to run git clone
            subprocess.run(
                ["git", "clone", repo_url, dest_dir],
                capture_output=True,
                check=True,
                text=True
            )
            return dest_dir
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone repository: {e.stderr}")

    def create_pull_request(self, repo_full_name: str, branch_name: str, title: str, body: str):
        """
        Creates a PR with automated AI fix suggestions.
        """
        if not self.github_client:
            raise Exception("GitHub client not initialized with access token")
            
        repo = self.github_client.get_repo(repo_full_name)
        
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=repo.default_branch
        )
        return pr.html_url
