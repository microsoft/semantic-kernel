# Copyright (c) Microsoft. All rights reserved.


from functools import reduce
from unittest.mock import Mock, patch

import boto3
import pytest

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_chat_completion import BedrockChatCompletion
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import BedrockModelProvider
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from tests.unit.connectors.ai.bedrock.conftest import MockBedrockClient, MockBedrockRuntimeClient

# region init


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion()

    assert bedrock_chat_completion.ai_model_id == bedrock_unit_test_env["BEDROCK_CHAT_MODEL_ID"]
    assert bedrock_chat_completion.service_id == bedrock_unit_test_env["BEDROCK_CHAT_MODEL_ID"]

    assert bedrock_chat_completion.bedrock_model_provider == BedrockModelProvider(
        bedrock_unit_test_env["BEDROCK_MODEL_PROVIDER"]
    )
    assert bedrock_chat_completion.bedrock_client is not None
    assert bedrock_chat_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init_model_id_override(mock_client, bedrock_unit_test_env, model_id) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(model_id=model_id)

    assert bedrock_chat_completion.ai_model_id == model_id
    assert bedrock_chat_completion.service_id == model_id

    assert bedrock_chat_completion.bedrock_client is not None
    assert bedrock_chat_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init_custom_service_id(mock_client, bedrock_unit_test_env, service_id) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(service_id=service_id)

    assert bedrock_chat_completion.service_id == service_id

    assert bedrock_chat_completion.bedrock_client is not None
    assert bedrock_chat_completion.bedrock_runtime_client is not None


def test_bedrock_chat_completion_init_custom_clients(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(
        runtime_client=MockBedrockRuntimeClient(),
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_chat_completion.bedrock_client, MockBedrockClient)
    assert isinstance(bedrock_chat_completion.bedrock_runtime_client, MockBedrockRuntimeClient)


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init_custom_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_chat_completion.bedrock_client, MockBedrockClient)
    assert bedrock_chat_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init_custom_runtime_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(
        runtime_client=MockBedrockRuntimeClient(),
    )

    assert bedrock_chat_completion.bedrock_client is not None
    assert isinstance(bedrock_chat_completion.bedrock_runtime_client, MockBedrockRuntimeClient)


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_chat_completion_init_custom_bedrock_model_provider(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service"""
    bedrock_chat_completion = BedrockChatCompletion(
        model_provider=BedrockModelProvider.AMAZON,
    )

    assert bedrock_chat_completion.bedrock_model_provider == BedrockModelProvider.AMAZON


@pytest.mark.parametrize("exclude_list", [["BEDROCK_CHAT_MODEL_ID"]], indirect=True)
def test_bedrock_chat_completion_client_init_with_empty_model_id(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service with empty model id"""
    with pytest.raises(ServiceInitializationError, match="The Amazon Bedrock Chat Model ID is missing."):
        BedrockChatCompletion(env_file_path="fake_env_file_path.env")


def test_bedrock_chat_completion_client_init_invalid_settings(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service with invalid settings"""
    with pytest.raises(
        ServiceInitializationError, match="Failed to initialize the Amazon Bedrock Chat Completion Service."
    ):
        BedrockChatCompletion(model_id=123)  # Model ID must be a string


def test_bedrock_chat_completion_client_init_invalid_model_provider(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Chat Completion service with invalid settings"""
    with pytest.raises(
        ServiceInitializationError, match="Failed to initialize the Amazon Bedrock Chat Completion Service."
    ):
        BedrockChatCompletion(model_provider="invalid_provider")


@patch.object(boto3, "client", return_value=Mock())
def test_prompt_execution_settings_class(mock_client, bedrock_unit_test_env) -> None:
    """Test getting prompt execution settings class"""
    bedrock_completion_client = BedrockChatCompletion()
    assert bedrock_completion_client.get_prompt_execution_settings_class() == BedrockChatPromptExecutionSettings


# endregion

# region private methods


@patch.object(boto3, "client", return_value=Mock())
def test_prepare_chat_history_for_request(mock_client, bedrock_unit_test_env, chat_history) -> None:
    """Test preparing chat history for request"""
    bedrock_chat_completion = BedrockChatCompletion()
    parsed_chat_history = bedrock_chat_completion._prepare_chat_history_for_request(chat_history)

    assert isinstance(parsed_chat_history, list)
    assert len(parsed_chat_history) == len(chat_history) - 2  # Exclude system message
    assert all([item["role"] in ["user", "assistant"] for item in parsed_chat_history])


@patch.object(boto3, "client", return_value=Mock())
def test_prepare_chat_history_for_request_merges_parallel_tool_results(mock_client, bedrock_unit_test_env) -> None:
    """Test that parallel tool calls and their results are merged into single Bedrock messages.

    When a model requests multiple tools in one turn, SK emits one assistant message per tool call
    and one tool message per tool result. The Bedrock Converse API requires every toolUse block for a
    turn to be in a single assistant message and every toolResult block to be in a single user message,
    otherwise the request is rejected with an "Expected toolResult blocks ..." error.
    """
    chat_history = ChatHistory()
    chat_history.add_user_message("What is the weather in Seattle and Tokyo?")
    chat_history.add_message(
        ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[FunctionCallContent(id="call_1", name="get_weather", arguments={"city": "Seattle"})],
        )
    )
    chat_history.add_message(
        ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[FunctionCallContent(id="call_2", name="get_weather", arguments={"city": "Tokyo"})],
        )
    )
    chat_history.add_message(
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="call_1", result="Sunny")],
        )
    )
    chat_history.add_message(
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="call_2", result="Rainy")],
        )
    )

    bedrock_chat_completion = BedrockChatCompletion()
    parsed_chat_history = bedrock_chat_completion._prepare_chat_history_for_request(chat_history)

    # user message + merged assistant message (2 toolUse) + merged user message (2 toolResult)
    assert len(parsed_chat_history) == 3

    assistant_message = parsed_chat_history[1]
    assert assistant_message["role"] == "assistant"
    tool_use_ids = [block["toolUse"]["toolUseId"] for block in assistant_message["content"] if "toolUse" in block]
    assert tool_use_ids == ["call_1", "call_2"]

    tool_result_message = parsed_chat_history[2]
    assert tool_result_message["role"] == "user"
    tool_result_ids = [
        block["toolResult"]["toolUseId"] for block in tool_result_message["content"] if "toolResult" in block
    ]
    assert tool_result_ids == ["call_1", "call_2"]


