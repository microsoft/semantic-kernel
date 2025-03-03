# Copyright (c) Microsoft. All rights reserved.

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.file_citation_annotation import FileCitation, FileCitationAnnotation
from openai.types.beta.threads.file_path_annotation import FilePath, FilePathAnnotation
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock


@pytest.fixture
def mock_thread():
    class MockThread:
        id = "test_thread_id"

    return MockThread()


@pytest.fixture
def mock_thread_messages():
    class MockMessage:
        def __init__(self, id, role, content, assistant_id=None):
            self.id = id
            self.role = role
            self.content = content
            self.assistant_id = assistant_id

    return [
        MockMessage(
            id="test_message_id_1",
            role="user",
            content=[
                TextContentBlock(
                    type="text",
                    text=Text(
                        value="Hello",
                        annotations=[
                            FilePathAnnotation(
                                type="file_path",
                                file_path=FilePath(file_id="test_file_id"),
                                end_index=5,
                                start_index=0,
                                text="Hello",
                            ),
                            FileCitationAnnotation(
                                type="file_citation",
                                file_citation=FileCitation(file_id="test_file_id"),
                                text="Hello",
                                start_index=0,
                                end_index=5,
                            ),
                        ],
                    ),
                )
            ],
        ),
        MockMessage(
            id="test_message_id_2",
            role="assistant",
            content=[
                ImageFileContentBlock(type="image_file", image_file=ImageFile(file_id="test_file_id", detail="auto"))
            ],
            assistant_id="assistant_1",
        ),
    ]


@pytest.fixture
def openai_client(assistant_definition, mock_thread, mock_thread_messages) -> AsyncMock:
    async def mock_list_messages(*args, **kwargs) -> Any:
        return MagicMock(data=mock_thread_messages)

    async def mock_retrieve_assistant(*args, **kwargs) -> Any:
        asst = AsyncMock(spec=Assistant)
        asst.name = "test-assistant"
        return asst

    client = AsyncMock(spec=AsyncOpenAI)
    client.beta = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.assistants.create = AsyncMock(return_value=assistant_definition)
    client.beta.assistants.retrieve = AsyncMock(side_effect=mock_retrieve_assistant)
    client.beta.threads = MagicMock()
    client.beta.threads.create = AsyncMock(return_value=mock_thread)
    client.beta.threads.messages = MagicMock()
    client.beta.threads.messages.list = AsyncMock(side_effect=mock_list_messages)

    return client


@pytest.fixture
def assistant_definition() -> AsyncMock:
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"

    return definition
