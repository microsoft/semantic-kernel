# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

import pytest

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.functions import kernel_function


class WeatherPlugin:
    """A sample Mock weather plugin."""

    @kernel_function(description="Get real-time weather information.")
    def current_weather(self, location: Annotated[str, "The location to get the weather"]) -> str:
        """Returns the current weather."""
        return f"The weather in {location} is sunny."


class TestChatCompletionAgentIntegration:
    @pytest.fixture(params=["azure", "openai"])
    async def chat_completion_agent(self, request):
        raw_param = request.param

        if isinstance(raw_param, str):
            agent_service, params = raw_param, {}
        elif isinstance(raw_param, tuple) and len(raw_param) == 2:
            agent_service, params = raw_param
        else:
            raise ValueError(f"Unsupported param format: {raw_param}")

        plugins = []

        service = AzureChatCompletion() if agent_service == "azure" else OpenAIChatCompletion()

        if params.get("enable_kernel_function"):
            plugins.append(WeatherPlugin())

        agent = ChatCompletionAgent(
            service=service,
            name="SKPythonIntegrationTestChatCompletionAgent",
            instructions="You are a helpful assistant that help users with their questions.",
            plugins=plugins,
        )

        yield agent  # yield agent for test method to use

    # region Simple 'Hello' messages tests

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response(self, chat_completion_agent: ChatCompletionAgent):
        """Test get response of the agent."""
        response = await chat_completion_agent.get_response(messages="Hello")
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response_with_thread(self, chat_completion_agent: ChatCompletionAgent):
        """Test get response of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            response = await chat_completion_agent.get_response(messages=user_message, thread=thread)
            thread = response.thread
            assert thread is not None
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None
        await thread.delete() if thread else None

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke(self, chat_completion_agent: ChatCompletionAgent):
        """Test invoke of the agent."""
        async for response in chat_completion_agent.invoke(messages="Hello"):
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_with_thread(self, chat_completion_agent: ChatCompletionAgent):
        """Test invoke of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            async for response in chat_completion_agent.invoke(messages=user_message, thread=thread):
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, ChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None
        await thread.delete() if thread else None

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream(self, chat_completion_agent: ChatCompletionAgent):
        """Test invoke stream of the agent."""
        async for response in chat_completion_agent.invoke_stream(messages="Hello"):
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("chat_completion_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream_with_thread(self, chat_completion_agent: ChatCompletionAgent):
        """Test invoke stream of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            async for response in chat_completion_agent.invoke_stream(messages=user_message, thread=thread):
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, StreamingChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None
        await thread.delete() if thread else None

    # endregion

    # region Function calling tests

    @pytest.mark.parametrize(
        "chat_completion_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["chat_completion_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_get_response(self, chat_completion_agent: ChatCompletionAgent):
        """Test function calling."""
        response = await chat_completion_agent.get_response(
            messages="What is the weather in Seattle?",
        )
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "chat_completion_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["chat_completion_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_invoke(self, chat_completion_agent: ChatCompletionAgent):
        """Test function calling."""
        async for response in chat_completion_agent.invoke(
            messages="What is the weather in Seattle?",
        ):
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "chat_completion_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["chat_completion_agent"],
        ids=["azure-function-calling", "openai-function-calling"],
    )
    async def test_function_calling_stream(self, chat_completion_agent: ChatCompletionAgent):
        """Test function calling streaming."""
        full_message: str = ""
        async for response in chat_completion_agent.invoke_stream(
            messages="What is the weather in Seattle?",
        ):
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            full_message += response.message.content
        assert "sunny" in full_message

    # endregion
