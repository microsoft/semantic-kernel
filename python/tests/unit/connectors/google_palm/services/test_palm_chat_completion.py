# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from google.generativeai.types import ChatResponse, MessageDict

from semantic_kernel.connectors.ai.google_palm import GooglePalmChatPromptExecutionSettings
from semantic_kernel.connectors.ai.google_palm.services.gp_chat_completion import GooglePalmChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_google_palm_chat_completion_init(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    gp_chat_completion = GooglePalmChatCompletion(ai_model_id=ai_model_id)

    assert gp_chat_completion.ai_model_id == ai_model_id
    assert gp_chat_completion.api_key == google_palm_unit_test_env["GOOGLE_PALM_API_KEY"]
    assert isinstance(gp_chat_completion, GooglePalmChatCompletion)


@pytest.mark.parametrize("exclude_list", [["GOOGLE_PALM_API_KEY"]], indirect=True)
def test_google_palm_chat_completion_init_with_empty_api_key(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        GooglePalmChatCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.asyncio
async def test_google_palm_text_completion_complete_chat_call_with_parameters(google_palm_unit_test_env) -> None:
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
        chats = ChatHistory()
        chats.add_user_message("Hello word")
        gp_chat_completion = GooglePalmChatCompletion(
            ai_model_id=ai_model_id,
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.get_chat_message_contents(chats, settings)

        assert isinstance(response[0].content, str) and len(response) > 0
        print(mock_gp.chat)
        mock_gp.chat.assert_called_once_with(
            model=ai_model_id,
            temperature=settings.temperature,
            top_p=settings.top_p,
            top_k=settings.top_k,
            candidate_count=settings.candidate_count,
            messages=[message.to_dict(role_key="author") for message in chats.messages],
        )
