# Copyright (c) Microsoft. All rights reserved.

import re
import uuid
from enum import Enum
from typing import ClassVar
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator

from semantic_kernel.exceptions.function_exceptions import PluginInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel, KernelBaseSettings
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token


class CodeInputType(str, Enum):
    """Code input type."""

    Inline = "inline"


class CodeExecutionType(str, Enum):
    """Code execution type."""

    Synchronous = "synchronous"
    # Asynchronous = "asynchronous" TODO: Enable when available


class SessionsPythonSettings(KernelBaseModel):
    """The Sessions Python code interpreter settings."""

    session_id: str | None = Field(default_factory=lambda: str(uuid.uuid4()), alias="identifier", exclude=True)
    code_input_type: CodeInputType | None = Field(default=CodeInputType.Inline, alias="codeInputType")
    execution_type: CodeExecutionType | None = Field(default=CodeExecutionType.Synchronous, alias="executionType")
    python_code: str | None = Field(alias="code", default=None)
    timeout_in_sec: int | None = Field(default=100, alias="timeoutInSeconds")
    sanitize_input: bool | None = Field(default=True, alias="sanitizeInput")


class ACASessionsSettings(KernelBaseSettings):
    """Azure Container Apps sessions settings.

    Required:
    - pool_management_endpoint: HttpsUrl - The URL of the Azure Container Apps pool management endpoint.
        (Env var ACA_POOL_MANAGEMENT_ENDPOINT)
    """

    env_prefix: ClassVar[str] = "ACA_"

    pool_management_endpoint: HttpsUrl
    token_endpoint: str = "https://acasessions.io/.default"

    @field_validator("pool_management_endpoint", mode="before")
    @classmethod
    def _validate_endpoint(cls, endpoint: str) -> str:
        """Validates the pool management endpoint."""
        if "python/execute" in endpoint:
            endpoint_parsed = urlsplit(endpoint.replace("python/execute", ""))._asdict()
        else:
            endpoint_parsed = urlsplit(endpoint)._asdict()
        if endpoint_parsed["path"]:
            endpoint_parsed["path"] = re.sub(r"/{2,}", "/", endpoint_parsed["path"])
        else:
            endpoint_parsed["path"] = "/"
        return str(urlunsplit(endpoint_parsed.values()))

    def get_sessions_auth_token(self, token_endpoint: str | None = None) -> str | None:
        """Retrieve a Microsoft Entra Auth Token for a given token endpoint for the use with an Azure Container App.

        The required role for the token is `Azure ContainerApps Session Executor and Contributor`.
        The token endpoint may be specified as an environment variable, via the .env
        file or as an argument. If the token endpoint is not provided, the default is None.
        The `token_endpoint` argument takes precedence over the `token_endpoint` attribute.

        Args:
            token_endpoint: The token endpoint to use. Defaults to `https://acasessions.io/.default`.

        Returns:
            The Azure token or None if the token could not be retrieved.

        Raises:
            ServiceInitializationError: If the token endpoint is not provided.
        """
        endpoint_to_use = token_endpoint or self.token_endpoint
        if endpoint_to_use is None:
            raise PluginInitializationError("Please provide a token endpoint to retrieve the authentication token.")
        return get_entra_auth_token(endpoint_to_use)
