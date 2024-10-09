# Copyright (c) Microsoft. All rights reserved.


import httpx
from pydantic import BaseModel, Field

from semantic_kernel.functions.kernel_function_decorator import kernel_function

# region GitHub Models


class Repo(BaseModel):
    id: int = Field(..., alias="id")
    name: str = Field(..., alias="full_name")
    description: str | None = Field(None, alias="description")
    url: str = Field(..., alias="html_url")


class User(BaseModel):
    id: int = Field(..., alias="id")
    login: str = Field(..., alias="login")
    name: str | None = Field(None, alias="name")
    company: str | None = Field(None, alias="company")
    url: str = Field(..., alias="html_url")


class Label(BaseModel):
    id: int = Field(..., alias="id")
    name: str = Field(..., alias="name")
    description: str | None = Field(None, alias="description")


class Issue(BaseModel):
    id: int = Field(..., alias="id")
    number: int = Field(..., alias="number")
    url: str = Field(..., alias="html_url")
    title: str = Field(..., alias="title")
    state: str = Field(..., alias="state")
    labels: list[Label] = Field(..., alias="labels")
    when_created: str | None = Field(None, alias="created_at")
    when_closed: str | None = Field(None, alias="closed_at")


class IssueDetail(Issue):
    body: str | None = Field(None, alias="body")


# endregion


class GitHubSettings(BaseModel):
    base_url: str = "https://api.github.com"
    token: str


class GitHubPlugin:
    def __init__(self, settings: GitHubSettings):
        self.settings = settings

    @kernel_function
    async def get_user_profile(self) -> "User":
        async with self.create_client() as client:
            response = await self.make_request(client, "/user")
            return User(**response)

    @kernel_function
    async def get_repository(self, organization: str, repo: str) -> "Repo":
        async with self.create_client() as client:
            response = await self.make_request(client, f"/repos/{organization}/{repo}")
            return Repo(**response)

    @kernel_function
    async def get_issues(
        self,
        organization: str,
        repo: str,
        max_results: int | None = None,
        state: str = "",
        label: str = "",
        assignee: str = "",
    ) -> list["Issue"]:
        async with self.create_client() as client:
            path = f"/repos/{organization}/{repo}/issues?"
            path = self.build_query(path, "state", state)
            path = self.build_query(path, "assignee", assignee)
            path = self.build_query(path, "labels", label)
            path = self.build_query(path, "per_page", str(max_results) if max_results else "")
            response = await self.make_request(client, path)
            return [Issue(**issue) for issue in response]

    @kernel_function
    async def get_issue_detail(self, organization: str, repo: str, issue_id: int) -> "IssueDetail":
        async with self.create_client() as client:
            path = f"/repos/{organization}/{repo}/issues/{issue_id}"
            response = await self.make_request(client, path)
            return IssueDetail(**response)

    def create_client(self) -> httpx.AsyncClient:
        headers = {
            "User-Agent": "request",
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.settings.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        return httpx.AsyncClient(base_url=self.settings.base_url, headers=headers)

    @staticmethod
    def build_query(path: str, key: str, value: str) -> str:
        if value:
            return f"{path}{key}={value}&"
        return path

    @staticmethod
    async def make_request(client: httpx.AsyncClient, path: str) -> dict:
        print(f"REQUEST: {path}\n")
        response = await client.get(path)
        response.raise_for_status()
        return response.json()
