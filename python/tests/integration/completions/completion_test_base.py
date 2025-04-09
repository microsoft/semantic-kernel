# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel import Kernel

ServiceType = ChatCompletionClientBase | TextCompletionClientBase


class CompletionTestBase:
    """Base class for testing completion services."""

    def services(self) -> dict[str, tuple["ServiceType", type[PromptExecutionSettings]]]:
        """Return completion services."""
        raise NotImplementedError

    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
    ) -> None:
        """Test completion service (Non-streaming).

        Args:
            kernel (Kernel): Kernel instance.
            service_id (str): Service name.
            services (dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]): Completion services.
            execution_settings_kwargs (dict[str, Any]): Execution settings keyword arguments.
            inputs (list[str]): List of input strings.
            kwargs (dict[str, Any]): Keyword arguments.
        """
        raise NotImplementedError

    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
    ):
        """Test completion service (Streaming).

        Args:
            kernel (Kernel): Kernel instance.
            service_id (str): Service name.
            services (dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]): Completion services.
            execution_settings_kwargs (dict[str, Any]): Execution settings keyword arguments.
            inputs (list[str]): List of input strings.
            kwargs (dict[str, Any]): Keyword arguments.
        """
        raise NotImplementedError

    def evaluate(self, test_target: Any, **kwargs):
        """Evaluate the response.

        Args:
            test_target (Any): Test target.
            kwargs (dict[str, Any]): Keyword arguments.
        """
        raise NotImplementedError
