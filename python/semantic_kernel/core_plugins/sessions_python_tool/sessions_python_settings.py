# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


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
