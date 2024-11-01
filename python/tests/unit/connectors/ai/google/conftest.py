# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_history import ChatHistory


@pytest.fixture()
def service_id() -> str:
    return "test_service_id"


@pytest.fixture()
def chat_history() -> ChatHistory:
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    return chat_history


@pytest.fixture()
def prompt() -> str:
    return "test_prompt"
