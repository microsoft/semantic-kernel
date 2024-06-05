# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletionBase
from semantic_kernel.contents import AuthorRole, ChatMessageContent, StreamingChatMessageContent, TextContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.exceptions import FunctionCallInvalidArgumentsException
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel


async def mock_async_process_chat_stream_response(arg1, response, tool_call_behavior, chat_history, kernel, arguments):
    mock_content = MagicMock(spec=StreamingChatMessageContent)
    yield [mock_content], None


@pytest.mark.asyncio
async def test_complete_chat_stream(kernel: Kernel):
    chat_history = MagicMock()
    settings = MagicMock()
    settings.number_of_responses = 1
    mock_response = MagicMock()
    arguments = KernelArguments()

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._prepare_settings",
        return_value=settings,
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_stream_request",
        return_value=mock_response,
    ) as mock_send_chat_stream_request:
        chat_completion_base = OpenAIChatCompletionBase(
            ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
        )

        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None

        prepare_settings_mock.assert_called_with(settings, chat_history, stream_request=True, kernel=kernel)
        mock_send_chat_stream_request.assert_called_with(settings)


@pytest.mark.parametrize("tool_call", [False, True])
@pytest.mark.asyncio
async def test_complete_chat(tool_call, kernel: Kernel):
    chat_history = MagicMock(spec=ChatHistory)
    chat_history.messages = []
    settings = MagicMock(spec=OpenAIChatPromptExecutionSettings)
    settings.number_of_responses = 1
    settings.function_call_behavior = None
    mock_function_call = MagicMock(spec=FunctionCallContent)
    mock_text = MagicMock(spec=TextContent)
    mock_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_function_call] if tool_call else [mock_text]
    )
    mock_message_content = [mock_message]
    arguments = KernelArguments()

    if tool_call:
        settings.function_call_behavior = MagicMock(spec=FunctionCallBehavior)
        settings.function_call_behavior.auto_invoke_kernel_functions = True
        settings.function_call_behavior.max_auto_invoke_attempts = 5
        chat_history.messages = [mock_message]

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._prepare_settings",
    ) as prepare_settings_mock, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_request",
        return_value=mock_message_content,
    ) as mock_send_chat_request, patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._process_function_call",
    ) as mock_process_function_call:
        chat_completion_base = OpenAIChatCompletionBase(
            ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
        )

        result = await chat_completion_base.get_chat_message_contents(
            chat_history, settings, kernel=kernel, arguments=arguments
        )
        assert result is not None

        prepare_settings_mock.assert_called_with(settings, chat_history, stream_request=False, kernel=kernel)
        mock_send_chat_request.assert_called_with(settings)
        if tool_call:
            mock_process_function_call.assert_called()


@pytest.mark.asyncio
async def test_process_tool_calls():
    tool_call_mock = MagicMock(spec=FunctionCallContent)
    tool_call_mock.split_name_dict.return_value = {"arg_name": "arg_value"}
    tool_call_mock.to_kernel_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.name = "test_function"
    tool_call_mock.arguments = {"arg_name": "arg_value"}
    tool_call_mock.ai_model_id = None
    tool_call_mock.metadata = {}
    tool_call_mock.index = 0
    tool_call_mock.parse_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.id = "test_id"
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="test_function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "test_function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)
    kernel_mock = MagicMock(spec=Kernel)
    kernel_mock.auto_function_invocation_filters = []
    kernel_mock.get_function.return_value = func_mock

    async def construct_call_stack(ctx):
        return ctx

    kernel_mock.construct_call_stack.return_value = construct_call_stack
    arguments = KernelArguments()

    chat_completion_base = OpenAIChatCompletionBase(
        ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
    )

    with patch("semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.logger", autospec=True):
        await chat_completion_base._process_function_call(
            tool_call_mock,
            chat_history_mock,
            kernel_mock,
            arguments,
            1,
            0,
            FunctionCallBehavior.AutoInvokeKernelFunctions(),
        )

    chat_history_mock.add_message.assert_called_once()


@pytest.mark.asyncio
async def test_process_tool_calls_with_continuation_on_malformed_arguments():
    tool_call_mock = MagicMock(spec=FunctionCallContent)
    tool_call_mock.parse_arguments.side_effect = FunctionCallInvalidArgumentsException("Malformed arguments")
    tool_call_mock.name = "test_function"
    tool_call_mock.arguments = {"arg_name": "arg_value"}
    tool_call_mock.ai_model_id = None
    tool_call_mock.metadata = {}
    tool_call_mock.index = 0
    tool_call_mock.parse_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.id = "test_id"
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = MagicMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="test_function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "test_function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = AsyncMock(return_value=func_result)
    kernel_mock = MagicMock(spec=Kernel)
    kernel_mock.auto_function_invocation_filters = []
    kernel_mock.get_function.return_value = func_mock
    arguments = KernelArguments()

    chat_completion_base = OpenAIChatCompletionBase(
        ai_model_id="test_model_id", service_id="test", client=MagicMock(spec=AsyncOpenAI)
    )

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.logger", autospec=True
    ) as logger_mock:
        await chat_completion_base._process_function_call(
            tool_call_mock,
            chat_history_mock,
            kernel_mock,
            arguments,
            1,
            0,
            FunctionCallBehavior.AutoInvokeKernelFunctions(),
        )

    logger_mock.exception.assert_any_call(
        "Received invalid arguments for function test_function: Malformed arguments. Trying tool call again."
    )

    add_message_calls = chat_history_mock.add_message.call_args_list
    assert any(
        call[1]["message"].items[0].result == "The tool call arguments are malformed. Arguments must be in JSON format. Please try again."  # noqa: E501
        and call[1]["message"].items[0].id == "test_id"
        and call[1]["message"].items[0].name == "test_function"
        for call in add_message_calls
    ), "Expected call to add_message not found with the expected message content and metadata."
