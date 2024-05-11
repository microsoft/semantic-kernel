# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import logging
import os
import re
from io import BufferedReader, BytesIO
from typing import Annotated, Any, Awaitable, Callable

import httpx
from pydantic import field_validator

from semantic_kernel.connectors.ai.open_ai.const import USER_AGENT
from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT, version_info
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_settings import (
    SessionsPythonSettings,
)
from semantic_kernel.core_plugins.sessions_python_tool.sessions_remote_file_metadata import SessionsRemoteFileMetadata
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


SESSIONS_USER_AGENT = f"{HTTP_USER_AGENT}/{version_info} (Language=Python)"


class SessionsPythonTool(KernelBaseModel):
    """A plugin for running Python code in an Azure Container Apps dynamic sessions code interpreter."""

    pool_management_endpoint: str
    settings: SessionsPythonSettings | None = None
    auth_callback: Callable[..., Awaitable[Any]]
    http_client: httpx.AsyncClient | None = None

    def __init__(
        self,
        pool_management_endpoint: str,
        auth_callback: Callable[..., Awaitable[Any]],
        settings: SessionsPythonSettings | None = None,
        http_client: httpx.AsyncClient | None = None,
        **kwargs,
    ):
        """Initializes a new instance of the SessionsPythonTool class."""
        if not settings:
            settings = SessionsPythonSettings()

        if not http_client:
            http_client = httpx.AsyncClient()

        super().__init__(
            pool_management_endpoint=pool_management_endpoint,
            auth_callback=auth_callback,
            settings=settings,
            http_client=http_client,
            **kwargs,
        )

    @field_validator("pool_management_endpoint", mode="before")
    @classmethod
    def _validate_endpoint(cls, endpoint: str):
        """Validates the pool management endpoint."""
        if "/python/execute" in endpoint:
            # Remove '/python/execute/' and ensure the endpoint ends with a '/'
            endpoint = endpoint.replace("/python/execute", "").rstrip("/") + "/"
        if not endpoint.endswith("/"):
            # Ensure the endpoint ends with a '/'
            endpoint = endpoint + "/"
        return endpoint

    async def _ensure_auth_token(self) -> str:
        """Ensure the auth token is valid."""

        try:
            auth_token = await self.auth_callback()
        except Exception as e:
            logger.error(f"Failed to retrieve the client auth token with message: {str(e)}")
            raise FunctionExecutionException(f"Failed to retrieve the client auth token with messages: {str(e)}") from e

        return auth_token

    def _sanitize_input(self, code: str) -> str:
        """Sanitize input to the python REPL.
        Remove whitespace, backtick & python (if llm mistakes python console as terminal)
        Args:
            query: The query to sanitize
        Returns:
            str: The sanitized query
        """

        # Removes `, whitespace & python from start
        code = re.sub(r"^(\s|`)*(?i:python)?\s*", "", code)
        # Removes whitespace & ` from end
        code = re.sub(r"(\s|`)*$", "", code)
        return code

    @kernel_function(
        description="""Executes the provided Python code.
                     Start and end the code snippet with double quotes to define it as a string.
                     Insert \\n within the string wherever a new line should appear.
                     Add spaces directly after \\n sequences to replicate indentation.
                     Use \" to include double quotes within the code without ending the string.
                     Keep everything in a single line; the \\n sequences will represent line breaks
                     when the string is processed or displayed.
                     """,
        name="execute_code",
    )
    async def execute_code(self, code: Annotated[str, "The valid Python code to execute"]) -> str:
        """
        Executes the provided Python code
        Args:
            code (str): The valid Python code to execute
        Returns:
            str: The result of the Python code execution in the form of Result, Stdout, and Stderr
        Raises:
            FunctionExecutionException: If the provided code is empty
        """

        if not code:
            raise FunctionExecutionException("The provided code is empty")

        if self.settings.sanitize_input:
            code = self._sanitize_input(code)

        auth_token = await self._ensure_auth_token()

        logger.info(f"Executing Python code: {code}")

        self.http_client.headers.update(
            {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
                USER_AGENT: SESSIONS_USER_AGENT,
            }
        )

        self.settings.python_code = code

        request_body = {
            "properties": self.settings.model_dump(exclude_none=True, exclude={"sanitize_input"}, by_alias=True),
        }

        response = await self.http_client.post(
            url=f"{self.pool_management_endpoint}python/execute/",
            json=request_body,
        )
        response.raise_for_status()

        result = response.json()
        return f"Result:\n{result['result']}Stdout:\n{result['stdout']}Stderr:\n{result['stderr']}"  # noqa: E501

    @kernel_function(name="upload_file", description="Uploads a file for the current Session ID")
    async def upload_file(
        self, *, data: BufferedReader = None, remote_file_path: str = None, local_file_path: str = None
    ) -> SessionsRemoteFileMetadata:
        """Upload a file to the session pool.
        Args:
            data (BufferedReader): The file data to upload.
            remote_file_path (str): The path to the file in the session.
            local_file_path (str): The path to the file on the local machine.
        Returns:
            RemoteFileMetadata: The metadata of the uploaded file.
        """

        if data and local_file_path:
            raise ValueError("data and local_file_path cannot be provided together")

        if local_file_path:
            if not remote_file_path:
                remote_file_path = os.path.basename(local_file_path)
            data = open(local_file_path, "rb")

        auth_token = await self._ensure_auth_token()
        self.http_client.headers.update(
            {
                "Authorization": f"Bearer {auth_token}",
                USER_AGENT: SESSIONS_USER_AGENT,
            }
        )
        files = [("file", (remote_file_path, data, "application/octet-stream"))]

        response = await self.http_client.post(
            url=f"{self.pool_management_endpoint}python/uploadFile?identifier={self.settings.session_id}",
            json={},
            files=files,
        )

        response.raise_for_status()

        response_json = response.json()
        return SessionsRemoteFileMetadata.from_dict(response_json)

    @kernel_function(name="list_files", description="Lists all files in the provided Session ID")
    async def list_files(self) -> list[SessionsRemoteFileMetadata]:
        """List the files in the session pool.
        Returns:
            list[SessionsRemoteFileMetadata]: The metadata for the files in the session pool
        """
        auth_token = await self._ensure_auth_token()
        self.http_client.headers.update(
            {
                "Authorization": f"Bearer {auth_token}",
                USER_AGENT: SESSIONS_USER_AGENT,
            }
        )

        response = await self.http_client.get(
            url=f"{self.pool_management_endpoint}python/files?identifier={self.settings.session_id}",
        )
        response.raise_for_status()

        response_json = response.json()
        return [SessionsRemoteFileMetadata.from_dict(entry) for entry in response_json["$values"]]

    async def download_file(self, *, remote_file_path: str, local_file_path: str = None) -> BufferedReader | None:
        """Download a file from the session pool.
        Args:
            remote_file_path: The path to download the file from, relative to `/mnt/data`.
            local_file_path: The path to save the downloaded file to. If not provided, the
                file is returned as a BufferedReader.
        Returns:
            BufferedReader: The data of the downloaded file.
        """
        auth_token = await self.auth_callback()
        self.http_client.headers.update(
            {
                "Authorization": f"Bearer {auth_token}",
                USER_AGENT: SESSIONS_USER_AGENT,
            }
        )

        response = await self.http_client.get(
            url=f"{self.pool_management_endpoint}python/downloadFile?identifier={self.settings.session_id}&filename={remote_file_path}",  # noqa: E501
        )
        response.raise_for_status()

        if local_file_path:
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            return None

        return BytesIO(response.content)
