# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from openai.types import Completion as TextCompletion
from openai.types import CompletionChoice
from opentelemetry.trace import StatusCode

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import (
    OpenAIChatCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.utils.telemetry.const import (
    CHAT_COMPLETION_OPERATION,
    COMPLETION_EVENT,
    COMPLETION_EVENT_COMPLETION,
    ERROR_TYPE,
    FINISH_REASON,
    MAX_TOKENS,
    MODEL,
    OPERATION,
    PROMPT_EVENT,
    PROMPT_EVENT_PROMPT,
    RESPONSE_ID,
    SYSTEM,
    TEMPERATURE,
    TEXT_COMPLETION_OPERATION,
    TOP_P,
)

TEST_CONTENT = "Test content"
TEST_RESPONSE_ID = "dummy_id"
TEST_MAX_TOKENS = "1000"
TEST_MODEL = "dummy_model"
TEST_TEMPERATURE = "0.5"
TEST_TOP_P = "0.9"
TEST_CREATED_AT = 1
TEST_TEXT_PROMPT = "Test prompt"
EXPECTED_CHAT_COMPLETION_EVENT_PAYLOAD = (
    f'[{{"role": "assistant", "content": "{TEST_CONTENT}"}}]'
)
EXPECTED_TEXT_COMPLETION_EVENT_PAYLOAD = f'["{TEST_CONTENT}"]'

TEST_CHAT_RESPONSE = [
    ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        ai_model_id=TEST_MODEL,
        content=TEST_CONTENT,
        metadata={"id": TEST_RESPONSE_ID},
        finish_reason=FinishReason.STOP,
    )
]

TEST_TEXT_RESPONSE = TextCompletion(
    model=TEST_MODEL,
    text=TEST_CONTENT,
    id=TEST_RESPONSE_ID,
    choices=[CompletionChoice(index=0, text=TEST_CONTENT, finish_reason="stop")],
    created=TEST_CREATED_AT,
    object="text_completion",
)

TEST_TEXT_RESPONSE_METADATA = {
    "id": TEST_RESPONSE_ID,
    "created": TEST_CREATED_AT,
    "system_fingerprint": None,
    "logprobs": None,
    "usage": None,
}

EXPECTED_TEXT_CONTENT = [
    TextContent(
        ai_model_id=TEST_MODEL,
        text=TEST_CONTENT,
        encoding=None,
        metadata=TEST_TEXT_RESPONSE_METADATA,
        inner_content=TEST_TEXT_RESPONSE,
    )
]


@pytest.mark.asyncio
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_model_diagnostics_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_sensitive_events_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_request",
    return_value=TEST_CHAT_RESPONSE,
)
@patch("opentelemetry.trace.INVALID_SPAN")
async def test_trace_chat_completion(
    mock_span,
    mock_send_chat_request,
    mock_sensitive_events_enabled,
    mock_model_diagnostics_enabled,
    openai_unit_test_env,
):
    chat_completion = OpenAIChatCompletion(
        ai_model_id=TEST_MODEL, env_file_path="test.env"
    )
    extension_data = {
        "max_tokens": TEST_MAX_TOKENS,
        "temperature": TEST_TEMPERATURE,
        "top_p": TEST_TOP_P,
    }

    results: list[ChatMessageContent] = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(),
        settings=PromptExecutionSettings(extension_data=extension_data),
    )

    assert results == TEST_CHAT_RESPONSE

    mock_span.set_attributes.assert_called_with(
        {
            OPERATION: CHAT_COMPLETION_OPERATION,
            SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
            MODEL: TEST_MODEL,
        }
    )
    mock_span.set_attribute.assert_any_call(MAX_TOKENS, TEST_MAX_TOKENS)
    mock_span.set_attribute.assert_any_call(TEMPERATURE, TEST_TEMPERATURE)
    mock_span.set_attribute.assert_any_call(TOP_P, TEST_TOP_P)
    mock_span.add_event.assert_any_call(PROMPT_EVENT, {PROMPT_EVENT_PROMPT: "[]"})

    mock_span.set_attribute.assert_any_call(RESPONSE_ID, TEST_RESPONSE_ID)
    mock_span.set_attribute.assert_any_call(FINISH_REASON, str(FinishReason.STOP))
    mock_span.add_event.assert_any_call(
        COMPLETION_EVENT,
        {COMPLETION_EVENT_COMPLETION: EXPECTED_CHAT_COMPLETION_EVENT_PAYLOAD},
    )


