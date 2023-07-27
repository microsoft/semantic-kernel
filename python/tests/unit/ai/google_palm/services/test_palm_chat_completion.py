# Copyright (c) Microsoft. All rights reserved.

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from semantic_kernel.connectors.ai.chat_request_settings import (
    ChatRequestSettings,
)
from semantic_kernel.connectors.ai.google_palm.services.gp_chat_completion import (
    GooglePalmChatCompletion
)


def test_palm_chat_completion_init() -> None:
    model_id = "test_model_id"
    api_key = "test_api_key"

    gp_chat_completion = GooglePalmChatCompletion(
        model_id=model_id,
        api_key=api_key,
    )

    assert gp_chat_completion._model_id == model_id
    assert gp_chat_completion._api_key == api_key
    assert isinstance(gp_chat_completion, GooglePalmChatCompletion)

def test_google_palm_chat_completion_init_with_empty_api_key() -> None:
    model_id = "test_model_id"
    #api_key = "test_api_key"

    with pytest.raises(
        ValueError, match="The Google PaLM API key cannot be `None` or empty"
    ):
        GooglePalmChatCompletion(
            model_id=model_id,
            api_key="",
        )

@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_async_call_with_parameters() -> None:
    mock_response = MagicMock()
    mock_response.last = asyncio.Future()
    mock_response.last.set_result("Example response")
    mock_gp = MagicMock()
    mock_gp.chat.return_value = mock_response
    with patch (
        "semantic_kernel.connectors.ai.google_palm.services.gp_chat_completion.palm",
        new=mock_gp,
    ):
        model_id = "test_model_id"
        api_key = "test_api_key"
        prompt = [("user", "hello world")]
        context = "test_context"
        gp_chat_completion = GooglePalmChatCompletion(
            model_id=model_id,
            api_key=api_key,
        )
        settings = ChatRequestSettings()
        response = await gp_chat_completion.complete_chat_async(prompt, settings, context)
        assert isinstance(response.result(), str) and len(response.result()) > 0

        mock_gp.chat.assert_called_once_with(
            model=model_id,
            context=context,
            examples=None,
            temperature=settings.temperature,
            candidate_count=settings.number_of_responses,
            top_p=settings.top_p,
            prompt=None,
            messages=prompt[-1][1],
        )