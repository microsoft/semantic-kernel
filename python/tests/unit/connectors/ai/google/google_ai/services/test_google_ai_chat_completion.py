# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from google.genai import Client
from google.genai.models import AsyncModels
from google.genai.types import Content, GenerateContentConfigDict

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.connectors.ai.google.shared_utils import filter_system_message
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.kernel import Kernel


# region init
def test_google_ai_chat_completion_init(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion"""
    model_id = google_ai_unit_test_env["GOOGLE_AI_GEMINI_MODEL_ID"]
    api_key = google_ai_unit_test_env["GOOGLE_AI_API_KEY"]
    google_ai_chat_completion = GoogleAIChatCompletion()

    assert google_ai_chat_completion.ai_model_id == model_id
    assert google_ai_chat_completion.service_id == model_id

    assert isinstance(google_ai_chat_completion.service_settings, GoogleAISettings)
    assert google_ai_chat_completion.service_settings.gemini_model_id == model_id
    assert google_ai_chat_completion.service_settings.api_key.get_secret_value() == api_key


def test_google_ai_chat_completion_init_with_service_id(google_ai_unit_test_env, service_id) -> None:
    """Test initialization of GoogleAIChatCompletion with a service_id that is not the model_id"""
    google_ai_chat_completion = GoogleAIChatCompletion(service_id=service_id)

    assert google_ai_chat_completion.service_id == service_id


def test_google_ai_chat_completion_init_with_model_id_in_argument(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with model_id in argument"""
    google_ai_chat_completion = GoogleAIChatCompletion(gemini_model_id="custom_model_id")

    assert google_ai_chat_completion.ai_model_id == "custom_model_id"
    assert google_ai_chat_completion.service_id == "custom_model_id"


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_GEMINI_MODEL_ID"]], indirect=True)
def test_google_ai_chat_completion_init_with_empty_model_id(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with an empty model_id"""
    with pytest.raises(ServiceInitializationError, match="The Google AI Gemini model ID is required."):
        GoogleAIChatCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_API_KEY"]], indirect=True)
def test_google_ai_chat_completion_init_with_empty_api_key(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with an empty api_key"""
    with pytest.raises(ServiceInitializationError, match="API key is required when use_vertexai is False."):
        GoogleAIChatCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_CLOUD_PROJECT_ID"]], indirect=True)
def test_google_ai_chat_completion_init_with_use_vertexai_missing_project_id(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with use_vertexai true but missing project_id"""
    with pytest.raises(ServiceInitializationError, match="Project ID must be provided when use_vertexai is True."):
        GoogleAIChatCompletion(use_vertexai=True, env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_API_KEY"]], indirect=True)
def test_google_ai_chat_completion_init_with_vertexai_without_api_key(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with use_vertexai true and no API key"""
    # This should succeed because API key is not required when using Vertex AI
    google_ai_chat_completion = GoogleAIChatCompletion(
        use_vertexai=True,
        project_id=google_ai_unit_test_env["GOOGLE_AI_CLOUD_PROJECT_ID"],
        env_file_path="fake_env_file_path.env",
    )

    assert google_ai_chat_completion.ai_model_id == google_ai_unit_test_env["GOOGLE_AI_GEMINI_MODEL_ID"]
    assert google_ai_chat_completion.service_settings.use_vertexai is True
    assert google_ai_chat_completion.service_settings.cloud_project_id == google_ai_unit_test_env["GOOGLE_AI_CLOUD_PROJECT_ID"]


def test_prompt_execution_settings_class(google_ai_unit_test_env) -> None:
    google_ai_chat_completion = GoogleAIChatCompletion()
    assert google_ai_chat_completion.get_prompt_execution_settings_class() == GoogleAIChatPromptExecutionSettings


# endregion init


# region chat completion


@patch.object(AsyncModels, "generate_content", new_callable=AsyncMock)
async def test_google_ai_chat_completion(
    mock_google_ai_model_generate_content,
    google_ai_unit_test_env,
    chat_history: ChatHistory,
    mock_google_ai_chat_completion_response,
) -> None:
    """Test chat completion with GoogleAIChatCompletion"""
    settings = GoogleAIChatPromptExecutionSettings(top_k=5, temperature=0.7)

    mock_google_ai_model_generate_content.return_value = mock_google_ai_chat_completion_response

    google_ai_chat_completion = GoogleAIChatCompletion()
    responses: list[ChatMessageContent] = await google_ai_chat_completion.get_chat_message_contents(
        chat_history, settings
    )

    mock_google_ai_model_generate_content.assert_called_once_with(
        model=google_ai_chat_completion.service_settings.gemini_model_id,
        contents=google_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        config=GenerateContentConfigDict(
            **settings.prepare_settings_dict(),
            system_instruction=filter_system_message(chat_history),
        ),
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == mock_google_ai_chat_completion_response.candidates[0].content.parts[0].text
    assert responses[0].finish_reason == FinishReason.STOP
    assert "usage" in responses[0].metadata
    assert "prompt_feedback" in responses[0].metadata
    assert responses[0].inner_content == mock_google_ai_chat_completion_response


async def test_google_ai_chat_completion_with_custom_client(
    chat_history: ChatHistory,
    google_ai_unit_test_env,
    mock_google_ai_chat_completion_response,
) -> None:
    """Test chat completion with GoogleAIChatCompletion using a custom client"""
    # Create a custom client with a fake API key for testing
    custom_client = Client(api_key="fake-api-key-for-testing")

    # Mock the custom client's generate_content method
    mock_generate_content = AsyncMock(return_value=mock_google_ai_chat_completion_response)
    custom_client.aio.models.generate_content = mock_generate_content

    google_ai_chat_completion = GoogleAIChatCompletion(client=custom_client)
    responses: list[ChatMessageContent] = await google_ai_chat_completion.get_chat_message_contents(
        chat_history,
        GoogleAIChatPromptExecutionSettings(),
    )

    custom_client.close()

    # Verify that the custom client was used and returned the expected response
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == mock_google_ai_chat_completion_response.candidates[0].content.parts[0].text
    assert responses[0].finish_reason == FinishReason.STOP

    # Verify that the custom client's method was called
    mock_generate_content.assert_called_once()


async def test_google_ai_chat_completion_with_function_choice_behavior_fail_verification(
    chat_history: ChatHistory,
    google_ai_unit_test_env,
) -> None:
    """Test completion of GoogleAIChatCompletion with function choice behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = GoogleAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

        google_ai_chat_completion = GoogleAIChatCompletion()

        await google_ai_chat_completion.get_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
        )


@patch.object(AsyncModels, "generate_content", new_callable=AsyncMock)
async def test_google_ai_chat_completion_with_function_choice_behavior(
    mock_google_ai_model_generate_content,
    google_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_google_ai_chat_completion_response_with_tool_call,
) -> None:
    """Test completion of GoogleAIChatCompletion with function choice behavior"""
    mock_google_ai_model_generate_content.return_value = mock_google_ai_chat_completion_response_with_tool_call

    settings = GoogleAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    google_ai_chat_completion = GoogleAIChatCompletion()

    responses = await google_ai_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    )

    # The function should be called twice:
    # One for the tool call and one for the last completion
    # after the maximum_auto_invoke_attempts is reached
    assert mock_google_ai_model_generate_content.call_count == 2
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    # Google doesn't return STOP as the finish reason for tool calls
    assert responses[0].finish_reason == FinishReason.STOP


@patch.object(AsyncModels, "generate_content", new_callable=AsyncMock)
async def test_google_ai_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_google_ai_model_generate_content,
    google_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_google_ai_chat_completion_response,
) -> None:
    """Test completion of GoogleAIChatCompletion with function choice behavior but no tool call returned"""
    mock_google_ai_model_generate_content.return_value = mock_google_ai_chat_completion_response

    settings = GoogleAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    google_ai_chat_completion = GoogleAIChatCompletion()

    responses = await google_ai_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    )

    mock_google_ai_model_generate_content.assert_awaited_once_with(
        model=google_ai_chat_completion.service_settings.gemini_model_id,
        contents=google_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        config=GenerateContentConfigDict(
            **settings.prepare_settings_dict(),
            system_instruction=filter_system_message(chat_history),
        ),
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == mock_google_ai_chat_completion_response.candidates[0].content.parts[0].text


# endregion chat completion


# region streaming chat completion


@patch.object(AsyncModels, "generate_content_stream", new_callable=AsyncMock)
async def test_google_ai_streaming_chat_completion(
    mock_google_ai_model_generate_content_stream,
    google_ai_unit_test_env,
    chat_history: ChatHistory,
    mock_google_ai_streaming_chat_completion_response,
) -> None:
    """Test streaming chat completion with GoogleAIChatCompletion"""
    settings = GoogleAIChatPromptExecutionSettings()

    mock_google_ai_model_generate_content_stream.return_value = mock_google_ai_streaming_chat_completion_response

    google_ai_chat_completion = GoogleAIChatCompletion()
    async for messages in google_ai_chat_completion.get_streaming_chat_message_contents(chat_history, settings):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].finish_reason == FinishReason.STOP
        assert "usage" in messages[0].metadata
        assert "prompt_feedback" in messages[0].metadata

    mock_google_ai_model_generate_content_stream.assert_called_once_with(
        model=google_ai_chat_completion.service_settings.gemini_model_id,
        contents=google_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        config=GenerateContentConfigDict(
            **settings.prepare_settings_dict(),
            system_instruction=filter_system_message(chat_history),
        ),
    )


async def test_google_ai_streaming_chat_completion_with_custom_client(
    chat_history: ChatHistory,
    google_ai_unit_test_env,
    mock_google_ai_streaming_chat_completion_response,
) -> None:
    """Test streaming chat completion with GoogleAIChatCompletion using a custom client"""
    # Create a custom client with a fake API key for testing
    custom_client = Client(api_key="fake-api-key-for-testing")

    # Mock the custom client's generate_content_stream method
    mock_generate_content_stream = AsyncMock(return_value=mock_google_ai_streaming_chat_completion_response)
    custom_client.aio.models.generate_content_stream = mock_generate_content_stream

    google_ai_chat_completion = GoogleAIChatCompletion(client=custom_client)

    all_messages = []
    async for messages in google_ai_chat_completion.get_streaming_chat_message_contents(
        chat_history, GoogleAIChatPromptExecutionSettings()
    ):
        all_messages.extend(messages)
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].finish_reason == FinishReason.STOP
        assert "usage" in messages[0].metadata
        assert "prompt_feedback" in messages[0].metadata

    custom_client.close()

    # Verify that the custom client was used and returned the expected response
    assert len(all_messages) > 0

    # Verify that the custom client's method was called
    mock_generate_content_stream.assert_called_once()


async def test_google_ai_streaming_chat_completion_with_function_choice_behavior_fail_verification(
    chat_history: ChatHistory,
    google_ai_unit_test_env,
) -> None:
    """Test streaming chat completion of GoogleAIChatCompletion with function choice
    behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = GoogleAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )

        google_ai_chat_completion = GoogleAIChatCompletion()

        async for _ in google_ai_chat_completion.get_streaming_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
        ):
            pass


@patch.object(AsyncModels, "generate_content_stream", new_callable=AsyncMock)
async def test_google_ai_streaming_chat_completion_with_function_choice_behavior(
    mock_google_ai_model_generate_content_stream,
    google_ai_unit_test_env,
    kernel: Kernel,
    chat_history: ChatHistory,
    mock_google_ai_streaming_chat_completion_response_with_tool_call,
    decorated_native_function,
) -> None:
    """Test streaming chat completion of GoogleAIChatCompletion with function choice behavior"""
    mock_google_ai_model_generate_content_stream.return_value = (
        mock_google_ai_streaming_chat_completion_response_with_tool_call
    )

    settings = GoogleAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    google_ai_chat_completion = GoogleAIChatCompletion()

    kernel.add_function(plugin_name="TestPlugin", function=decorated_native_function)

    all_messages = []
    async for messages in google_ai_chat_completion.get_streaming_chat_message_contents(
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


@patch.object(AsyncModels, "generate_content_stream", new_callable=AsyncMock)
async def test_google_ai_streaming_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_google_ai_model_generate_content_stream,
    google_ai_unit_test_env,
    kernel,
    chat_history: ChatHistory,
    mock_google_ai_streaming_chat_completion_response,
) -> None:
    """Test completion of GoogleAIChatCompletion with function choice behavior but no tool call returned"""
    mock_google_ai_model_generate_content_stream.return_value = mock_google_ai_streaming_chat_completion_response

    settings = GoogleAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    google_ai_chat_completion = GoogleAIChatCompletion()

    async for messages in google_ai_chat_completion.get_streaming_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
    ):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Test content"

    mock_google_ai_model_generate_content_stream.assert_awaited_once_with(
        model=google_ai_chat_completion.service_settings.gemini_model_id,
        contents=google_ai_chat_completion._prepare_chat_history_for_request(chat_history),
        config=GenerateContentConfigDict(
            **settings.prepare_settings_dict(),
            system_instruction=filter_system_message(chat_history),
        ),
    )


# endregion streaming chat completion


def test_google_ai_chat_completion_parse_chat_history_correctly(google_ai_unit_test_env) -> None:
    """Test _prepare_chat_history_for_request method"""
    google_ai_chat_completion = GoogleAIChatCompletion()

    chat_history = ChatHistory()
    chat_history.add_system_message("test_system_message")
    chat_history.add_user_message("test_user_message")
    chat_history.add_assistant_message("test_assistant_message")

    parsed_chat_history = google_ai_chat_completion._prepare_chat_history_for_request(chat_history)

    assert isinstance(parsed_chat_history, list)
    # System message should be ignored
    assert len(parsed_chat_history) == 2
    assert all(isinstance(message, Content) for message in parsed_chat_history)
    assert parsed_chat_history[0].role == "user"
    assert parsed_chat_history[0].parts[0].text == "test_user_message"
    assert parsed_chat_history[1].role == "model"
    assert parsed_chat_history[1].parts[0].text == "test_assistant_message"
