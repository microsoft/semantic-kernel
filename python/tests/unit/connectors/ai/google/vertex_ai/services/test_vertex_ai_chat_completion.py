# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, patch

import pytest
from google.cloud.aiplatform_v1beta1.types.content import Content
from vertexai.generative_models import GenerativeModel

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_chat_completion import VertexAIChatCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.kernel import Kernel


# region init
def test_vertex_ai_chat_completion_init(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAIChatCompletion"""
    model_id = vertex_ai_unit_test_env["VERTEX_AI_GEMINI_MODEL_ID"]
    project_id = vertex_ai_unit_test_env["VERTEX_AI_PROJECT_ID"]
    vertex_ai_chat_completion = VertexAIChatCompletion()

    assert vertex_ai_chat_completion.ai_model_id == model_id
    assert vertex_ai_chat_completion.service_id == model_id

    assert isinstance(vertex_ai_chat_completion.service_settings, VertexAISettings)
    assert vertex_ai_chat_completion.service_settings.gemini_model_id == model_id
    assert vertex_ai_chat_completion.service_settings.project_id == project_id


def test_vertex_ai_chat_completion_init_with_service_id(vertex_ai_unit_test_env, service_id) -> None:
    """Test initialization of VertexAIChatCompletion with a service id that is not the model id"""
    vertex_ai_chat_completion = VertexAIChatCompletion(service_id=service_id)

    assert vertex_ai_chat_completion.service_id == service_id


def test_vertex_ai_chat_completion_init_with_model_id_in_argument(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAIChatCompletion with model id in argument"""
    vertex_ai_chat_completion = VertexAIChatCompletion(gemini_model_id="custom_model_id")

    assert vertex_ai_chat_completion.ai_model_id == "custom_model_id"
    assert vertex_ai_chat_completion.service_id == "custom_model_id"


@pytest.mark.parametrize("exclude_list", [["VERTEX_AI_GEMINI_MODEL_ID"]], indirect=True)
def test_vertex_ai_chat_completion_init_with_empty_model_id(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAIChatCompletion with an empty model id"""
    with pytest.raises(ServiceInitializationError):
        VertexAIChatCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["VERTEX_AI_PROJECT_ID"]], indirect=True)
def test_vertex_ai_chat_completion_init_with_empty_project_id(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAIChatCompletion with an empty project id"""
    with pytest.raises(ServiceInitializationError):
        VertexAIChatCompletion(env_file_path="fake_env_file_path.env")


def test_prompt_execution_settings_class(vertex_ai_unit_test_env) -> None:
    vertex_ai_chat_completion = VertexAIChatCompletion()
    assert vertex_ai_chat_completion.get_prompt_execution_settings_class() == VertexAIChatPromptExecutionSettings


# endregion init


# region chat completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_chat_completion(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    chat_history: ChatHistory,
    mock_vertex_ai_chat_completion_response,
) -> None:
    """Test chat completion with VertexAIChatCompletion"""
    settings = VertexAIChatPromptExecutionSettings()

    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_chat_completion_response

    vertex_ai_chat_completion = VertexAIChatCompletion()
    responses: list[ChatMessageContent] = await vertex_ai_chat_completion.get_chat_message_contents(
        chat_history, settings
    )

    mock_vertex_ai_model_generate_content_async.assert_called_once_with(
        contents=vertex_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        generation_config=settings.prepare_settings_dict(),
        tools=None,
        tool_config=None,
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == mock_vertex_ai_chat_completion_response.candidates[0].content.parts[0].text
    assert responses[0].finish_reason == FinishReason.STOP
    assert "usage" in responses[0].metadata
    assert "prompt_feedback" in responses[0].metadata
    assert responses[0].inner_content == mock_vertex_ai_chat_completion_response


async def test_vertex_ai_chat_completion_with_function_choice_behavior_fail_verification(
    chat_history: ChatHistory,
    vertex_ai_unit_test_env,
) -> None:
    """Test completion of VertexAIChatCompletion with function choice behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = VertexAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

        vertex_ai_chat_completion = VertexAIChatCompletion()

        await vertex_ai_chat_completion.get_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
        )


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_chat_completion_with_function_choice_behavior(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_vertex_ai_chat_completion_response_with_tool_call,
) -> None:
    """Test completion of VertexAIChatCompletion with function choice behavior"""
    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_chat_completion_response_with_tool_call

    settings = VertexAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    vertex_ai_chat_completion = VertexAIChatCompletion()

    responses = await vertex_ai_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    )

    # The function should be called twice:
    # One for the tool call and one for the last completion
    # after the maximum_auto_invoke_attempts is reached
    assert mock_vertex_ai_model_generate_content_async.call_count == 2
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    # Google doesn't return STOP as the finish reason for tool calls
    assert responses[0].finish_reason == FinishReason.STOP


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_vertex_ai_chat_completion_response,
) -> None:
    """Test completion of VertexAIChatCompletion with function choice behavior but no tool call returned"""
    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_chat_completion_response

    settings = VertexAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    vertex_ai_chat_completion = VertexAIChatCompletion()

    responses = await vertex_ai_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    )

    mock_vertex_ai_model_generate_content_async.assert_awaited_once_with(
        contents=vertex_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        generation_config=settings.prepare_settings_dict(),
        tools=None,
        tool_config=None,
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == mock_vertex_ai_chat_completion_response.candidates[0].content.parts[0].text


# endregion chat completion


# region streaming chat completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_streaming_chat_completion(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    chat_history: ChatHistory,
    mock_vertex_ai_streaming_chat_completion_response,
) -> None:
    """Test chat completion with VertexAIChatCompletion"""
    settings = VertexAIChatPromptExecutionSettings()

    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_streaming_chat_completion_response

    vertex_ai_chat_completion = VertexAIChatCompletion()
    async for messages in vertex_ai_chat_completion.get_streaming_chat_message_contents(chat_history, settings):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].finish_reason == FinishReason.STOP
        assert "usage" in messages[0].metadata
        assert "prompt_feedback" in messages[0].metadata

    mock_vertex_ai_model_generate_content_async.assert_called_once_with(
        contents=vertex_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        generation_config=settings.prepare_settings_dict(),
        tools=None,
        tool_config=None,
        stream=True,
    )


async def test_vertex_ai_streaming_chat_completion_with_function_choice_behavior_fail_verification(
    chat_history: ChatHistory,
    vertex_ai_unit_test_env,
) -> None:
    """Test streaming chat completion of VertexAIChatCompletion with function choice
    behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = VertexAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

        vertex_ai_chat_completion = VertexAIChatCompletion()

        async for _ in vertex_ai_chat_completion.get_streaming_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
        ):
            pass


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_streaming_chat_completion_with_function_choice_behavior(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    kernel: Kernel,
    chat_history: ChatHistory,
    mock_vertex_ai_streaming_chat_completion_response_with_tool_call,
    decorated_native_function,
) -> None:
    """Test streaming chat completion of VertexAIChatCompletion with function choice behavior"""
    mock_vertex_ai_model_generate_content_async.return_value = (
        mock_vertex_ai_streaming_chat_completion_response_with_tool_call
    )

    settings = VertexAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    vertex_ai_chat_completion = VertexAIChatCompletion()

    kernel.add_function(plugin_name="TestPlugin", function=decorated_native_function)

    all_messages = []
    async for messages in vertex_ai_chat_completion.get_streaming_chat_message_contents(
        chat_history,
        settings,
        kernel=kernel,
    ):
        all_messages.extend(messages)

    assert len(all_messages) == 2, f"Expected 2 messages, got {len(all_messages)}"

    # Validate the first message
    assert all_messages[0].role == "assistant", f"Unexpected role for first message: {all_messages[0].role}"
    assert all_messages[0].content == "", f"Unexpected content for first message: {all_messages[0].content}"
    assert all_messages[0].finish_reason == FinishReason.STOP, (
        f"Unexpected finish reason for first message: {all_messages[0].finish_reason}"
    )

    # Validate the second message
    assert all_messages[1].role == "tool", f"Unexpected role for second message: {all_messages[1].role}"
    assert all_messages[1].content == "", f"Unexpected content for second message: {all_messages[1].content}"
    assert all_messages[1].finish_reason is None


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_streaming_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_vertex_ai_streaming_chat_completion_response,
) -> None:
    """Test completion of VertexAIChatCompletion with function choice behavior but no tool call returned"""
    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_streaming_chat_completion_response

    settings = VertexAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    vertex_ai_chat_completion = VertexAIChatCompletion()

    async for messages in vertex_ai_chat_completion.get_streaming_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    ):
        assert len(messages) == 1
        assert messages[0].role == "assistant"

    mock_vertex_ai_model_generate_content_async.assert_awaited_once_with(
        contents=vertex_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        generation_config=settings.prepare_settings_dict(),
        tools=None,
        tool_config=None,
        stream=True,
    )


# endregion streaming chat completion


def test_vertex_ai_chat_completion_parse_chat_history_correctly(vertex_ai_unit_test_env) -> None:
    """Test _prepare_chat_history_for_request method"""
    vertex_ai_chat_completion = VertexAIChatCompletion()

    chat_history = ChatHistory()
    chat_history.add_system_message("test_system_message")
    chat_history.add_user_message("test_user_message")
    chat_history.add_assistant_message("test_assistant_message")

    parsed_chat_history = vertex_ai_chat_completion._prepare_chat_history_for_request(chat_history)

    assert isinstance(parsed_chat_history, list)
    # System message should be ignored
    assert len(parsed_chat_history) == 2
    assert all(isinstance(message, Content) for message in parsed_chat_history)
    assert parsed_chat_history[0].role == "user"
    assert parsed_chat_history[0].parts[0].text == "test_user_message"
    assert parsed_chat_history[1].role == "model"
    assert parsed_chat_history[1].parts[0].text == "test_assistant_message"
