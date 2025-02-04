# Copyright (c) Microsoft. All rights reserved.

import pytest
from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


class TestBedrockAgentIntegration:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.bedrock_agent = BedrockAgent(
            name="test_agent",
            agent_resource_role_arn="arn:aws:iam::123456789012:role/test-role",
            foundation_model="test_model",
        )
        yield
        if self.bedrock_agent.agent_model.agent_id:
            self.bedrock_agent.delete_agent()

    @pytest.mark.asyncio
    async def test_create_bedrock_agent(self):
        await self.bedrock_agent.create_agent()
        assert self.bedrock_agent.agent_model.agent_id is not None

    @pytest.mark.asyncio
    async def test_update_bedrock_agent(self):
        self.bedrock_agent.agent_model.agent_id = "test_agent_id"
        await self.bedrock_agent.update_agent(agentName="updated_agent")
        assert self.bedrock_agent.agent_model.agent_name == "updated_agent"

    @pytest.mark.asyncio
    async def test_delete_bedrock_agent(self):
        self.bedrock_agent.agent_model.agent_id = "test_agent_id"
        await self.bedrock_agent.delete_agent()
        assert self.bedrock_agent.agent_model.agent_id is None

    @pytest.mark.asyncio
    async def test_invoke_bedrock_agent(self):
        session_id = "test_session_id"
        input_text = "Hello"
        async for message in self.bedrock_agent.invoke(session_id, input_text):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert message.content is not None

    @pytest.mark.asyncio
    async def test_streaming_invoke_bedrock_agent(self):
        session_id = "test_session_id"
        input_text = "Hello"
        async for message in self.bedrock_agent.invoke_stream(session_id, input_text):
            assert isinstance(message, StreamingChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert message.content is not None

    @pytest.mark.asyncio
    async def test_code_interpreter_file_generation(self):
        await self.bedrock_agent.create_agent(enable_code_interpreter=True)
        session_id = "test_session_id"
        input_text = "Generate a file with the content 'Hello, world!'"
        async for message in self.bedrock_agent.invoke(session_id, input_text):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert any(item.metadata["name"] == "generated_file.txt" for item in message.items)

    @pytest.mark.asyncio
    async def test_function_calling(self):
        kernel = Kernel()
        kernel.add_function("dummy_function", lambda: "dummy_result")
        await self.bedrock_agent.create_agent(enable_kernel_function=True)
        session_id = "test_session_id"
        input_text = "Call the dummy_function"
        async for message in self.bedrock_agent.invoke(session_id, input_text, kernel=kernel):
            assert isinstance(message, ChatMessageContent)
            assert message.role == AuthorRole.ASSISTANT
            assert "dummy_result" in message.content
