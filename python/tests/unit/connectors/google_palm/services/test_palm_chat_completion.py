# Copyright (c) Microsoft. All rights reserved.

import asyncio
<<<<<<< HEAD
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
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
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
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        )


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
async def test_google_palm_text_completion_complete_chat_call_with_parameters(google_palm_unit_test_env) -> None:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
async def test_google_palm_text_completion_complete_chat_call_with_parameters(google_palm_unit_test_env) -> None:
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
async def test_google_palm_text_completion_complete_chat_call_with_parameters(google_palm_unit_test_env) -> None:
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
async def test_google_palm_text_completion_complete_chat_call_with_parameters(google_palm_unit_test_env) -> None:
=======
async def test_google_palm_text_completion_complete_chat_call_with_parameters() -> None:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
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
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        api_key = "test_api_key"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        chats = ChatHistory()
        chats.add_user_message("Hello word")
        gp_chat_completion = GooglePalmChatCompletion(
            ai_model_id=ai_model_id,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.get_chat_message_contents(chats, settings)
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.get_chat_message_contents(chats, settings)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.get_chat_message_contents(chats, settings)
=======
            api_key=api_key,
        )
        settings = GooglePalmChatPromptExecutionSettings()
        response = await gp_chat_completion.complete_chat(chats, settings)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        assert isinstance(response[0].content, str) and len(response) > 0
        print(mock_gp.chat)
        mock_gp.chat.assert_called_once_with(
            model=ai_model_id,
            temperature=settings.temperature,
            top_p=settings.top_p,
            top_k=settings.top_k,
            candidate_count=settings.candidate_count,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            messages=[message.to_dict(role_key="author") for message in chats.messages],
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            messages=[message.to_dict(role_key="author") for message in chats.messages],
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            messages=[message.to_dict(role_key="author") for message in chats.messages],
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            messages=[message.to_dict(role_key="author") for message in chats.messages],
=======
            messages=gp_chat_completion._prepare_chat_history_for_request(chats),
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        )
