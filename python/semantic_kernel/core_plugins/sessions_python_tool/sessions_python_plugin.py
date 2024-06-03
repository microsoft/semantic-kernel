# Copyright (c) Microsoft. All rights reserved.

import logging
import os
import re
from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Annotated, Any

import httpx
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.const import USER_AGENT
from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT, version_info
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_settings import (
    ACASessionsSettings,
    SessionsPythonSettings,
)
from semantic_kernel.core_plugins.sessions_python_tool.sessions_remote_file_metadata import SessionsRemoteFileMetadata
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel

logger = logging.getLogger(__name__)


SESSIONS_USER_AGENT = f"{HTTP_USER_AGENT}/{version_info} (Language=Python)"

SESSIONS_API_VERSION = "2024-02-02-preview"


class SessionsPythonTool(KernelBaseModel):
    """A plugin for running Python code in an Azure Container Apps dynamic sessions code interpreter."""

    pool_management_endpoint: HttpsUrl
    settings: SessionsPythonSettings
    auth_callback: Callable[..., Awaitable[Any]]
    http_client: httpx.AsyncClient

    def __init__(
        self,
        auth_callback: Callable[..., Awaitable[Any]],
        pool_management_endpoint: str | None = None,
        settings: SessionsPythonSettings | None = None,
        http_client: httpx.AsyncClient | None = None,
        env_file_path: str | None = None,
        **kwargs,
    ):
        """Initializes a new instance of the SessionsPythonTool class."""
        try:
            aca_settings = ACASessionsSettings.create(
                env_file_path=env_file_path, pool_management_endpoint=pool_management_endpoint
            )
        except ValidationError as e:
            logger.error(f"Failed to load the ACASessionsSettings with message: {e!s}")
            raise FunctionInitializationError(f"Failed to load the ACASessionsSettings with message: {e!s}") from e

        if not settings:
            settings = SessionsPythonSettings()

        if not http_client:
            http_client = httpx.AsyncClient()

        super().__init__(
            pool_management_endpoint=aca_settings.pool_management_endpoint,
            settings=settings,
            auth_callback=auth_callback,
            http_client=http_client,
            **kwargs,
        )

    async def _ensure_auth_token(self) -> str:
        """Ensure the auth token is valid."""
        try:
            auth_token = await self.auth_callback()
        except Exception as e:
            logger.error(f"Failed to retrieve the client auth token with message: {e!s}")
            raise FunctionExecutionException(f"Failed to retrieve the client auth token with messages: {e!s}") from e

        return auth_token

    def _sanitize_input(self, code: str) -> str:
        """Sanitize input to the python REPL.

        Remove whitespace, backtick & python (if llm mistakes python console as terminal).

        Args:
            code (str): The query to sanitize
        Returns:
            str: The sanitized query
        """
        # Removes `, whitespace & python from start
        code = re.sub(r"^(\s|`)*(?i:python)?\s*", "", code)
        # Removes whitespace & ` from end
        return re.sub(r"(\s|`)*$", "", code)
    
    def _construct_remote_file_path(self, remote_file_path: str) -> str:
        """Construct the remote file path.

        Args:
            remote_file_path (str): The remote file path.

        Returns:
            str: The remote file path.
        """
        if not remote_file_path.startswith("/mnt/data/"):
            remote_file_path = f"/mnt/data/{remote_file_path}"
        return remote_file_path

    def _build_url_with_version(self, base_url, endpoint, params):
        """Builds a URL with the provided base URL, endpoint, and query parameters."""
        params['api-version'] = SESSIONS_API_VERSION
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        return f"{base_url}{endpoint}?{query_string}"

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
        """Executes the provided Python code.

        Args:
            code (str): The valid Python code to execute
        Returns:
            str: The result of the Python code execution in the form of Result, Stdout, and Stderr
        Raises:
            FunctionExecutionException: If the provided code is empty.
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

        url = self._build_url_with_version(
            base_url=self.pool_management_endpoint,
            endpoint="python/execute/",
            params={"identifier": self.settings.session_id},
        )

        response = await self.http_client.post(
            url=url,
            json=request_body,
        )
        response.raise_for_status()

        result = response.json()
        return f"Result:\n{result['result']}Stdout:\n{result['stdout']}Stderr:\n{result['stderr']}"

    @kernel_function(name="upload_file", description="Uploads a file for the current Session ID")
    async def upload_file(
        self,
        *,
        local_file_path: Annotated[str, "The path to the local file on the machine"],
        remote_file_path: Annotated[str | None, "The remote path to the file in the session. Defaults to /mnt/data"] = None,  # noqa: E501
    ) -> Annotated[SessionsRemoteFileMetadata, "The metadata of the uploaded file"]:
        """Upload a file to the session pool.

        Args:
            remote_file_path (str): The path to the file in the session.
            local_file_path (str): The path to the file on the local machine.

        Returns:
            RemoteFileMetadata: The metadata of the uploaded file.

        Raises:
            FunctionExecutionException: If local_file_path is not provided.
        """
        if not local_file_path:
            raise FunctionExecutionException("Please provide a local file path to upload.")

        remote_file_path = self._construct_remote_file_path(remote_file_path or os.path.basename(local_file_path))

        with open(local_file_path, "rb") as data:
            auth_token = await self._ensure_auth_token()
            self.http_client.headers.update(
                {
                    "Authorization": f"Bearer {auth_token}",
                    USER_AGENT: SESSIONS_USER_AGENT,
                }
            )
            files = [("file", (remote_file_path, data, "application/octet-stream"))]

            url = self._build_url_with_version(
                base_url=self.pool_management_endpoint,
                endpoint="python/uploadFile",
                params={"identifier": self.settings.session_id},
            )

            response = await self.http_client.post(
                url=url,
                json={},
                files=files,  # type: ignore
            )

            response.raise_for_status()

            response_json = response.json()
            return SessionsRemoteFileMetadata.from_dict(response_json['$values'][0])

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

        url = self._build_url_with_version(
            base_url=self.pool_management_endpoint,
            endpoint="python/files",
            params={"identifier": self.settings.session_id}
        )

        response = await self.http_client.get(
            url=url,
        )
        response.raise_for_status()

        response_json = response.json()
        return [SessionsRemoteFileMetadata.from_dict(entry) for entry in response_json["$values"]]

    async def download_file(self, *, remote_file_path: str, local_file_path: str | None = None) -> BytesIO | None:
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

        url = self._build_url_with_version(
            base_url=self.pool_management_endpoint,
            endpoint="python/downloadFile",
            params={
                "identifier": self.settings.session_id,
                "filename": remote_file_path
            }
        )

        response = await self.http_client.get(
            url=url,
        )
        response.raise_for_status()

        if local_file_path:
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            return None

        return BytesIO(response.content)
