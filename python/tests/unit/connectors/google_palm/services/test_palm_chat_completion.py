# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

if sys.version_info >= (3, 9):
    from google.generativeai.types import ChatResponse, MessageDict

    from semantic_kernel.connectors.ai.google_palm import (
        GooglePalmChatPromptExecutionSettings,
    )
    from semantic_kernel.connectors.ai.google_palm.services.gp_chat_completion import (
        GooglePalmChatCompletion,
    )
    from semantic_kernel.contents.chat_history import ChatHistory


pytestmark = pytest.mark.skipif(sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater")


def test_google_palm_chat_completion_init() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"

    gp_chat_completion = GooglePalmChatCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
    )

    assert gp_chat_completion.ai_model_id == ai_model_id
    assert gp_chat_completion.api_key == api_key
    assert isinstance(gp_chat_completion, GooglePalmChatCompletion)


def test_google_palm_chat_completion_init_with_empty_api_key() -> None:
    ai_model_id = "test_model_id"
    # api_key = "test_api_key"

    with pytest.raises(ValidationError, match="api_key"):
        GooglePalmChatCompletion(
            ai_model_id=ai_model_id,
            api_key="",
        )


@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_chat_call_with_parameters() -> None:
    class MockChatResponse(ChatResponse):
        def last(self):
            return ""

        def reply(self):
            return self

    gp_response = MockChatResponse()
    gp_response.candidates = [MessageDict(content="Example response", author=3)]
    gp_response.filters = None
    mock_response = MagicMock()
    mock_response.last = asyncio.Future()
    mock_response.last.set_result(gp_response)
    mock_gp = MagicMock()
    mock_gp.chat.return_value = gp_response
    with patch(
        "semantic_kernel.connectors.ai.google_palm.services.gp_chat_completion.palm",
        new=mock_gp,
    ):
        ai_model_id = "test_model_id"
        api_key = "test_api_key"
        chats = ChatHistory()
        chats.add_user_message("Hello word")
        gp_chat_completion = GooglePalmChatCompletion(
            ai_model_id=ai_model_id,
            api_key=api_key,
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.complete_chat(chats, settings)

        assert isinstance(response[0].content, str) and len(response) > 0
        print(mock_gp.chat)
        mock_gp.chat.assert_called_once_with(
            model=ai_model_id,
            temperature=settings.temperature,
            top_p=settings.top_p,
            top_k=settings.top_k,
            candidate_count=settings.candidate_count,
            messages=gp_chat_completion._prepare_chat_history_for_request(chats),
        )
