"""GitHub repository management client."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CLONE_BASE = os.path.join(tempfile.gettempdir(), "repos")


class GitHubClient:
    """Async helper for GitHub API calls and local git operations."""

    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.github_token
        self.api_url = "https://api.github.com"

    @property
    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ----- High-level helpers -------------------------------------------

    async def clone_repository(self, repo_url: str, dest: Optional[str] = None) -> str:
        """Clone *repo_url* into *dest* (or a temp directory) and return the path."""
        name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
        dest = dest or os.path.join(CLONE_BASE, name)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        clone_url = repo_url
        if self.token and "github.com" in repo_url:
            clone_url = repo_url.replace(
                "https://", f"https://x-access-token:{self.token}@"
            )

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth=1", clone_url, dest,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode()
            if self.token:
                error_msg = error_msg.replace(self.token, "***")
            raise RuntimeError(f"git clone failed: {error_msg}")
        logger.info("Cloned %s → %s", repo_url, dest)
        return dest

    async def analyze_repository(self, repo_url: str) -> dict[str, Any]:
        """Return basic structural info about a repository."""
        owner_repo = self._extract_owner_repo(repo_url)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_url}/repos/{owner_repo}",
                headers=self._headers,
            )
            resp.raise_for_status()
            repo_data = resp.json()

            resp_langs = await client.get(
                f"{self.api_url}/repos/{owner_repo}/languages",
                headers=self._headers,
            )
            resp_langs.raise_for_status()
            languages = resp_langs.json()

        return {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "default_branch": repo_data.get("default_branch"),
            "language": repo_data.get("language"),
            "languages": languages,
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "open_issues": repo_data.get("open_issues_count"),
            "url": repo_data.get("html_url"),
        }

    async def create_branch(
        self, owner_repo: str, branch_name: str, from_branch: str = "main"
    ) -> dict[str, Any]:
        """Create a new branch from *from_branch*."""
        async with httpx.AsyncClient(timeout=30) as client:
            ref_resp = await client.get(
                f"{self.api_url}/repos/{owner_repo}/git/ref/heads/{from_branch}",
                headers=self._headers,
            )
            ref_resp.raise_for_status()
            sha = ref_resp.json()["object"]["sha"]

            create_resp = await client.post(
                f"{self.api_url}/repos/{owner_repo}/git/refs",
                headers=self._headers,
                json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            )
            create_resp.raise_for_status()
            logger.info("Branch '%s' created on %s", branch_name, owner_repo)
            return create_resp.json()

    async def create_pull_request(
        self,
        owner_repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> dict[str, Any]:
        """Open a pull request."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_url}/repos/{owner_repo}/pulls",
                headers=self._headers,
                json={
                    "title": title,
                    "head": head,
                    "base": base,
                    "body": body,
                },
            )
            resp.raise_for_status()
            pr_data = resp.json()
            logger.info("PR #%s created on %s", pr_data.get("number"), owner_repo)
            return pr_data

    async def get_repo_contents(
        self, owner_repo: str, path: str = "", ref: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """List directory contents of a repo path."""
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_url}/repos/{owner_repo}/contents/{path}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return [data]
            return data

    # ----- Internals ----------------------------------------------------

    @staticmethod
    def _extract_owner_repo(url: str) -> str:
        """Extract ``owner/repo`` from a GitHub URL or pass-through."""
        url = url.rstrip("/").removesuffix(".git")
        if "github.com" in url:
            parts = url.split("github.com/")[-1]
            return parts
        return url


_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
