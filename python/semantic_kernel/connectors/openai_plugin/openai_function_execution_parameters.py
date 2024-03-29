# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from typing import Any, Awaitable, Callable

from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
    OpenAPIFunctionExecutionParameters,
)

OpenAIAuthCallbackType = Callable[..., Awaitable[Any]]


class OpenAIFunctionExecutionParameters(OpenAPIFunctionExecutionParameters):
    """OpenAI function execution parameters."""

    auth_callback: OpenAIAuthCallbackType | None = None
