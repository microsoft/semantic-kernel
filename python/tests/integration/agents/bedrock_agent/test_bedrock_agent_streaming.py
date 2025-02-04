# Copyright (c) Microsoft. All rights reserved.

import pytest
from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def bedrock_agent():
    return BedrockAgent(
        name="test_agent",
        agent_resource_role_arn="arn:aws:iam::123456789012:role/test-role",
        foundation_model="test_model",
    )


@pytest.mark.asyncio
async def test_streaming_invoke_bedrock_agent(bedrock_agent):
    session_id = "test_session_id"
    input_text = "Hello"
    async for message in bedrock_agent.invoke_stream(session_id, input_text):
        assert isinstance(message, StreamingChatMessageContent)
        assert message.role == AuthorRole.ASSISTANT
        assert message.content is not None


@pytest.mark.asyncio
async def test_handle_function_calls_bedrock_agent(bedrock_agent):
    event = {
        "returnControl": {
            "invocationId": "test_invocation_id",
            "invocationInputs": [],
        }
    }
    kernel = Kernel()
    arguments = KernelArguments()
    result = await bedrock_agent._handle_return_control_event(event, kernel, arguments)
    assert result["invocationId"] == "test_invocation_id"
    assert result["returnControlInvocationResults"] == []


@pytest.mark.asyncio
async def test_handle_file_events_bedrock_agent(bedrock_agent):
    event = {
        "files": {
            "files": [
                {
                    "name": "test_file.txt",
                    "type": "text/plain",
                    "bytes": b"Hello, world!",
                }
            ]
        }
    }
    result = bedrock_agent._handle_files_event(event)
    assert len(result) == 1
    assert result[0].metadata["name"] == "test_file.txt"
    assert result[0].data == b"Hello, world!"
