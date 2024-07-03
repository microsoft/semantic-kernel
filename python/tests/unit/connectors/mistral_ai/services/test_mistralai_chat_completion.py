# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock

import pytest
from mistralai.async_client import MistralAsyncClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
async def test_complete_chat_contents(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    chat_completion_response = AsyncMock()
    choices = [
        MagicMock(finish_reason="stop", message=MagicMock(role="assistant", content="Test"))
    ]
    chat_completion_response.choices = choices
    client.chat.return_value = chat_completion_response
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    content: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    )
    assert content is not None


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.ai_model_id = None
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    chat_completion_response = MagicMock()
    choices = [
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test")),
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test", tool_calls=None))
        ]
    chat_completion_response.choices = choices
    chat_completion_response_empty = MagicMock()
    chat_completion_response_empty.choices = []
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [chat_completion_response_empty, chat_completion_response]
    client.chat_stream.return_value = generator_mock

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


@pytest.mark.asyncio
async def test_mistral_ai_sdk_exception(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.ai_model_id = None
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    client.chat.side_effect = Exception("Test Exception")
    client.chat_stream.side_effect = Exception("Test Exception")

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        )


@pytest.mark.asyncio
async def test_mistral_ai_sdk_exception_streaming(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    client.chat_stream.side_effect = Exception("Test Exception")

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None
        

def test_mistral_ai_chat_completion_init(mistralai_unit_test_env) -> None:
    # Test successful initialization
    mistral_ai_chat_completion = MistralAIChatCompletion()

    assert mistral_ai_chat_completion.ai_model_id == mistralai_unit_test_env["MISTRALAI_CHAT_MODEL_ID"]
    assert isinstance(mistral_ai_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY"]], indirect=True)
def test_mistral_ai_chat_completion_init_with_empty_api_key(mistralai_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        MistralAIChatCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_CHAT_MODEL_ID"]], indirect=True)
def test_mistral_ai_chat_completion_init_with_empty_model_id(mistralai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        MistralAIChatCompletion(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(mistralai_unit_test_env):
    mistral_ai_chat_completion = MistralAIChatCompletion()
    prompt_execution_settings = mistral_ai_chat_completion.get_prompt_execution_settings_class()
    assert prompt_execution_settings == MistralAIChatPromptExecutionSettings
