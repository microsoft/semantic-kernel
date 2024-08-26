# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from opentelemetry.trace import StatusCode

from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    TEXT_COMPLETION_OPERATION,
    _messages_to_openai_format,
    trace_text_completion,
)

pytestmark = pytest.mark.parametrize(
    "service_type, execution_settings, mock_response, service_env_vars",
    [
        pytest.param(
            OpenAITextCompletion,
            PromptExecutionSettings(
                extension_data={
                    "max_tokens": 1000,
                    "temperature": 0.5,
                    "top_p": 0.9,
                }
            ),
            [
                TextContent(
                    ai_model_id="openai_text_model_id",
                    text="Test content",
                    metadata={"id": "test_id"},
                )
            ],
            {
                "OPENAI_API_KEY": "openai_api_key",
                "OPENAI_TEXT_MODEL_ID": "openai_text_model_id",
            },
            id="openai_text_completion",
        ),
        pytest.param(
            OllamaTextCompletion,
            PromptExecutionSettings(
                extension_data={
                    "max_tokens": 1000,
                    "temperature": 0.5,
                    "top_p": 0.9,
                }
            ),
            [
                TextContent(
                    ai_model_id="ollama_model",
                    text="Test content",
                    metadata={},
                )
            ],
            {
                "OLLAMA_MODEL": "ollama_model",
                "OLLAMA_HOST": "ollama_host",
            },
            id="ollama_text_completion",
        ),
    ],
    indirect=["service_env_vars"],
)


@pytest.mark.asyncio
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion(
    mock_span,
    service_type,
    execution_settings,
    mock_response,
    service_env_vars,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = service_type()

    with patch.object(service_type, "get_text_contents", return_value=mock_response):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        service_type.get_text_contents = trace_text_completion(service_type.MODEL_PROVIDER_NAME)(
            text_completion.get_text_contents
        )

        results: list[ChatMessageContent] = await text_completion.get_text_contents(
            prompt=prompt, settings=execution_settings
        )

        assert results == mock_response

        # Before the call to the model
        mock_span.set_attributes.assert_called_with({
            gen_ai_attributes.OPERATION: TEXT_COMPLETION_OPERATION,
            gen_ai_attributes.SYSTEM: service_type.MODEL_PROVIDER_NAME,
            gen_ai_attributes.MODEL: text_completion.ai_model_id,
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
            gen_ai_attributes.PROMPT_EVENT, {gen_ai_attributes.PROMPT_EVENT_PROMPT: prompt}
        )

        # After the call to the model
        # Not all connectors return the same metadata
        if mock_response[0].metadata.get("id") is not None:
            mock_span.set_attribute.assert_any_call(gen_ai_attributes.RESPONSE_ID, mock_response[0].metadata["id"])

        mock_span.add_event.assert_any_call(
            gen_ai_attributes.COMPLETION_EVENT,
            {gen_ai_attributes.COMPLETION_EVENT_COMPLETION: _messages_to_openai_format(mock_response)},
        )


@pytest.mark.asyncio
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion_exception(
    mock_span,
    service_type,
    execution_settings,
    mock_response,
    service_env_vars,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = service_type()

    with patch.object(service_type, "get_text_contents", side_effect=ServiceResponseException()):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        service_type.get_text_contents = trace_text_completion(service_type.MODEL_PROVIDER_NAME)(
            text_completion.get_text_contents
        )

        with pytest.raises(ServiceResponseException):
            await text_completion.get_text_contents(prompt=prompt, settings=execution_settings)

        exception = ServiceResponseException()
        mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
        mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

        mock_span.end.assert_any_call()
