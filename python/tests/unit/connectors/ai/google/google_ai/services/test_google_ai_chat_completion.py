# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from google.genai import Client
from google.genai.models import AsyncModels
from google.genai.types import (
    Candidate,
    Content,
    FinishReason as GoogleFinishReason,
    GenerateContentConfigDict,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
    Part,
)

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


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_CLOUD_REGION"]], indirect=True)
def test_google_ai_chat_completion_init_with_use_vertexai_missing_region(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with use_vertexai true but missing region"""
    with pytest.raises(ServiceInitializationError, match="Region must be provided when use_vertexai is True."):
        GoogleAIChatCompletion(use_vertexai=True, env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_API_KEY"]], indirect=True)
def test_google_ai_chat_completion_init_with_use_vertexai_no_api_key(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion succeeds with use_vertexai=True and no api_key"""
    chat_completion = GoogleAIChatCompletion(use_vertexai=True)
    assert chat_completion.service_settings.use_vertexai is True


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


def test_google_ai_chat_completion_filters_thought_text_parts(google_ai_unit_test_env) -> None:
    google_ai_chat_completion = GoogleAIChatCompletion()

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="model", parts=[])
    candidate.finish_reason = GoogleFinishReason.STOP

    thinking_part = Part.from_text(text="internal reasoning")
    thinking_part.thought = True  # type: ignore[attr-defined]
    answer_part = Part.from_text(text="final answer")

    candidate.content.parts.extend([thinking_part, answer_part])

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    message = google_ai_chat_completion._create_chat_message_content(response, candidate)

    assert message.content == "final answer"
    assert len(message.items) == 1


def test_google_ai_streaming_chat_completion_filters_thought_text_parts(google_ai_unit_test_env) -> None:
    google_ai_chat_completion = GoogleAIChatCompletion()

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="model", parts=[])
    candidate.finish_reason = GoogleFinishReason.STOP

    thinking_part = Part.from_text(text="internal reasoning")
    thinking_part.thought = True  # type: ignore[attr-defined]
    answer_part = Part.from_text(text="streamed answer")
    candidate.content.parts.extend([thinking_part, answer_part])

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    message = google_ai_chat_completion._create_streaming_chat_message_content(response, candidate)

    assert message.content == "streamed answer"
    assert len(message.items) == 1


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


# region deserialization (Part → FunctionCallContent round-trip)


def test_create_chat_message_content_with_thought_signature(google_ai_unit_test_env) -> None:
    """Test that thought_signature from a Part is deserialized into FunctionCallContent.metadata."""
    from google.genai.types import (
        Candidate,
        Content,
        GenerateContentResponse,
        GenerateContentResponseUsageMetadata,
        Part,
    )
    from google.genai.types import (
        FinishReason as GFinishReason,
    )

    from semantic_kernel.contents.function_call_content import FunctionCallContent

    thought_sig_value = b"test-thought-sig-bytes"
    part = Part.from_function_call(name="test_function", args={"key": "value"})
    part.thought_signature = thought_sig_value

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[part])
    candidate.finish_reason = GFinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0, cached_content_token_count=0, candidates_token_count=0, total_token_count=0
    )

    completion = GoogleAIChatCompletion()
    result = completion._create_chat_message_content(response, candidate)

    fc_items = [item for item in result.items if isinstance(item, FunctionCallContent)]
    assert len(fc_items) == 1
    assert fc_items[0].metadata is not None
    assert fc_items[0].metadata["thought_signature"] == thought_sig_value


def test_create_chat_message_content_without_thought_signature(google_ai_unit_test_env) -> None:
    """Test that FunctionCallContent works when Part has no thought_signature."""
    from google.genai.types import (
        Candidate,
        Content,
        GenerateContentResponse,
        GenerateContentResponseUsageMetadata,
        Part,
    )
    from google.genai.types import (
        FinishReason as GFinishReason,
    )

    from semantic_kernel.contents.function_call_content import FunctionCallContent

    part = Part.from_function_call(name="test_function", args={"key": "value"})

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[part])
    candidate.finish_reason = GFinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0, cached_content_token_count=0, candidates_token_count=0, total_token_count=0
    )

    completion = GoogleAIChatCompletion()
    result = completion._create_chat_message_content(response, candidate)

    fc_items = [item for item in result.items if isinstance(item, FunctionCallContent)]
    assert len(fc_items) == 1
    assert "thought_signature" not in fc_items[0].metadata


