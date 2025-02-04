# Copyright (c) Microsoft. All rights reserved.

import uuid

import pytest

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class TestBedrockAgentIntegration:
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self, request):
        """Setup and teardown for the test.

        This is run for each test function, i.e. each test function will have its own instance of the agent.
        """
        kwargs = {}
        if hasattr(request, "param"):
            if "enable_code_interpreter" in request.param:
                kwargs["enable_code_interpreter"] = request.param.get("enable_code_interpreter")
            if "enable_kernel_function" in request.param:
                kwargs["enable_kernel_function"] = request.param.get("enable_kernel_function")
            if "kernel" in request.param:
                kwargs["kernel"] = request.getfixturevalue(request.param.get("kernel"))

        try:
            self.bedrock_agent = await BedrockAgent.create(
                name=f"semantic-kernel-integration-test-agent-{uuid.uuid4()}",
                instructions="You are a helpful assistant that help users with their questions.",
                **kwargs,
            )
        except Exception as e:
            pytest.fail("Failed to create agent")
            raise e
        # Yield control to the test
        yield
        # Clean up
        try:
            await self.bedrock_agent.delete_agent()
        except Exception as e:
            pytest.fail(f"Failed to delete agent: {e}")
            raise e

    @pytest.mark.asyncio
    async def test_update(self):
        """Test updating the agent."""
        await self.bedrock_agent.update_agent(agentName="updated_agent")
        assert self.bedrock_agent.agent_model.agent_name == "updated_agent"

    @pytest.mark.asyncio
    async def test_invoke(self):
        """Test invoke of the agent."""
        async for message in self.bedrock_agent.invoke(BedrockAgent.create_session_id(), "Hello"):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert message.content is not None

    @pytest.mark.asyncio
    async def test_invoke_stream(self):
        """Test invoke stream of the agent."""
        async for message in self.bedrock_agent.invoke_stream(BedrockAgent.create_session_id(), "Hello"):
            assert isinstance(message, StreamingChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert message.content is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setup_and_teardown", [{"enable_code_interpreter": True}], indirect=True)
    async def test_code_interpreter(self):
        """Test code interpreter."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8 
Lion    3
Monkey  6
Dolphin  2
"""
        async for message in self.bedrock_agent.invoke(BedrockAgent.create_session_id(), input_text):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert any(item for item in message.items if isinstance(item, BinaryContent))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setup_and_teardown", [{"enable_code_interpreter": True}], indirect=True)
    async def test_code_interpreter_stream(self):
        """Test code interpreter streaming."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8 
Lion    3
Monkey  6
Dolphin  2
"""
        binary_item: BinaryContent | None = None
        async for message in self.bedrock_agent.invoke_stream(BedrockAgent.create_session_id(), input_text):
            assert isinstance(message, StreamingChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            binary_item = next((item for item in message.items if isinstance(item, BinaryContent)), None)
        assert binary_item

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup_and_teardown",
        [
            {
                "enable_kernel_function": True,
                "kernel": "kernel_with_dummy_function",
            },
        ],
        indirect=True,
    )
    async def test_function_calling(self):
        """Test function calling."""
        async for message in self.bedrock_agent.invoke(
            BedrockAgent.create_session_id(),
            "What is the weather in Seattle?",
        ):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert "sunny" in message.content

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "setup_and_teardown",
        [
            {
                "enable_kernel_function": True,
                "kernel": "kernel_with_dummy_function",
            },
        ],
        indirect=True,
    )
    async def test_function_calling_stream(self):
        """Test function calling streaming."""
        full_message: str = ""
        async for message in self.bedrock_agent.invoke_stream(
            BedrockAgent.create_session_id(),
            "What is the weather in Seattle?",
        ):
            assert isinstance(message, StreamingChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            full_message += message.content
        assert "sunny" in full_message
