# Copyright (c) Microsoft. All rights reserved.

from functools import reduce
from typing import Any, Union

import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel import Kernel

ServiceType = Union[ChatCompletionClientBase | TextCompletionClientBase]


class TestCompletionBase:
    """Base class for testing completion services."""

    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]:
        """Return completion services."""

    def setup(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
    ):
        """Setup the kernel with the completion service and function."""
        kernel.add_service(services[service_id][0])
        kernel.add_function(
            function_name="text",
            plugin_name="text",
            prompt="Perform the task: {{$input}}",
            prompt_execution_settings=services[service_id][1](**execution_settings_kwargs),
        )

    @pytest.mark.asyncio(scope="module")
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
    ) -> None:
        """Test completion service (Non-streaming).

        Args:
            kernel (Kernel): Kernel instance.
            service (str): Service name.
            services (dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]): Completion services.
            execution_settings_kwargs (dict[str, Any]): Execution settings keyword arguments.
            inputs (list[str]): List of input strings.
        """

    @pytest.mark.asyncio(scope="module")
    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
    ):
        """Test completion service (Streaming).

        Args:
            kernel (Kernel): Kernel instance.
            service (str): Service name.
            services (dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]): Completion services.
            execution_settings_kwargs (dict[str, Any]): Execution settings keyword arguments.
            inputs (list[str]): List of input strings.
        """

    async def execute_invoke(self, kernel: Kernel, input: str | ChatHistory, stream: bool) -> Any:
        """Invoke the kernel function and return the result.

        Args:
            kernel (Kernel): Kernel instance.
            input (str): Input string.
            stream (bool): Stream flag.
        """
        if stream:
            invocation = kernel.invoke_stream(function_name="text", plugin_name="text", input=input)
            parts = [part[0] async for part in invocation]
            if parts:
                response = reduce(lambda p, r: p + r, parts)
            else:
                raise AssertionError("No response")
        else:
            invocation = await kernel.invoke(function_name="text", plugin_name="text", input=input)
            assert invocation is not None
            response = invocation.value[0]

        return response

    def evaluate_response(self, response: Any, **kwargs):
        """Evaluate the response.

        Args:
            response (Any): Response.
            kwargs (dict[str, Any]): Keyword arguments.
        """
