# Copyright (c) Microsoft. All rights reserved.

from azure.ai.agents.models import MessageAttachment, MessageRole

from semantic_kernel.agents.azure_ai.azure_ai_agent_utils import AzureAIAgentUtils
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def test_azure_ai_agent_utils_get_thread_messages_none():
    msgs = AzureAIAgentUtils.get_thread_messages([])
    assert msgs is None


def test_azure_ai_agent_utils_get_thread_messages():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="Hello!")
    msg1.items.append(FileReferenceContent(file_id="file123"))
    results = AzureAIAgentUtils.get_thread_messages([msg1])
    assert len(results) == 1
    assert results[0].content == "Hello!"
    assert results[0].role == MessageRole.USER
    assert len(results[0].attachments) == 1
    assert isinstance(results[0].attachments[0], MessageAttachment)


def test_azure_ai_agent_utils_get_attachments_empty():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="No file items")
    atts = AzureAIAgentUtils.get_attachments(msg1)
    assert atts == []


def test_azure_ai_agent_utils_get_attachments_file():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="One file item")
    msg1.items.append(FileReferenceContent(file_id="file123"))
    atts = AzureAIAgentUtils.get_attachments(msg1)
    assert len(atts) == 1
    assert atts[0].file_id == "file123"


def test_azure_ai_agent_utils_get_metadata():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="has meta", metadata={"k": 123})
    meta = AzureAIAgentUtils.get_metadata(msg1)
    assert meta["k"] == "123"


def test_azure_ai_agent_utils_get_tool_definition():
    gen = AzureAIAgentUtils._get_tool_definition(["file_search", "code_interpreter", "non_existent"])
    # file_search & code_interpreter exist, non_existent yields nothing
    tools_list = list(gen)
    assert len(tools_list) == 2
