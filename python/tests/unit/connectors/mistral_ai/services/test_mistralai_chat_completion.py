# Copyright (c) Microsoft. All rights reserved.

# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest
from mistralai.async_client import MistralAsyncClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    arguments = KernelArguments()

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=MagicMock(spec=MistralAsyncClient)
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


@pytest.mark.asyncio
async def test_complete_chat_contents(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    arguments = KernelArguments()

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=MagicMock(spec=MistralAsyncClient)
    )

    content = await chat_completion_base.get_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    )
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