@pytest.mark.asyncio
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_model_diagnostics_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_sensitive_events_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base.OpenAITextCompletionBase._send_request",
    return_value=TEST_TEXT_RESPONSE,
)
@patch("opentelemetry.trace.INVALID_SPAN")
async def test_trace_text_completion(
    mock_span,
    mock_send_request,
    mock_sensitive_events_enabled,
    mock_model_diagnostics_enabled,
    openai_unit_test_env,
):
    chat_completion = OpenAITextCompletion(
        ai_model_id=TEST_MODEL, env_file_path="test.env"
    )
    extension_data = {
        "max_tokens": TEST_MAX_TOKENS,
        "temperature": TEST_TEMPERATURE,
        "top_p": TEST_TOP_P,
    }

    results: list[TextContent] = await chat_completion.get_text_contents(
        prompt=TEST_TEXT_PROMPT,
        settings=PromptExecutionSettings(extension_data=extension_data),
    )

    assert results == EXPECTED_TEXT_CONTENT

    mock_span.set_attributes.assert_called_with(
        {
            OPERATION: TEXT_COMPLETION_OPERATION,
            SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
            MODEL: TEST_MODEL,
        }
    )
    mock_span.set_attribute.assert_any_call(MAX_TOKENS, TEST_MAX_TOKENS)
    mock_span.set_attribute.assert_any_call(TEMPERATURE, TEST_TEMPERATURE)
    mock_span.set_attribute.assert_any_call(TOP_P, TEST_TOP_P)
    mock_span.add_event.assert_any_call(
        PROMPT_EVENT, {PROMPT_EVENT_PROMPT: TEST_TEXT_PROMPT}
    )

    mock_span.set_attribute.assert_any_call(RESPONSE_ID, TEST_RESPONSE_ID)
    mock_span.add_event.assert_any_call(
        COMPLETION_EVENT,
        {COMPLETION_EVENT_COMPLETION: EXPECTED_TEXT_COMPLETION_EVENT_PAYLOAD},
    )


@pytest.mark.asyncio
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_model_diagnostics_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_sensitive_events_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base.OpenAIChatCompletionBase._send_chat_request",
    side_effect=ServiceResponseException,
)
@patch("opentelemetry.trace.INVALID_SPAN")
async def test_trace_chat_completion_exception(
    mock_span,
    mock_send_chat_request,
    mock_sensitive_events_enabled,
    mock_model_diagnostics_enabled,
    openai_unit_test_env,
):
    chat_completion = OpenAIChatCompletion(
        ai_model_id=TEST_MODEL, env_file_path="test.env"
    )
    extension_data = {
        "max_tokens": TEST_MAX_TOKENS,
        "temperature": TEST_TEMPERATURE,
        "top_p": TEST_TOP_P,
    }

    with pytest.raises(ServiceResponseException):
        await chat_completion.get_chat_message_contents(
            chat_history=ChatHistory(),
            settings=PromptExecutionSettings(extension_data=extension_data),
        )

    mock_span.set_attributes.assert_called_with(
        {
            OPERATION: CHAT_COMPLETION_OPERATION,
            SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
            MODEL: TEST_MODEL,
        }
    )

    exception = ServiceResponseException()
    mock_span.set_attribute.assert_any_call(ERROR_TYPE, str(type(exception)))
    mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

    mock_span.end.assert_any_call()


@pytest.mark.asyncio
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_model_diagnostics_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.utils.telemetry.decorators.are_sensitive_events_enabled",
    return_value=True,
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base.OpenAITextCompletionBase._send_request",
    side_effect=ServiceResponseException,
)
@patch("opentelemetry.trace.INVALID_SPAN")
async def test_trace_text_completion_exception(
    mock_span,
    mock_send_chat_request,
    mock_sensitive_events_enabled,
    mock_model_diagnostics_enabled,
    openai_unit_test_env,
):
    chat_completion = OpenAITextCompletion(
        ai_model_id=TEST_MODEL, env_file_path="test.env"
    )
    extension_data = {
        "max_tokens": TEST_MAX_TOKENS,
        "temperature": TEST_TEMPERATURE,
        "top_p": TEST_TOP_P,
    }

    with pytest.raises(ServiceResponseException):
        await chat_completion.get_text_contents(
            prompt=TEST_TEXT_PROMPT,
            settings=PromptExecutionSettings(extension_data=extension_data),
        )

    mock_span.set_attributes.assert_called_with(
        {
            OPERATION: TEXT_COMPLETION_OPERATION,
            SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
            MODEL: TEST_MODEL,
        }
    )

    exception = ServiceResponseException()
    mock_span.set_attribute.assert_any_call(ERROR_TYPE, str(type(exception)))
    mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

    mock_span.end.assert_any_call()
