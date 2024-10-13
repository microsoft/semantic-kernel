# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

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
    _messages_to_openai_format,
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


@pytest.mark.asyncio
@patch("opentelemetry.trace.INVALID_SPAN")  # When no tracer provider is available, the span will be an INVALID_SPAN
async def test_trace_text_completion(
    mock_span,
    execution_settings,
    mock_response,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = MockTextCompletion(ai_model_id="ai_model_id")

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    with patch.object(MockTextCompletion, "_inner_get_text_contents", return_value=mock_response):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion._inner_get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion._inner_get_text_contents
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    with patch.object(MockTextCompletion, "get_text_contents", return_value=mock_response):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion.get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion.get_text_contents
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
    execution_settings,
    mock_response,
    prompt,
    model_diagnostics_unit_test_env,
):
    # Setup
    text_completion: TextCompletionClientBase = MockTextCompletion(ai_model_id="ai_model_id")

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    with patch.object(MockTextCompletion, "_inner_get_text_contents", side_effect=ServiceResponseException()):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion._inner_get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion._inner_get_text_contents
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    with patch.object(MockTextCompletion, "get_text_contents", side_effect=ServiceResponseException()):
        # We need to reapply the decorator to the method since the mock will not have the decorator applied
        MockTextCompletion.get_text_contents = trace_text_completion(MockTextCompletion.MODEL_PROVIDER_NAME)(
            text_completion.get_text_contents
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        )

        with pytest.raises(ServiceResponseException):
            await text_completion.get_text_contents(prompt=prompt, settings=execution_settings)

        exception = ServiceResponseException()
        mock_span.set_attribute.assert_any_call(gen_ai_attributes.ERROR_TYPE, str(type(exception)))
        mock_span.set_status.assert_any_call(StatusCode.ERROR, repr(exception))

        mock_span.end.assert_any_call()
