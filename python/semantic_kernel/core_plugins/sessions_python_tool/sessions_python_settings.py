# Copyright (c) Microsoft. All rights reserved.

import re
import uuid
from enum import Enum
from typing import ClassVar
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator

from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel, KernelBaseSettings


class CodeInputType(str, Enum):
    """Code input type."""

    Inline = "inline"


class CodeExecutionType(str, Enum):
    """Code execution type."""

    Synchronous = "synchronous"
    # Asynchronous = "asynchronous" TODO: Enable when available


class SessionsPythonSettings(KernelBaseModel):
    """The Sessions Python code interpreter settings."""

    session_id: str | None = Field(default_factory=lambda: str(uuid.uuid4()), alias="identifier")
    code_input_type: CodeInputType | None = Field(default=CodeInputType.Inline, alias="codeInputType")
    execution_type: CodeExecutionType | None = Field(default=CodeExecutionType.Synchronous, alias="executionType")
    python_code: str | None = Field(alias="pythonCode", default=None)
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

    @field_validator("pool_management_endpoint", mode="before")
    @classmethod
    def _validate_endpoint(cls, endpoint: str) -> str:
        """Validates the pool management endpoint."""
        if "python/execute" in endpoint:
            endpoint_parsed = urlsplit(endpoint.replace("python/execute", ""))._asdict()
        else:
            endpoint_parsed = urlsplit(endpoint)._asdict()
        if endpoint_parsed["path"]:
            endpoint_parsed["path"] = re.sub("/{2,}", "/", endpoint_parsed["path"])
        else:
            endpoint_parsed["path"] = "/"
        return str(urlunsplit(endpoint_parsed.values()))
