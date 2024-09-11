# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from opentelemetry.trace import StatusCode

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    CHAT_COMPLETION_OPERATION,
    _messages_to_openai_format,
    trace_chat_completion,
)
from tests.unit.utils.model_diagnostics.conftest import MockChatCompletion

pytestmark = pytest.mark.parametrize(
    "execution_settings, mock_response",
    [
        pytest.param(
            PromptExecutionSettings(
                extension_data={
                    "max_tokens": 1000,
                    "temperature": 0.5,
                    "top_p": 0.9,
                }
            ),
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    ai_model_id="ai_model_id",
                    content="Test content",
                    metadata={"id": "test_id"},
                    finish_reason=FinishReason.STOP,
                )
            ],
            id="test_execution_settings_with_extension_data",
        ),
        pytest.param(
            PromptExecutionSettings(),
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    ai_model_id="ai_model_id",
                    metadata={"id": "test_id"},
                    finish_reason=FinishReason.STOP,
                )
            ],
            id="test_execution_settings_no_extension_data",
        ),
        pytest.param(
            PromptExecutionSettings(),
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    ai_model_id="ai_model_id",
                    metadata={},
                    finish_reason=FinishReason.STOP,
                )
            ],
            id="test_chat_message_content_no_metadata",
        ),
        pytest.param(
            PromptExecutionSettings(),
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    ai_model_id="ai_model_id",
                    metadata={"id": "test_id"},
                )
            ],
            id="test_chat_message_content_no_finish_reason",
        ),
    ],
)


@pytest.mark.asyncio
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_chat_completion(
    mock_span,
    execution_settings,
    mock_response,
    chat_history,
    model_diagnostics_unit_test_env,
):
    # Setup
    chat_completion: ChatCompletionClientBase = MockChatCompletion(ai_model_id="ai_model_id")

    with patch.object(MockChatCompletion, "_inner_get_chat_message_contents", return_value=mock_response):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockChatCompletion._inner_get_chat_message_contents = trace_chat_completion(
            MockChatCompletion.MODEL_PROVIDER_NAME
        )(chat_completion._inner_get_chat_message_contents)

        results: list[ChatMessageContent] = await chat_completion.get_chat_message_contents(
            chat_history, execution_settings
        )

        assert results == mock_response

        # Before the call to the model
        mock_span.set_attributes.assert_called_with({
            gen_ai_attributes.OPERATION: CHAT_COMPLETION_OPERATION,
            gen_ai_attributes.SYSTEM: MockChatCompletion.MODEL_PROVIDER_NAME,
            gen_ai_attributes.MODEL: chat_completion.ai_model_id,
        })

        # No all connectors take the same parameters
        if execution_settings.extension_data.get("max_tokens") is not None:
            mock_span.set_attribute.assert_any_call(
                gen_ai_attributes.MAX_TOKENS, execution_settings.extension_data["max_tokens"]
            )
        if execution_settings.extension_data.get("temperature") is not None:
            mock_span.set_attribute.assert_any_call(
                gen_ai_attributes.TEMPERATURE, execution_settings.extension_data["temperature"]
            )
        if execution_settings.extension_data.get("top_p") is not None:
            mock_span.set_attribute.assert_any_call(gen_ai_attributes.TOP_P, execution_settings.extension_data["top_p"])

        mock_span.add_event.assert_any_call(
            gen_ai_attributes.PROMPT_EVENT,
            {gen_ai_attributes.PROMPT_EVENT_PROMPT: _messages_to_openai_format(chat_history)},
        )

        # After the call to the model
        # Not all connectors return the same metadata
        if mock_response[0].metadata.get("id") is not None:
            mock_span.set_attribute.assert_any_call(gen_ai_attributes.RESPONSE_ID, mock_response[0].metadata["id"])
        if any(completion.finish_reason is not None for completion in mock_response):
            mock_span.set_attribute.assert_any_call(
                gen_ai_attributes.FINISH_REASON,
                ",".join([str(completion.finish_reason) for completion in mock_response]),
            )

        mock_span.add_event.assert_any_call(
            gen_ai_attributes.COMPLETION_EVENT,
            {gen_ai_attributes.COMPLETION_EVENT_COMPLETION: _messages_to_openai_format(mock_response)},
        )


@pytest.mark.asyncio
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_chat_completion_exception(
    mock_span,
    execution_settings,
    mock_response,
    chat_history,
    model_diagnostics_unit_test_env,
):
    # Setup
    chat_completion: ChatCompletionClientBase = MockChatCompletion(ai_model_id="ai_model_id")

    with patch.object(MockChatCompletion, "_inner_get_chat_message_contents", side_effect=ServiceResponseException()):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockChatCompletion._inner_get_chat_message_contents = trace_chat_completion(
            MockChatCompletion.MODEL_PROVIDER_NAME
        )(chat_completion._inner_get_chat_message_contents)

        with pytest.raises(ServiceResponseException):
            await chat_completion.get_chat_message_contents(chat_history, execution_settings)

        exception = ServiceResponseException()
        mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
        mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

        mock_span.end.assert_any_call()
