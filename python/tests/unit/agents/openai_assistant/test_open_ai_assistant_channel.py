# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant, ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from openai.types.beta.threads.file_citation_annotation import FileCitation, FileCitationAnnotation
from openai.types.beta.threads.file_path_annotation import FilePath, FilePathAnnotation
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel


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
            "__run_options": json.dumps({
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            })
        },
        model="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],  # type: ignore
        temperature=0.7,
        top_p=0.9,
        response_format={"type": "json_object"},  # type: ignore
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
    )


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
        await channel.receive(history)  # type: ignore


async def test_invoke_agent():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
        arguments=KernelArguments(test="test"),
        kernel=AsyncMock(spec=Kernel),
    )

    channel = OpenAIAssistantChannel(client=client, thread_id="test_thread_id")

    async def mock_invoke_internal(*args, **kwargs):
        for _ in range(3):
            yield True, MagicMock(spec=ChatMessageContent)

    results = []
    with patch(
        "semantic_kernel.agents.channels.open_ai_assistant_channel.AssistantThreadActions.invoke",
        side_effect=mock_invoke_internal,
    ):
        async for is_visible, message in channel.invoke(agent):
            results.append((is_visible, message))

    assert len(results) == 3
    for is_visible, message in results:
        assert is_visible is True
        assert isinstance(message, ChatMessageContent)


async def test_invoke_agent_invalid_instance_throws():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock(spec=ChatCompletionAgent)
    agent._is_deleted = False
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    with pytest.raises(AgentChatException, match=f"Agent is not of the expected type {type(OpenAIAssistantAgent)}."):
        async for _, _ in channel.invoke(agent):
            pass


async def test_invoke_streaming_agent():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
        arguments=KernelArguments(test="test"),
        kernel=AsyncMock(spec=Kernel),
    )

    channel = OpenAIAssistantChannel(client=client, thread_id="test_thread_id")

    results = []

    async def mock_invoke_internal(*args, **kwargs):
        for _ in range(3):
            msg = MagicMock(spec=ChatMessageContent)
            yield msg
            results.append(msg)

    with patch(
        "semantic_kernel.agents.channels.open_ai_assistant_channel.AssistantThreadActions.invoke_stream",
        side_effect=mock_invoke_internal,
    ):
        async for message in channel.invoke_stream(agent, results):
            assert message is not None

    assert len(results) == 3
    for message in results:
        assert isinstance(message, ChatMessageContent)


async def test_invoke_streaming_agent_invalid_instance_throws():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock(spec=ChatCompletionAgent)
    agent._is_deleted = False
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    with pytest.raises(AgentChatException, match=f"Agent is not of the expected type {type(OpenAIAssistantAgent)}."):
        async for _ in channel.invoke_stream(agent, []):
            pass


async def test_invoke_agent_wrong_type():
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = MagicMock(spec=AsyncOpenAI)
    thread_id = "test_thread"
    agent = MagicMock()
    channel = OpenAIAssistantChannel(client=client, thread_id=thread_id)

    with pytest.raises(AgentChatException, match="Agent is not of the expected type"):
        async for _ in channel.invoke(agent):
            pass


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


async def test_reset_channel(mock_thread_messages, mock_assistant, openai_unit_test_env):
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
    mock_client.beta.threads.delete = AsyncMock()

    thread_id = "test_thread"
    channel = OpenAIAssistantChannel(client=mock_client, thread_id=thread_id)

    results = []
    async for content in channel.get_history():
        results.append(content)

    assert len(results) == 2
    mock_client.beta.threads.messages.list.assert_awaited_once_with(thread_id=thread_id, limit=100, order="desc")

    await channel.reset()

    assert channel.thread_id is not None


async def test_reset_channel_error_throws_exception(mock_thread_messages, mock_assistant, openai_unit_test_env):
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
    mock_client.beta.threads.delete = AsyncMock(side_effect=Exception("Test error"))

    thread_id = "test_thread"
    channel = OpenAIAssistantChannel(client=mock_client, thread_id=thread_id)

    results = []
    async for content in channel.get_history():
        results.append(content)

    assert len(results) == 2
    mock_client.beta.threads.messages.list.assert_awaited_once_with(thread_id=thread_id, limit=100, order="desc")

    with pytest.raises(Exception, match="Test error"):
        await channel.reset()


async def test_channel_receive_fcc_skipped(openai_unit_test_env):
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[FunctionCallContent(function_name="test_function")])

    client = MagicMock(spec=AsyncOpenAI)

    channel = OpenAIAssistantChannel(client=client, thread_id="test_thread")

    await channel.receive([message])
