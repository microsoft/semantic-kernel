# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Annotated

import pytest

from semantic_kernel.agents import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.functions import kernel_function
from tests.integration.agents.agent_test_base import AgentTestBase


class WeatherPlugin:
    """A sample Mock weather plugin."""

    @kernel_function(description="Get real-time weather information.")
    def current_weather(self, location: Annotated[str, "The location to get the weather"]) -> str:
        """Returns the current weather."""
        return f"The weather in {location} is sunny."


class TestOpenAIAssistantAgentIntegration:
    @pytest.fixture(params=["azure", "openai"])
    async def assistant_agent(self, request):
        raw_param = request.param

        if isinstance(raw_param, str):
            agent_type, params = raw_param, {}
        elif isinstance(raw_param, tuple) and len(raw_param) == 2:
            agent_type, params = raw_param
        else:
            raise ValueError(f"Unsupported param format: {raw_param}")

        tools, tool_resources, plugins = [], {}, []

        if agent_type == "azure":
            client, model = AzureAssistantAgent.setup_resources()
            AgentClass = AzureAssistantAgent
        else:  # agent_type == "openai"
            client, model = OpenAIAssistantAgent.setup_resources()
            AgentClass = OpenAIAssistantAgent

        if params.get("enable_code_interpreter"):
            code_interpreter_tool, code_interpreter_tool_resources = (
                AzureAssistantAgent.configure_code_interpreter_tool()
                if agent_type == "azure"
                else OpenAIAssistantAgent.configure_code_interpreter_tool()
            )
            tools.extend(code_interpreter_tool)
            tool_resources.update(code_interpreter_tool_resources)

        if params.get("enable_file_search"):
            pdf_file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
            )
            with open(pdf_file_path, "rb") as file:
                file = await client.files.create(file=file, purpose="assistants")
            vector_store = await client.vector_stores.create(
                name="assistant_file_search_int_tests",
                file_ids=[file.id],
            )
            file_search_tool, file_search_tool_resources = (
                AzureAssistantAgent.configure_file_search_tool(vector_store.id)
                if agent_type == "azure"
                else OpenAIAssistantAgent.configure_file_search_tool(vector_store.id)
            )
            tools.extend(file_search_tool)
            tool_resources.update(file_search_tool_resources)

        if params.get("enable_kernel_function"):
            plugins.append(WeatherPlugin())

        definition = await client.beta.assistants.create(
            model=model,
            tools=tools,
            tool_resources=tool_resources,
            name="SKPythonIntegrationTestAssistantAgent",
            instructions="You are a helpful assistant that help users with their questions.",
        )

        agent = AgentClass(
            client=client,
            definition=definition,
            plugins=plugins,
        )

        yield agent  # yield agent for test method to use

        # cleanup
        await client.beta.assistants.delete(agent.id)

    # region Simple 'Hello' messages tests

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test get response of the agent."""
        response = await agent_test_base.get_response_with_retry(assistant_agent, messages="Hello")
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response_with_thread(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test get response of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            response = await agent_test_base.get_response_with_retry(
                assistant_agent, messages=user_message, thread=thread
            )
            thread = response.thread
            assert thread is not None
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

        await thread.delete() if thread else None

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent."""
        responses = await agent_test_base.get_invoke_with_retry(assistant_agent, messages="Hello")
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_with_thread(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_with_retry(
                assistant_agent, messages=user_message, thread=thread
            )
            assert len(responses) > 0
            for response in responses:
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, ChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None

        await thread.delete() if thread else None

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test invoke stream of the agent."""
        responses = await agent_test_base.get_invoke_stream_with_retry(assistant_agent, messages="Hello")
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("assistant_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream_with_thread(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test invoke stream of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_stream_with_retry(
                assistant_agent, messages=user_message, thread=thread
            )
            assert len(responses) > 0
            for response in responses:
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, StreamingChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None

        await thread.delete() if thread else None

    # endregion

    # region Code interpreter tests

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_code_interpreter": True}),
            ("openai", {"enable_code_interpreter": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-code-interpreter", "openai-code-interpreter"],
    )
    async def test_code_interpreter_get_response(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8 
Lion    3
Monkey  6
Dolphin  2
"""
        response = await agent_test_base.get_response_with_retry(assistant_agent, messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_code_interpreter": True}),
            ("openai", {"enable_code_interpreter": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-code-interpreter", "openai-code-interpreter"],
    )
    async def test_code_interpreter_invoke(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8 
Lion    3
Monkey  6
Dolphin  2
"""
        responses = await agent_test_base.get_invoke_with_retry(assistant_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_code_interpreter": True}),
            ("openai", {"enable_code_interpreter": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-code-interpreter", "openai-code-interpreter"],
    )
    async def test_code_interpreter_invoke_stream(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter streaming."""
        input_text = """
Create a bar chart for the following data:
Panda   5
Tiger   8 
Lion    3
Monkey  6
Dolphin  2
"""
        responses = await agent_test_base.get_invoke_stream_with_retry(assistant_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    # endregion

    # region File search tests

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-file-search", "openai-file-search"],
    )
    async def test_file_search_get_response(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        response = await agent_test_base.get_response_with_retry(assistant_agent, messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-file-search", "openai-file-search"],
    )
    async def test_file_search_invoke(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_with_retry(assistant_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-file-search", "openai-file-search"],
    )
    async def test_file_search_invoke_stream(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter streaming."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_stream_with_retry(assistant_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    # endregion

    # region Function calling tests

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_get_response(
        self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase
    ):
        """Test function calling."""
        response = await agent_test_base.get_response_with_retry(
            assistant_agent,
            messages="What is the weather in Seattle?",
        )
        assert isinstance(response.message, ChatMessageContent)
        assert all(isinstance(item, TextContent) for item in response.items)
        assert response.message.role == AuthorRole.ASSISTANT
        assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_invoke(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test function calling."""
        responses = await agent_test_base.get_invoke_with_retry(
            assistant_agent,
            messages="What is the weather in Seattle?",
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert all(isinstance(item, TextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "assistant_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["assistant_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_stream(self, assistant_agent: OpenAIAssistantAgent, agent_test_base: AgentTestBase):
        """Test function calling streaming."""
        full_message: str = ""
        responses = await agent_test_base.get_invoke_stream_with_retry(
            assistant_agent, messages="What is the weather in Seattle?"
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert all(isinstance(item, StreamingTextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            full_message += response.message.content
        assert "sunny" in full_message

    # endregion
