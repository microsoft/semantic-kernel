# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.agents.history.chat_history_reducer_extensions import SUMMARY_METADATA_KEY
from semantic_kernel.agents.history.chat_history_summarization_reducer import (
    ChatHistorySummarizationReducer,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatHistoryReducerException


@pytest.fixture
def mock_service():
    """Returns a mock ChatCompletionClientBase with required methods."""
    service = MagicMock(spec=ChatCompletionClientBase)
    # Mock the get_prompt_execution_settings_class to return a placeholder
    service.get_prompt_execution_settings_class.return_value = MagicMock(return_value=MagicMock(service_id="foo"))
    # Mock the async call get_chat_message_contents
    service.get_chat_message_contents = AsyncMock()
    return service


@pytest.fixture
def chat_messages():
    """Returns a list of ChatMessageContent objects with default roles."""
    msgs = []

    # Existing summary
    summary_msg = ChatMessageContent(role=AuthorRole.SYSTEM, content="Prior summary.")
    summary_msg.metadata[SUMMARY_METADATA_KEY] = True
    msgs.append(summary_msg)

    # Normal user messages
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Hello!"))
    msgs.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi there."))
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="What can you do?"))
    msgs.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="I can help with tasks."))
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Ok, let's do something."))
    return msgs


def test_summarization_reducer_init(mock_service):
    reducer = ChatHistorySummarizationReducer(
        service=mock_service,
        target_count=10,
        service_id="my_service",
        threshold_count=5,
        summarization_instructions="Custom instructions",
        use_single_summary=False,
        fail_on_error=False,
    )

    assert reducer.service == mock_service
    assert reducer.target_count == 10
    assert reducer.service_id == "my_service"
    assert reducer.threshold_count == 5
    assert reducer.summarization_instructions == "Custom instructions"
    assert reducer.use_single_summary is False
    assert reducer.fail_on_error is False


def test_summarization_reducer_defaults(mock_service):
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=5)
    # Check default property values
    assert reducer.threshold_count == 0
    assert reducer.summarization_instructions in reducer.summarization_instructions
    assert reducer.use_single_summary is True
    assert reducer.fail_on_error is True
    assert reducer.service_id == DEFAULT_SERVICE_NAME


def test_summarization_reducer_eq_and_hash(mock_service):
    r1 = ChatHistorySummarizationReducer(service=mock_service, target_count=5, threshold_count=2)
    r2 = ChatHistorySummarizationReducer(service=mock_service, target_count=5, threshold_count=2)
    r3 = ChatHistorySummarizationReducer(service=mock_service, target_count=6, threshold_count=2)
    assert r1 == r2
    assert r1 != r3

    # Test hash
    assert hash(r1) == hash(r2)
    assert hash(r1) != hash(r3)


async def test_summarization_reducer_reduce_no_need(chat_messages, mock_service):
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=10, threshold_count=0)

    # If len(history) <= target_count => None
    result = await reducer.reduce(chat_messages)
    assert result is None
    mock_service.get_chat_message_contents.assert_not_awaited()


async def test_summarization_reducer_reduce_needed(chat_messages, mock_service):
    # Force a smaller target
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=3, threshold_count=1)

    # Mock that the service will return a single summary message
    summary_content = ChatMessageContent(role=AuthorRole.ASSISTANT, content="This is a summary.")
    mock_service.get_chat_message_contents.return_value = [summary_content]

    result = await reducer.reduce(chat_messages)
    # We expect a shortened list with the new summary inserted
    assert result is not None
    # Check that summary metadata is set
    assert SUMMARY_METADATA_KEY in result[0].metadata or SUMMARY_METADATA_KEY in result[1].metadata
    # We do call the service
    mock_service.get_chat_message_contents.assert_awaited_once()


async def test_summarization_reducer_reduce_no_messages_to_summarize(mock_service):
    # If we do use_single_summary=False, the older_range_start is insertion_point
    # In that scenario, if insertion_point == older_range_end => no messages to summarize => return None
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=1, use_single_summary=False)

    # Provide just one message flagged as summary => insertion_point=0, so older_range_start=0, older_range_end=0
    only_summary = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="Only summary.", metadata={SUMMARY_METADATA_KEY: True})
    ]
    result = await reducer.reduce(only_summary)
    assert result is None
    mock_service.get_chat_message_contents.assert_not_awaited()


async def test_summarization_reducer_reduce_summarizer_returns_none(chat_messages, mock_service):
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=3)
    # If the summarizer yields no messages, we return None
    mock_service.get_chat_message_contents.return_value = []
    result = await reducer.reduce(chat_messages)
    assert result is None


async def test_summarization_reducer_reduce_summarization_fails(chat_messages, mock_service):
    # If summarization fails, we raise if fail_on_error=True
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=3, fail_on_error=True)
    mock_service.get_chat_message_contents.side_effect = Exception("Summarizer error")
    with pytest.raises(AgentChatHistoryReducerException):
        await reducer.reduce(chat_messages)


async def test_summarization_reducer_reduce_summarization_fails_no_raise(chat_messages, mock_service):
    # If summarization fails, but fail_on_error=False, we just log and return None
    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=3, fail_on_error=False)
    mock_service.get_chat_message_contents.side_effect = Exception("Summarizer error")
    result = await reducer.reduce(chat_messages)
    assert result is None


async def test_summarization_reducer_private_summarize(mock_service):
    """Directly test the _summarize method for coverage, though it's indirectly tested via reduce()."""
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.utils.author_role import AuthorRole

    reducer = ChatHistorySummarizationReducer(service=mock_service, target_count=5)
    chat_messages = [
        ChatMessageContent(role=AuthorRole.USER, content="Message1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Message2"),
    ]
    summary_content = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Mock Summary")
    mock_service.get_chat_message_contents.return_value = [summary_content]

    # Call _summarize
    actual_summary = await reducer._summarize(chat_messages)
    assert actual_summary.content == "Mock Summary"
    mock_service.get_chat_message_contents.assert_awaited_once()
