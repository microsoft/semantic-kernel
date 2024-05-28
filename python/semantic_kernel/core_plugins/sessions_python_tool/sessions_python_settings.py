# Copyright (c) Microsoft. All rights reserved.


import uuid
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings

from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel


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


class ACASessionsSettings(BaseSettings):
    """Azure Container Apps sessions settings.

    Required:
    - pool_management_endpoint: HttpsUrl - The URL of the Azure Container Apps pool management endpoint.
        (Env var ACA_POOL_MANAGEMENT_ENDPOINT)
    """

    env_file_path: str | None = None
    pool_management_endpoint: HttpsUrl

    class Config:
        """Configuration for the Azure Container Apps sessions settings."""

        env_prefix = "ACA_"
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        """Create an instance of the Azure Container Apps sessions settings."""
        if "env_file_path" in kwargs and kwargs["env_file_path"]:
            cls.Config.env_file = kwargs["env_file_path"]
        else:
            cls.Config.env_file = None
        return cls(**kwargs)
