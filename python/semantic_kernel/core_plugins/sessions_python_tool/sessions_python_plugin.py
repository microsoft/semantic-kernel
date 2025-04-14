# Copyright (c) Microsoft. All rights reserved.

import inspect
import logging
import os
import re
from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Annotated, Any

from httpx import AsyncClient, HTTPStatusError
from pydantic import ValidationError

from semantic_kernel.const import USER_AGENT
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_settings import (
    ACASessionsSettings,
    SessionsPythonSettings,
)
from semantic_kernel.core_plugins.sessions_python_tool.sessions_remote_file_metadata import SessionsRemoteFileMetadata
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel
from semantic_kernel.utils.telemetry.user_agent import HTTP_USER_AGENT, version_info

logger = logging.getLogger(__name__)


SESSIONS_USER_AGENT = f"{HTTP_USER_AGENT}/{version_info} (Language=Python)"

SESSIONS_API_VERSION = "2024-02-02-preview"


class SessionsPythonTool(KernelBaseModel):
    """A plugin for running Python code in an Azure Container Apps dynamic sessions code interpreter."""

    pool_management_endpoint: HttpsUrl
    settings: SessionsPythonSettings
    auth_callback: Callable[..., Any | Awaitable[Any]]
    http_client: AsyncClient

    def __init__(
        self,
        auth_callback: Callable[..., Any | Awaitable[Any]] | None = None,
        pool_management_endpoint: str | None = None,
        settings: SessionsPythonSettings | None = None,
        http_client: AsyncClient | None = None,
        env_file_path: str | None = None,
        token_endpoint: str | None = None,
        **kwargs,
    ):
        """Initializes a new instance of the SessionsPythonTool class."""
        try:
            aca_settings = ACASessionsSettings(
                env_file_path=env_file_path,
                pool_management_endpoint=pool_management_endpoint,
                token_endpoint=token_endpoint,
            )
        except ValidationError as e:
            logger.error(f"Failed to load the ACASessionsSettings with message: {e!s}")
            raise FunctionInitializationError(f"Failed to load the ACASessionsSettings with message: {e!s}") from e

        if not settings:
            settings = SessionsPythonSettings()

        if not http_client:
            http_client = AsyncClient(timeout=5)

        if auth_callback is None:
            auth_callback = self._default_auth_callback(aca_settings)

        super().__init__(
            pool_management_endpoint=aca_settings.pool_management_endpoint,
            settings=settings,
            auth_callback=auth_callback,
            http_client=http_client,
            **kwargs,
        )

    # region Helper Methods
    def _default_auth_callback(self, aca_settings: ACASessionsSettings) -> Callable[..., Any | Awaitable[Any]]:
        """Generates a default authentication callback using the ACA settings."""
        token = aca_settings.get_sessions_auth_token()

        if token is None:
            raise FunctionInitializationError("Failed to retrieve the client auth token.")

        def auth_callback() -> str:
            """Retrieve the client auth token."""
            return token

        return auth_callback

    async def _ensure_auth_token(self) -> str:
        """Ensure the auth token is valid and handle both sync and async callbacks."""
        try:
            if inspect.iscoroutinefunction(self.auth_callback):
                auth_token = await self.auth_callback()
            else:
                auth_token = self.auth_callback()
        except Exception as e:
            logger.error(f"Failed to retrieve the client auth token with message: {e!s}")
            raise FunctionExecutionException(f"Failed to retrieve the client auth token with message: {e!s}") from e

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
        params["api-version"] = SESSIONS_API_VERSION
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        if not base_url.endswith("/"):
            base_url += "/"
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        return f"{base_url}{endpoint}?{query_string}"

    # endregion

    # region Kernel Functions
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

        self.http_client.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            USER_AGENT: SESSIONS_USER_AGENT,
        })

        self.settings.python_code = code

        request_body = {
            "properties": self.settings.model_dump(exclude_none=True, exclude={"sanitize_input"}, by_alias=True),
        }

        url = self._build_url_with_version(
            base_url=str(self.pool_management_endpoint),
            endpoint="code/execute/",
            params={"identifier": self.settings.session_id},
        )

        try:
            response = await self.http_client.post(
                url=url,
                json=request_body,
            )
            response.raise_for_status()
            result = response.json()["properties"]
            return (
                f"Status:\n{result['status']}\n"
                f"Result:\n{result['result']}\n"
                f"Stdout:\n{result['stdout']}\n"
                f"Stderr:\n{result['stderr']}"
            )
        except HTTPStatusError as e:
            error_message = e.response.text if e.response.text else e.response.reason_phrase
            raise FunctionExecutionException(
                f"Code execution failed with status code {e.response.status_code} and error: {error_message}"
            ) from e

    @kernel_function(name="upload_file", description="Uploads a file for the current Session ID")
    async def upload_file(
        self,
        *,
        local_file_path: Annotated[str, "The path to the local file on the machine"],
        remote_file_path: Annotated[
            str | None, "The remote path to the file in the session. Defaults to /mnt/data"
        ] = None,
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

        auth_token = await self._ensure_auth_token()
        self.http_client.headers.update({
            "Authorization": f"Bearer {auth_token}",
            USER_AGENT: SESSIONS_USER_AGENT,
        })

        url = self._build_url_with_version(
            base_url=str(self.pool_management_endpoint),
            endpoint="files/upload",
            params={"identifier": self.settings.session_id},
        )

        try:
            with open(local_file_path, "rb") as data:
                files = {"file": (remote_file_path, data, "application/octet-stream")}
                response = await self.http_client.post(url=url, files=files)
                response.raise_for_status()
                response_json = response.json()
                return SessionsRemoteFileMetadata.from_dict(response_json["value"][0]["properties"])
        except HTTPStatusError as e:
            error_message = e.response.text if e.response.text else e.response.reason_phrase
            raise FunctionExecutionException(
                f"Upload failed with status code {e.response.status_code} and error: {error_message}"
            ) from e

    @kernel_function(name="list_files", description="Lists all files in the provided Session ID")
    async def list_files(self) -> list[SessionsRemoteFileMetadata]:
        """List the files in the session pool.

        Returns:
            list[SessionsRemoteFileMetadata]: The metadata for the files in the session pool
        """
        auth_token = await self._ensure_auth_token()
        self.http_client.headers.update({
            "Authorization": f"Bearer {auth_token}",
            USER_AGENT: SESSIONS_USER_AGENT,
        })

        url = self._build_url_with_version(
            base_url=str(self.pool_management_endpoint),
            endpoint="files",
            params={"identifier": self.settings.session_id},
        )

        try:
            response = await self.http_client.get(
                url=url,
            )
            response.raise_for_status()
            response_json = response.json()
            return [SessionsRemoteFileMetadata.from_dict(entry["properties"]) for entry in response_json["value"]]
        except HTTPStatusError as e:
            error_message = e.response.text if e.response.text else e.response.reason_phrase
            raise FunctionExecutionException(
                f"List files failed with status code {e.response.status_code} and error: {error_message}"
            ) from e

    async def download_file(
        self,
        *,
        remote_file_name: Annotated[str, "The name of the file to download, relative to /mnt/data"],
        local_file_path: Annotated[str | None, "The local file path to save the file to, optional"] = None,
    ) -> Annotated[BytesIO | None, "The data of the downloaded file"]:
        """Download a file from the session pool.

        Args:
            remote_file_name: The name of the file to download, relative to `/mnt/data`.
            local_file_path: The path to save the downloaded file to. Should include the extension.
                If not provided, the file is returned as a BufferedReader.

        Returns:
            BufferedReader: The data of the downloaded file.
        """
        auth_token = await self._ensure_auth_token()
        self.http_client.headers.update({
            "Authorization": f"Bearer {auth_token}",
            USER_AGENT: SESSIONS_USER_AGENT,
        })

        url = self._build_url_with_version(
            base_url=str(self.pool_management_endpoint),
            endpoint=f"files/content/{remote_file_name}",
            params={"identifier": self.settings.session_id},
        )

        try:
            response = await self.http_client.get(
                url=url,
            )
            response.raise_for_status()
            if local_file_path:
                with open(local_file_path, "wb") as f:
                    f.write(response.content)
                return None

            return BytesIO(response.content)
        except HTTPStatusError as e:
            error_message = e.response.text if e.response.text else e.response.reason_phrase
            raise FunctionExecutionException(
                f"Download failed with status code {e.response.status_code} and error: {error_message}"
            ) from e
        # endregion
