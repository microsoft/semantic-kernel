# Copyright (c) Microsoft. All rights reserved.
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant, ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from openai.types.beta.threads.annotation import FileCitationAnnotation, FilePathAnnotation
from openai.types.beta.threads.file_citation_annotation import FileCitation
from openai.types.beta.threads.file_path_annotation import FilePath
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock

from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


@pytest.fixture
def mock_thread_messages():
    class MockMessage:
        def __init__(self, role, content, assistant_id=None):
            self.role = role
            self.content = content
            self.assistant_id = assistant_id

    return [
        MockMessage(
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
                                file_citation=FileCitation(file_id="test_file_id", quote="test quote"),
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
            role="assistant",
            content=[
                ImageFileContentBlock(type="image_file", image_file=ImageFile(file_id="test_file_id", detail="auto"))
            ],
            assistant_id="assistant_1",
        ),
    ]


@pytest.fixture
def mock_assistant():
    return Assistant(
        created_at=123456789,
        object="assistant",
        metadata={
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        model="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        temperature=0.7,
        top_p=0.9,
        response_format={"type": "json_object"},
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
    )


@pytest.mark.asyncio
async def test_receive_messages():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    client.beta = AsyncMock()
    thread_id = "test_thread"
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)
    history = [
        MagicMock(spec=ChatMessageContent, role=AuthorRole.USER, items=[TextContent(text="test")]) for _ in range(3)
    ]

    with patch("semantic_kernel.agents.open_ai.assistant_content_generation.create_chat_message"):
        await channel.receive(history)


@pytest.mark.asyncio
async def test_invoke_agent():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock(spec=OpenAIAssistantBase)
    agent._is_deleted = False
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    async def mock_invoke_internal(*args, **kwargs):
        for _ in range(3):
            yield True, MagicMock(spec=ChatMessageContent)

    agent._invoke_internal.side_effect = mock_invoke_internal

    results = []
    async for is_visible, message in channel.invoke(agent):
        results.append((is_visible, message))

    assert len(results) == 3
    for is_visible, message in results:
        assert is_visible is True
        assert isinstance(message, ChatMessageContent)


@pytest.mark.asyncio
async def test_invoke_agent_deleted():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock(spec=OpenAIAssistantBase)
    agent._is_deleted = True
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    with pytest.raises(AgentChatException, match="Agent is deleted"):
        async for _ in channel.invoke(agent):
            pass


@pytest.mark.asyncio
async def test_invoke_agent_wrong_type():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock()
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    with pytest.raises(AgentChatException, match="Agent is not of the expected type"):
        async for _ in channel.invoke(agent):
            pass


@pytest.mark.asyncio
async def test_get_history(mock_thread_messages, mock_assistant, openai_unit_test_env):
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    async def mock_list_messages(*args, **kwargs) -> Any:
        return MagicMock(data=mock_thread_messages)

    async def mock_retrieve_assistant(*args, **kwargs) -> Any:
        return mock_assistant

    mock_client = MagicMock(spec=AsyncOpenAI)
    mock_client.beta = MagicMock()
    mock_client.beta.threads = MagicMock()
    mock_client.beta.threads.messages = MagicMock()
    mock_client.beta.threads.messages.list = AsyncMock(side_effect=mock_list_messages)
    mock_client.beta.assistants = MagicMock()
    mock_client.beta.assistants.retrieve = AsyncMock(side_effect=mock_retrieve_assistant)

    thread_id = "test_thread"
    channel = OpenAIAssistantChannel(client=mock_client, thread_id=thread_id)

    results = []
    async for content in channel.get_history():
        results.append(content)

    assert len(results) == 2
    mock_client.beta.threads.messages.list.assert_awaited_once_with(thread_id=thread_id, limit=100, order="desc")
