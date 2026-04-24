from github import Github, GithubException
import os

class RepoManagerAgent:
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.g = Github(self.github_token) if self.github_token else None

    async def create_repo(self, repo_name: str, description: str = "", private: bool = True) -> dict:
        if not self.g:
            return {"error": "GitHub token not configured"}
        try:
            user = self.g.get_user()
            repo = user.create_repo(repo_name, private=private, description=description)
            return {"url": repo.html_url, "clone_url": repo.clone_url, "success": True}
        except GithubException as e:
            return {"error": str(e), "success": False}

    async def push_files(self, repo_name: str, files: dict, commit_message: str = "Initial AI-generated code"):
        """files = {"path/to/file.py": "content", ...}"""
        if not self.g:
            return {"error": "No token"}
        try:
            user = self.g.get_user()
            repo = user.get_repo(repo_name)
            # Assume repo is empty; create files one by one on main
            for file_path, content in files.items():
                try:
                    repo.create_file(file_path, commit_message, content, branch="main")
                except GithubException:
                    # try update if exists
                    try:
                        existing = repo.get_contents(file_path)
                        repo.update_file(file_path, commit_message, content, existing.sha, branch="main")
                    except Exception:
                        # skip
                        pass
            return {"success": True, "message": f"Pushed {len(files)} files"}
        except Exception as e:
            return {"error": str(e), "success": False}
