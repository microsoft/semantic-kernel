# Copyright (c) Microsoft. All rights reserved.

from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import (
    OpenAIChatMessageContent,
)
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_streaming_chat_message_content import (
    OpenAIStreamingChatMessageContent,
)
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletionBase,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.kernel import Kernel


async def mock_async_process_chat_stream_response(arg1, response, tool_call_behavior, chat_history, kernel):
    mock_content = MagicMock(spec=OpenAIStreamingChatMessageContent)
    yield [mock_content]


@pytest.mark.asyncio
async def test_complete_chat_stream():
    chat_history = MagicMock()
    settings = MagicMock()
    mock_response = MagicMock()

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._get_auto_invoke_execution_settings",
        return_value=(True, 3),
    ) as settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._validate_kernel_for_tool_calling",
        return_value=MagicMock(),
    ) as validate_kernel_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._prepare_settings",
        return_value=settings,
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_stream_request",
        return_value=mock_response,
    ) as mock_send_chat_stream_request, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._process_chat_stream_response",
        new_callable=lambda: mock_async_process_chat_stream_response,
    ):
        kernel = Kernel()

        chat_completion_base = OpenAIChatCompletionBase(
            ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
        )

        async for content in chat_completion_base.complete_chat_stream(chat_history, settings, kernel=kernel):
            assert content is not None

        settings_mock.assert_called_once_with(settings)
        validate_kernel_mock.assert_called_once_with(kernel=kernel)
        prepare_settings_mock.assert_called_with(settings, chat_history, stream_request=True)
        mock_send_chat_stream_request.assert_called_with(settings)


@pytest.mark.parametrize("tool_call", [False, True])
@pytest.mark.asyncio
async def test_complete_chat(tool_call):
    chat_history = MagicMock()
    settings = MagicMock()
    mock_message_content = MagicMock(spec=List[OpenAIChatMessageContent])

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._get_auto_invoke_execution_settings",
        return_value=(True, 3),
    ) as settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._validate_kernel_for_tool_calling",
        return_value=MagicMock(),
    ) as validate_kernel_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._prepare_settings",
        return_value=settings,
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_request",
        return_value=mock_message_content,
    ) as mock_send_chat_request, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._should_return_completions_response",
        return_value=not tool_call,
    ), patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._process_chat_response_with_tool_call",
    ) as mock_process_chat_response_with_tool_call:
        kernel = Kernel()

        chat_completion_base = OpenAIChatCompletionBase(
            ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
        )

        result = await chat_completion_base.complete_chat(chat_history, settings, kernel=kernel)

        if tool_call:
            assert result is None
        else:
            assert result is not None

        settings_mock.assert_called_once_with(settings)
        validate_kernel_mock.assert_called_once_with(kernel=kernel)
        prepare_settings_mock.assert_called_with(settings, chat_history, stream_request=False)
        mock_send_chat_request.assert_called_with(settings)
        if tool_call:
            mock_process_chat_response_with_tool_call.assert_called()


def test_build_streaming_message_with_tool_call():
    chat_completion_base = OpenAIChatCompletionBase(
        ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
    )

    stream_chunks = {1: [MagicMock(spec=OpenAIStreamingChatMessageContent)]}
    update_storage = {"tool_call_ids_by_index": {1: MagicMock(spec=ToolCall)}}

    result = chat_completion_base._build_streaming_message_with_tool_call(stream_chunks, update_storage)

    assert result is not None


@pytest.mark.asyncio
async def test_process_tool_calls():
    tool_call_mock = MagicMock()
    tool_call_mock.function.split_name_dict.return_value = {"arg_name": "arg_value"}
    tool_call_mock.function.to_kernel_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.function.name = "test_function"
    tool_call_mock.id = "test_id"

    result_mock = MagicMock(spec=OpenAIChatMessageContent)
    result_mock.tool_calls = [tool_call_mock]

    chat_history_mock = MagicMock(spec=ChatHistory)

    kernel_mock = MagicMock(spec=Kernel)
    kernel_mock.invoke = AsyncMock(return_value=MagicMock(value="Function result"))

    chat_completion_base = OpenAIChatCompletionBase(
        ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
    )

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.logger", autospec=True
    ) as logger_mock:
        await chat_completion_base._process_tool_calls(result_mock, kernel_mock, chat_history_mock)

    logger_mock.info.assert_any_call(f"processing {len(result_mock.tool_calls)} tool calls")
    logger_mock.info.assert_any_call(
        f"Calling {tool_call_mock.function.name} function with args: {tool_call_mock.function.to_kernel_arguments()}"
    )

    kernel_mock.invoke.assert_called_once_with(
        kernel_mock.func(**tool_call_mock.function.split_name_dict()), {"arg_name": "arg_value"}
    )

    chat_history_mock.add_tool_message.assert_called_once_with(
        "Function result",
        metadata={"tool_call_id": tool_call_mock.id, "function_name": tool_call_mock.function.name},
    )


@pytest.mark.parametrize(
    "completions,auto_invoke_kernel_functions,expected_result",
    [
        # Case 1: Empty completions, auto_invoke_kernel_functions=False
        ([], False, True),
        # Case 2: Completions with OpenAIChatMessageContent, auto_invoke_kernel_functions=True
        ([MagicMock(spec=OpenAIChatMessageContent)], True, True),
        # Case 3: Completions with OpenAIChatMessageContent, no tool_calls, auto_invoke_kernel_functions=True
        ([MagicMock(spec=OpenAIChatMessageContent, tool_calls=[])], True, True),
        # Case 4: Completions with OpenAIStreamingChatMessageContent, auto_invoke_kernel_functions=True
        ([MagicMock(spec=OpenAIStreamingChatMessageContent)], True, True),
        # Case 5: Completions with OpenAIStreamingChatMessageContent, auto_invoke_kernel_functions=False
        ([MagicMock(spec=OpenAIStreamingChatMessageContent)], False, True),
        # Case 6: Completions with both types, auto_invoke_kernel_functions=True
        ([MagicMock(spec=OpenAIChatMessageContent), MagicMock(spec=OpenAIStreamingChatMessageContent)], True, True),
        # Case 7: Completions with OpenAIChatMessageContent with tool_calls, auto_invoke_kernel_functions=True
        ([MagicMock(spec=OpenAIChatMessageContent, tool_calls=[{}])], True, False),
    ],
)
@pytest.mark.asyncio
async def test_should_return_completions_response(completions, auto_invoke_kernel_functions, expected_result):
    chat_completion_base = OpenAIChatCompletionBase(
        ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
    )
    result = chat_completion_base._should_return_completions_response(completions, auto_invoke_kernel_functions)
    assert result == expected_result