@patch.object(boto3, "client", return_value=Mock())
def test_prepare_chat_history_for_request_merges_consecutive_same_role_messages(
    mock_client, bedrock_unit_test_env
) -> None:
    """Test that consecutive same-role messages are merged even without tool content.

    The merge applies to any consecutive messages mapping to the same Bedrock role, not just
    tool-related ones, so two consecutive user text messages collapse into a single user
    message whose content preserves both text blocks in order.
    """
    chat_history = ChatHistory()
    chat_history.add_user_message("First question.")
    chat_history.add_user_message("Second question.")

    bedrock_chat_completion = BedrockChatCompletion()
    parsed_chat_history = bedrock_chat_completion._prepare_chat_history_for_request(chat_history)

    assert len(parsed_chat_history) == 1
    merged_message = parsed_chat_history[0]
    assert merged_message["role"] == "user"
    texts = [block["text"] for block in merged_message["content"] if "text" in block]
    assert texts == ["First question.", "Second question."]


@patch.object(boto3, "client", return_value=Mock())
def test_prepare_system_message_for_request(mock_client, bedrock_unit_test_env, chat_history) -> None:
    """Test preparing system message for request"""
    bedrock_chat_completion = BedrockChatCompletion()
    parsed_system_message = bedrock_chat_completion._prepare_system_messages_for_request(chat_history)

    assert isinstance(parsed_system_message, list)
    assert len(parsed_system_message) == 2


@pytest.mark.parametrize(
    "model_id",
    [
        "amazon.titan",
        "anthropic.claude",
        "cohere.command",
        "ai21.jamba",
        "meta.llama",
        "mistral.ai",
    ],
)
@patch.object(boto3, "client", return_value=Mock())
def test_prepare_settings_for_request(mock_client, model_id, chat_history) -> None:
    """Test preparing settings for request"""
    bedrock_chat_completion = BedrockChatCompletion(model_id=model_id)
    settings = BedrockChatPromptExecutionSettings()
    parsed_settings = bedrock_chat_completion._prepare_settings_for_request(chat_history, settings)

    assert isinstance(parsed_settings, dict)
    assert parsed_settings["modelId"] == bedrock_chat_completion.ai_model_id
    assert parsed_settings["messages"] == bedrock_chat_completion._prepare_chat_history_for_request(chat_history)
    assert parsed_settings["system"] == bedrock_chat_completion._prepare_system_messages_for_request(chat_history)
    assert isinstance(parsed_settings["inferenceConfig"], dict)
    assert all([parsed_settings["inferenceConfig"].values()])


