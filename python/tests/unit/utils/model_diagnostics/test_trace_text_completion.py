# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import ANY, patch

import pytest
from opentelemetry.trace import StatusCode

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    TEXT_COMPLETION_OPERATION,
    trace_text_completion,
)
from tests.unit.utils.model_diagnostics.conftest import MockTextCompletion

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
                TextContent(
                    ai_model_id="ai_model_id",
                    text="Test content",
                    metadata={"id": "test_id"},
                )
            ],
            id="test_execution_settings_with_extension_data",
        ),
        pytest.param(
            PromptExecutionSettings(),
            [
                TextContent(
                    ai_model_id="ai_model_id",
                    text="Test content",
                    metadata={"id": "test_id"},
                )
            ],
            id="test_execution_settings_no_extension_data",
        ),
        pytest.param(
            PromptExecutionSettings(),
            [
                TextContent(
                    ai_model_id="ai_model_id",
                    text="Test content",
                    metadata={},
                )
            ],
            id="test_text_content_no_metadata",
        ),
    ],
)


@patch("semantic_kernel.utils.telemetry.model_diagnostics.decorators.logger")
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion(
    mock_span,
    mock_logger,
    execution_settings,
    mock_response,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = MockTextCompletion(ai_model_id="ai_model_id")

    with patch.object(MockTextCompletion, "_inner_get_text_contents", return_value=mock_response):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion._inner_get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion._inner_get_text_contents
        )

        results: list[ChatMessageContent] = await text_completion.get_text_contents(
            prompt=prompt, settings=execution_settings
        )

        assert results == mock_response

        # Before the call to the model
        mock_span.set_attributes.assert_called_with({
            gen_ai_attributes.OPERATION: TEXT_COMPLETION_OPERATION,
            gen_ai_attributes.SYSTEM: MockTextCompletion.MODEL_PROVIDER_NAME,
            gen_ai_attributes.MODEL: text_completion.ai_model_id,
        })

        with pytest.raises(AssertionError):
            # The service_url attribute is not set for text completion
            mock_span.set_attribute.assert_any_call(gen_ai_attributes.ADDRESS, ANY)

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

        mock_logger.info.assert_any_call(
            prompt,
            extra={
                gen_ai_attributes.EVENT_NAME: gen_ai_attributes.PROMPT,
                gen_ai_attributes.SYSTEM: MockTextCompletion.MODEL_PROVIDER_NAME,
            },
        )

        # After the call to the model
        # Not all connectors return the same metadata
        if mock_response[0].metadata.get("id") is not None:
            mock_span.set_attribute.assert_any_call(gen_ai_attributes.RESPONSE_ID, mock_response[0].metadata["id"])

        mock_logger.info.assert_any_call(
            json.dumps({"message": results[0].to_dict()}),
            extra={
                gen_ai_attributes.EVENT_NAME: gen_ai_attributes.CHOICE,
                gen_ai_attributes.SYSTEM: MockTextCompletion.MODEL_PROVIDER_NAME,
            },
        )


@patch("semantic_kernel.utils.telemetry.model_diagnostics.decorators.logger")
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion_exception(
    mock_span,
    mock_logger,
    execution_settings,
    mock_response,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = MockTextCompletion(ai_model_id="ai_model_id")

    with patch.object(MockTextCompletion, "_inner_get_text_contents", side_effect=ServiceResponseException()):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion._inner_get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion._inner_get_text_contents
        )

        with pytest.raises(ServiceResponseException):
            await text_completion.get_text_contents(prompt=prompt, settings=execution_settings)

        exception = ServiceResponseException()
        mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
        mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

        mock_span.end.assert_any_call()

        mock_logger.info.assert_any_call(
            prompt,
            extra={
                gen_ai_attributes.EVENT_NAME: gen_ai_attributes.PROMPT,
                gen_ai_attributes.SYSTEM: MockTextCompletion.MODEL_PROVIDER_NAME,
            },
        )
