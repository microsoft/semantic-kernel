# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Awaitable, Callable
from typing import Any

from typing_extensions import deprecated

from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
    OpenAPIFunctionExecutionParameters,
)

OpenAIAuthCallbackType = Callable[..., Awaitable[Any]]


@deprecated("The `OpenAIFunctionExecutionParameters` class is deprecated; use OpenAPI Plugins instead.", category=None)
class OpenAIFunctionExecutionParameters(OpenAPIFunctionExecutionParameters):
    """OpenAI function execution parameters."""

    auth_callback: OpenAIAuthCallbackType | None = None
