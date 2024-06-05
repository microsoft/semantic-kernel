# Copyright (c) Microsoft. All rights reserved.

from functools import partial

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory, ChatMessageContent, TextContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from tests.integration.completions.test_utils import retry


@pytest.mark.parametrize(
    "service, execution_settings, inputs",
    [
        (
            OpenAIChatCompletion(service_id="openai"),
            OpenAIChatPromptExecutionSettings(service_id="openai"),
            [
                ChatMessageContent(role="user", items=[TextContent(text="Hello")]),
                ChatMessageContent(role="user", items=[TextContent(text="How are you today?")]),
            ],
        ),
        (
            AzureChatCompletion(service_id="azure"),
            AzureChatPromptExecutionSettings(service_id="azure"),
            [
                ChatMessageContent(role="user", items=[TextContent(text="Hello")]),
                ChatMessageContent(role="user", items=[TextContent(text="How are you today?")]),
            ],
        ),
    ],
    ids=["openai_text_input", "azure_text_input"],
)
@pytest.mark.asyncio
async def test_chat_completion(
    kernel: Kernel,
    service: ChatCompletionClientBase,
    execution_settings: PromptExecutionSettings,
    inputs: list[ChatMessageContent],
):
    kernel.add_service(service)
    history = ChatHistory()
    kernel.add_function(function_name="chat", plugin_name="chat", prompt="{{$chat_history}}")
    for message in inputs:
        history.add_message(message)
        arguments = KernelArguments(settings=execution_settings, chat_history=history)
        response = await retry(
            partial(kernel.invoke, function_name="chat", plugin_name="chat", arguments=arguments), retries=5
        )
        assert response is not None