@pytest.mark.parametrize(
    "model_id",
    [
        "arn:aws:bedrock:us-east-1:972143716085:application-inference-profile/123456",
    ],
)
@patch.object(boto3, "client", return_value=Mock())
def test_prepare_settings_for_request_with_application_inference_profile(mock_client, model_id, chat_history) -> None:
    """Test preparing settings for request"""
    # Without a valid model provider, it should raise an error
    bedrock_chat_completion = BedrockChatCompletion(model_id=model_id)
    settings = BedrockChatPromptExecutionSettings()
    with pytest.raises(
        ValueError,
        match=f"Model ID {model_id} does not contain a valid model provider name.",
    ):
        bedrock_chat_completion._prepare_settings_for_request(chat_history, settings)

    # With a valid model provider, it should not raise an error
    bedrock_chat_completion = BedrockChatCompletion(model_id=model_id, model_provider=BedrockModelProvider.AMAZON)
    parsed_settings = bedrock_chat_completion._prepare_settings_for_request(chat_history, settings)

    assert isinstance(parsed_settings, dict)
    assert parsed_settings["modelId"] == bedrock_chat_completion.ai_model_id
    assert parsed_settings["messages"] == bedrock_chat_completion._prepare_chat_history_for_request(chat_history)
    assert parsed_settings["system"] == bedrock_chat_completion._prepare_system_messages_for_request(chat_history)
    assert isinstance(parsed_settings["inferenceConfig"], dict)
    assert all([parsed_settings["inferenceConfig"].values()])


# endregion


# region chat completion


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "anthropic.claude",
        "cohere.command",
        "ai21.jamba",
        "meta.llama",
        "mistral.ai",
    ],
)
async def test_bedrock_chat_completion(
    model_id,
    chat_history: ChatHistory,
    mock_bedrock_chat_completion_response,
) -> None:
    """Test Amazon Bedrock Chat Completion complete method"""
    with patch.object(
        MockBedrockRuntimeClient, "converse", return_value=mock_bedrock_chat_completion_response
    ) as mock_converse:
        # Setup
        bedrock_chat_completion = BedrockChatCompletion(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockChatPromptExecutionSettings()
        response = await bedrock_chat_completion.get_chat_message_contents(chat_history=chat_history, settings=settings)

        # Assert
        mock_converse.assert_called_once_with(
            **(bedrock_chat_completion._prepare_settings_for_request(chat_history, settings))
        )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], ChatMessageContent)
        assert response[0].ai_model_id == model_id
        assert response[0].role == AuthorRole.ASSISTANT
        assert len(response[0].items) == 1
        assert isinstance(response[0].items[0], TextContent)
        assert response[0].finish_reason == FinishReason.STOP
        assert response[0].metadata["usage"] == CompletionUsage(
            prompt_tokens=mock_bedrock_chat_completion_response["usage"]["inputTokens"],
            completion_tokens=mock_bedrock_chat_completion_response["usage"]["outputTokens"],
        )
        assert (
            response[0].items[0].text
            == mock_bedrock_chat_completion_response["output"]["message"]["content"][0]["text"]
        )
        assert response[0].inner_content == mock_bedrock_chat_completion_response


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "anthropic.claude",
        "cohere.command",
        "ai21.jamba",
        "meta.llama",
        "mistral.ai",
    ],
)
async def test_bedrock_streaming_chat_completion(
    model_id,
    chat_history: ChatHistory,
    mock_bedrock_streaming_chat_completion_response,
) -> None:
    """Test Amazon Bedrock Streaming Chat Completion complete method"""
    with patch.object(
        MockBedrockRuntimeClient, "converse_stream", return_value=mock_bedrock_streaming_chat_completion_response
    ) as mock_converse_stream:
        # Setup
        bedrock_chat_completion = BedrockChatCompletion(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockChatPromptExecutionSettings()
        chunks: list[StreamingChatMessageContent] = []
        async for streaming_messages in bedrock_chat_completion.get_streaming_chat_message_contents(
            chat_history=chat_history, settings=settings
        ):
            chunks.extend(streaming_messages)
        response = reduce(lambda p, r: p + r, chunks)

        # Assert
        mock_converse_stream.assert_called_once_with(
            **(bedrock_chat_completion._prepare_settings_for_request(chat_history, settings))
        )

        assert isinstance(response, StreamingChatMessageContent)
        assert response.ai_model_id == model_id
        assert response.role == AuthorRole.ASSISTANT
        assert len(response.items) == 1
        assert isinstance(response.inner_content, list)
        assert len(response.inner_content) == 7
        assert response.finish_reason == FinishReason.STOP


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "anthropic.claude",
        "cohere.command",
        "ai21.jamba",
        "meta.llama",
        "mistral.ai",
    ],
)
async def test_bedrock_streaming_chat_completion_invalid_event(
    model_id,
    chat_history: ChatHistory,
    mock_bedrock_streaming_chat_completion_invalid_response,
) -> None:
    """Test Amazon Bedrock Streaming Chat Completion complete method"""
    with patch.object(
        MockBedrockRuntimeClient,
        "converse_stream",
        return_value=mock_bedrock_streaming_chat_completion_invalid_response,
    ):
        # Setup
        bedrock_chat_completion = BedrockChatCompletion(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockChatPromptExecutionSettings()
        with pytest.raises(ServiceInvalidResponseError):
            async for chunk in bedrock_chat_completion.get_streaming_chat_message_contents(
                chat_history=chat_history, settings=settings
            ):
                pass


# endregion