def test_create_streaming_chat_message_content_with_thought_signature(google_ai_unit_test_env) -> None:
    """Test that thought_signature from a Part is deserialized in streaming path."""
    from google.genai.types import (
        Candidate,
        Content,
        GenerateContentResponse,
        GenerateContentResponseUsageMetadata,
        Part,
    )
    from google.genai.types import (
        FinishReason as GFinishReason,
    )

    from semantic_kernel.contents.function_call_content import FunctionCallContent

    thought_sig_value = b"streaming-thought-sig"
    part = Part.from_function_call(name="stream_func", args={"a": "b"})
    part.thought_signature = thought_sig_value

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[part])
    candidate.finish_reason = GFinishReason.STOP

    chunk = GenerateContentResponse()
    chunk.candidates = [candidate]
    chunk.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0, cached_content_token_count=0, candidates_token_count=0, total_token_count=0
    )

    completion = GoogleAIChatCompletion()
    result = completion._create_streaming_chat_message_content(chunk, candidate)

    fc_items = [item for item in result.items if isinstance(item, FunctionCallContent)]
    assert len(fc_items) == 1
    assert fc_items[0].metadata is not None
    assert fc_items[0].metadata["thought_signature"] == thought_sig_value


def test_create_streaming_chat_message_content_without_thought_signature(google_ai_unit_test_env) -> None:
    """Test that streaming FunctionCallContent works when Part lacks thought_signature."""
    from google.genai.types import (
        Candidate,
        Content,
        GenerateContentResponse,
        GenerateContentResponseUsageMetadata,
        Part,
    )
    from google.genai.types import (
        FinishReason as GFinishReason,
    )

    from semantic_kernel.contents.function_call_content import FunctionCallContent

    part = Part.from_function_call(name="stream_func", args={"a": "b"})

    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[part])
    candidate.finish_reason = GFinishReason.STOP

    chunk = GenerateContentResponse()
    chunk.candidates = [candidate]
    chunk.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0, cached_content_token_count=0, candidates_token_count=0, total_token_count=0
    )

    completion = GoogleAIChatCompletion()
    result = completion._create_streaming_chat_message_content(chunk, candidate)

    fc_items = [item for item in result.items if isinstance(item, FunctionCallContent)]
    assert len(fc_items) == 1
    assert "thought_signature" not in fc_items[0].metadata


def test_create_chat_message_content_getattr_guard_on_missing_attribute(google_ai_unit_test_env) -> None:
    """Test that getattr guard handles SDK versions where thought_signature doesn't exist on Part."""
    from unittest.mock import MagicMock

    from google.genai.types import (
        GenerateContentResponse,
        GenerateContentResponseUsageMetadata,
    )

    from semantic_kernel.contents.function_call_content import FunctionCallContent

    # Create a mock Part that lacks 'thought_signature' attribute entirely
    mock_part = MagicMock()
    mock_part.text = None
    mock_part.function_call.name = "test_func"
    mock_part.function_call.args = {"x": "y"}
    del mock_part.thought_signature  # simulate older SDK without the field

    # Use a fully-mocked candidate to avoid Content pydantic validation
    mock_candidate = MagicMock()
    mock_candidate.index = 0
    mock_candidate.content.parts = [mock_part]
    mock_candidate.finish_reason = 1  # STOP

    response = GenerateContentResponse()
    response.candidates = [mock_candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0, cached_content_token_count=0, candidates_token_count=0, total_token_count=0
    )

    completion = GoogleAIChatCompletion()
    result = completion._create_chat_message_content(response, mock_candidate)

    fc_items = [item for item in result.items if isinstance(item, FunctionCallContent)]
    assert len(fc_items) == 1
    assert "thought_signature" not in fc_items[0].metadata


# endregion deserialization
