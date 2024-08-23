# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, patch

import pytest
from opentelemetry.trace import StatusCode

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import OpenAIChatCompletionBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import OpenAITextCompletionBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    CHAT_COMPLETION_OPERATION,
    TEXT_COMPLETION_OPERATION,
    _messages_to_openai_format,
    trace_chat_completion,
    trace_text_completion,
)


@pytest.mark.asyncio
@patch.object(OpenAIChatCompletion, "get_chat_message_contents", new_callable=AsyncMock)
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_chat_completion(
    mock_span,
    mock_get_chat_message_contents,
    mock_get_chat_message_contents_response,
    mock_prompt_execution_settings,
    chat_history,
    openai_unit_test_env,
    model_diagnostics_unit_test_env,
):
    mock_get_chat_message_contents.return_value = mock_get_chat_message_contents_response

    chat_completion = OpenAIChatCompletion()

    # We need to reapply the decorator to the method since the mock will not have the decorator applied
    OpenAIChatCompletion.get_chat_message_contents = trace_chat_completion(
        OpenAIChatCompletionBase.MODEL_PROVIDER_NAME
    )(chat_completion.get_chat_message_contents)

    results: list[ChatMessageContent] = await chat_completion.get_chat_message_contents(
        chat_history=chat_history, settings=mock_prompt_execution_settings
    )

    assert results == mock_get_chat_message_contents_response

    # Before the call to the model
    mock_span.set_attributes.assert_called_with({
        gen_ai_attributes.OPERATION: CHAT_COMPLETION_OPERATION,
        gen_ai_attributes.SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
        gen_ai_attributes.MODEL: openai_unit_test_env["OPENAI_CHAT_MODEL_ID"],
    })
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.MAX_TOKENS, mock_prompt_execution_settings.extension_data["max_tokens"]
    )
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.TEMPERATURE, mock_prompt_execution_settings.extension_data["temperature"]
    )
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.TOP_P, mock_prompt_execution_settings.extension_data["top_p"]
    )
    mock_span.add_event.assert_any_call(
        gen_ai_attributes.PROMPT_EVENT,
        {gen_ai_attributes.PROMPT_EVENT_PROMPT: _messages_to_openai_format(chat_history)},
    )

    # After the call to the model
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.RESPONSE_ID, mock_get_chat_message_contents_response[0].metadata["id"]
    )
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.FINISH_REASON,
        ",".join([str(completion.finish_reason) for completion in mock_get_chat_message_contents_response]),
    )
    mock_span.add_event.assert_any_call(
        gen_ai_attributes.COMPLETION_EVENT,
        {
            gen_ai_attributes.COMPLETION_EVENT_COMPLETION: json.dumps([
                str(completion) for completion in mock_get_chat_message_contents_response
            ])
        },
    )


@pytest.mark.asyncio
@patch.object(OpenAITextCompletion, "get_text_contents", new_callable=AsyncMock)
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion(
    mock_span,
    mock_get_text_contents,
    mock_get_text_contents_response,
    mock_prompt_execution_settings,
    prompt,
    openai_unit_test_env,
    model_diagnostics_unit_test_env,
):
    mock_get_text_contents.return_value = mock_get_text_contents_response

    text_completion = OpenAITextCompletion()

    # We need to reapply the decorator to the method since the mock will not have the decorator applied
    OpenAITextCompletion.get_text_contents = trace_text_completion(OpenAITextCompletionBase.MODEL_PROVIDER_NAME)(
        text_completion.get_text_contents
    )

    results: list[TextContent] = await text_completion.get_text_contents(
        prompt=prompt, settings=mock_prompt_execution_settings
    )

    assert results == mock_get_text_contents_response

    # Before the call to the model
    mock_span.set_attributes.assert_called_with({
        gen_ai_attributes.OPERATION: TEXT_COMPLETION_OPERATION,
        gen_ai_attributes.SYSTEM: OpenAITextCompletionBase.MODEL_PROVIDER_NAME,
        gen_ai_attributes.MODEL: openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
    })
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.MAX_TOKENS, mock_prompt_execution_settings.extension_data["max_tokens"]
    )
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.TEMPERATURE, mock_prompt_execution_settings.extension_data["temperature"]
    )
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.TOP_P, mock_prompt_execution_settings.extension_data["top_p"]
    )
    mock_span.add_event.assert_any_call(gen_ai_attributes.PROMPT_EVENT, {gen_ai_attributes.PROMPT_EVENT_PROMPT: prompt})

    # After the call to the model
    mock_span.set_attribute.assert_any_call(
        gen_ai_attributes.RESPONSE_ID, mock_get_text_contents_response[0].metadata["id"]
    )
    mock_span.add_event.assert_any_call(
        gen_ai_attributes.COMPLETION_EVENT,
        {
            gen_ai_attributes.COMPLETION_EVENT_COMPLETION: json.dumps([
                str(completion) for completion in mock_get_text_contents_response
            ])
        },
    )


@pytest.mark.asyncio
@patch.object(OpenAIChatCompletion, "get_chat_message_contents", new_callable=AsyncMock)
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_chat_completion_exception(
    mock_span,
    mock_get_chat_message_contents,
    mock_prompt_execution_settings,
    chat_history,
    openai_unit_test_env,
    model_diagnostics_unit_test_env,
):
    chat_completion = OpenAIChatCompletion()

    mock_get_chat_message_contents.side_effect = ServiceResponseException()
    # We need to reapply the decorator to the method since the mock will not have the decorator applied
    OpenAIChatCompletion.get_chat_message_contents = trace_chat_completion(
        OpenAIChatCompletionBase.MODEL_PROVIDER_NAME
    )(chat_completion.get_chat_message_contents)

    with pytest.raises(ServiceResponseException):
        await chat_completion.get_chat_message_contents(
            chat_history=chat_history, settings=mock_prompt_execution_settings
        )

    mock_span.set_attributes.assert_called_with({
        gen_ai_attributes.OPERATION: CHAT_COMPLETION_OPERATION,
        gen_ai_attributes.SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
        gen_ai_attributes.MODEL: openai_unit_test_env["OPENAI_CHAT_MODEL_ID"],
    })

    exception = ServiceResponseException()
    mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
    mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

    mock_span.end.assert_any_call()


@pytest.mark.asyncio
@patch.object(OpenAITextCompletion, "get_text_contents", new_callable=AsyncMock)
@patch("opentelemetry.trace.INVALID_SPAN")
async def test_trace_text_completion_exception(
    mock_span,
    mock_get_text_contents,
    mock_prompt_execution_settings,
    prompt,
    openai_unit_test_env,
    model_diagnostics_unit_test_env,
):
    text_completion = OpenAITextCompletion()

    mock_get_text_contents.side_effect = ServiceResponseException()
    # We need to reapply the decorator to the method since the mock will not have the decorator applied
    OpenAITextCompletion.get_text_contents = trace_text_completion(OpenAITextCompletionBase.MODEL_PROVIDER_NAME)(
        text_completion.get_text_contents
    )

    with pytest.raises(ServiceResponseException):
        await text_completion.get_text_contents(prompt=prompt, settings=mock_prompt_execution_settings)

    mock_span.set_attributes.assert_called_with({
        gen_ai_attributes.OPERATION: TEXT_COMPLETION_OPERATION,
        gen_ai_attributes.SYSTEM: OpenAIChatCompletionBase.MODEL_PROVIDER_NAME,
        gen_ai_attributes.MODEL: openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
    })

    exception = ServiceResponseException()
    mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
    mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

    mock_span.end.assert_any_call()
