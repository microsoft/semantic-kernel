# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Annotated

import pytest
from azure.ai.projects.models import CodeInterpreterTool, FileSearchTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.functions import kernel_function
from tests.integration.agents.agent_test_base import AgentTestBase


class WeatherPlugin:
    """Mock weather plugin."""

    @kernel_function(description="Get real-time weather information.")
    def current_weather(self, location: Annotated[str, "The location to get the weather"]) -> str:
        """Returns the current weather."""
        return f"The weather in {location} is sunny."


class TestAzureAIAgentIntegration:
    @pytest.fixture
    async def azureai_agent(self, request):
        ai_agent_settings = AzureAIAgentSettings()
        async with (
            DefaultAzureCredential() as creds,
            AzureAIAgent.create_client(credential=creds) as client,
        ):
            tools, tool_resources, plugins = [], {}, []

            params = getattr(request, "param", {})
            if params.get("enable_code_interpreter"):
                ci_tool = CodeInterpreterTool()
                tools.extend(ci_tool.definitions)
                tool_resources.update(ci_tool.resources)

            if params.get("enable_file_search"):
                pdf_file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "resources",
                    "employees.pdf",
                )
                file = await client.agents.upload_file_and_poll(file_path=pdf_file_path, purpose="assistants")
                vector_store = await client.agents.create_vector_store_and_poll(
                    file_ids=[file.id], name="my_vectorstore"
                )
                fs_tool = FileSearchTool(vector_store_ids=[vector_store.id])
                tools.extend(fs_tool.definitions)
                tool_resources.update(fs_tool.resources)

            if params.get("enable_kernel_function"):
                plugins.append(WeatherPlugin())

            agent_definition = await client.agents.create_agent(
                model=ai_agent_settings.model_deployment_name,
                tools=tools,
                tool_resources=tool_resources,
                name="SKPythonIntegrationTestAgent",
                instructions="You are a helpful assistant that help users with their questions.",
            )

            azureai_agent = AzureAIAgent(
                client=client,
                definition=agent_definition,
                plugins=plugins,
            )

            yield azureai_agent  # yield agent for test method to use

            # cleanup
            await azureai_agent.client.agents.delete_agent(azureai_agent.id)

    async def test_get_response(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test get response of the agent."""
        response = await agent_test_base.get_response_with_retry(azureai_agent, messages="Hello")
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None
        assert "thread_id" in response.message.metadata
        assert "run_id" in response.message.metadata

    async def test_get_response_with_thread(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test get response of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            response = await agent_test_base.get_response_with_retry(
                azureai_agent, messages=user_message, thread=thread
            )
            thread = response.thread
            assert thread is not None
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

        await thread.delete() if thread else None

    async def test_invoke(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent."""
        responses = await agent_test_base.get_invoke_with_retry(azureai_agent, messages="Hello")
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    async def test_invoke_with_thread(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_with_retry(azureai_agent, messages=user_message, thread=thread)
            assert len(responses) > 0
            for response in responses:
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, ChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None

        await thread.delete() if thread else None

    async def test_invoke_stream(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test invoke stream of the agent."""
        responses = await agent_test_base.get_invoke_stream_with_retry(azureai_agent, messages="Hello")
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("azureai_agent", [{"enable_code_interpreter": True}], indirect=True)
    async def test_invoke_stream_with_thread(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test invoke stream of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_stream_with_retry(
                azureai_agent, messages=user_message, thread=thread
            )
            assert len(responses) > 0
            for response in responses:
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, StreamingChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None

        await thread.delete() if thread else None

    @pytest.mark.parametrize("azureai_agent", [{"enable_code_interpreter": True}], indirect=True)
    async def test_code_interpreter_get_response(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2
"""
        response = await agent_test_base.get_response_with_retry(azureai_agent, messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    @pytest.mark.parametrize("azureai_agent", [{"enable_code_interpreter": True}], indirect=True)
    async def test_code_interpreter_invoke(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2
"""
        responses = await agent_test_base.get_invoke_with_retry(azureai_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("azureai_agent", [{"enable_code_interpreter": True}], indirect=True)
    async def test_code_interpreter_invoke_stream(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter streaming."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2
"""
        responses = await agent_test_base.get_invoke_stream_with_retry(azureai_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("azureai_agent", [{"enable_file_search": True}], indirect=True)
    async def test_file_search_get_response(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        response = await agent_test_base.get_response_with_retry(azureai_agent, messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize("azureai_agent", [{"enable_file_search": True}], indirect=True)
    async def test_file_search_invoke(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_with_retry(azureai_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize("azureai_agent", [{"enable_file_search": True}], indirect=True)
    async def test_file_search_invoke_stream(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test code interpreter streaming."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_stream_with_retry(azureai_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize("azureai_agent", [{"enable_kernel_function": True}], indirect=True)
    async def test_function_calling_get_response(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test function calling."""
        response = await agent_test_base.get_response_with_retry(
            azureai_agent,
            messages="What is the weather in Seattle?",
        )
        assert isinstance(response.message, ChatMessageContent)
        assert all(isinstance(item, TextContent) for item in response.items)
        assert response.message.role == AuthorRole.ASSISTANT
        assert "sunny" in response.message.content

    @pytest.mark.parametrize("azureai_agent", [{"enable_kernel_function": True}], indirect=True)
    async def test_function_calling_invoke(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test function calling."""
        responses = await agent_test_base.get_invoke_with_retry(
            azureai_agent,
            messages="What is the weather in Seattle?",
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert all(isinstance(item, TextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            assert "sunny" in response.message.content

    @pytest.mark.parametrize("azureai_agent", [{"enable_kernel_function": True}], indirect=True)
    async def test_function_calling_stream(self, azureai_agent: AzureAIAgent, agent_test_base: AgentTestBase):
        """Test function calling streaming."""
        full_message: str = ""
        responses = await agent_test_base.get_invoke_stream_with_retry(
            azureai_agent, messages="What is the weather in Seattle?"
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert all(isinstance(item, StreamingTextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            full_message += response.message.content
        assert "sunny" in full_message
