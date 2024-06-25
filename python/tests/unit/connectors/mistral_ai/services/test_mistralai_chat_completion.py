# Copyright (c) Microsoft. All rights reserved.

# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai.async_client import MistralAsyncClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import MistralAIChatPromptExecutionSettings
from semantic_kernel.exceptions import ServiceInitializationError

from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

from semantic_kernel.contents import AuthorRole, ChatMessageContent, TextContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel



@pytest.mark.asyncio
async def test_complete_chat_stream(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    mock_response = MagicMock()
    arguments = KernelArguments()

    with patch(
        "semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion.MistralAIChatCompletion._prepare_settings",
        return_value=settings,
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion.MistralAIChatCompletion._send_chat_stream_request",
        return_value=mock_response,
    ) as mock_send_chat_stream_request:
        chat_completion_base = MistralAIChatCompletion(
            ai_model_id="test_model_id", service_id="test", api_key="", async_client=MagicMock(spec=MistralAsyncClient)
        )

        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None

        prepare_settings_mock.assert_called_with(settings, chat_history, stream_request=True, kernel=kernel)
        mock_send_chat_stream_request.assert_called_with(settings)


@pytest.mark.parametrize("tool_call", [False])
@pytest.mark.asyncio
async def test_complete_chat(tool_call, kernel: Kernel):
    chat_history = MagicMock(spec=ChatHistory)
    chat_history.messages = []
    settings = MagicMock(spec=MistralAIChatPromptExecutionSettings)
    settings.function_call_behavior = None
    mock_text = MagicMock(spec=TextContent)
    mock_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_text]
    )
    mock_message_content = [mock_message]
    arguments = KernelArguments()

    with patch(
        "semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion.MistralAIChatCompletion._prepare_settings",
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion.MistralAIChatCompletion._send_chat_request",
        return_value=mock_message_content,
    ) as mock_send_chat_request:
        chat_completion_base = MistralAIChatCompletion(
            ai_model_id="test_model_id", service_id="test",api_key="", async_client=MagicMock(spec=MistralAsyncClient)
        )

        result = await chat_completion_base.get_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        )
        assert result is not None

        prepare_settings_mock.assert_called_with(settings, chat_history, kernel=kernel)
        mock_send_chat_request.assert_called_with(settings)

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
