# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Annotated

import pytest
from pydantic import BaseModel

from semantic_kernel.agents import AzureResponsesAgent, OpenAIResponsesAgent
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


class Step(BaseModel):
    explanation: str
    output: str


class Reasoning(BaseModel):
    steps: list[Step]
    final_answer: str


class TestOpenAIResponsesAgentIntegration:
    @pytest.fixture(params=["azure", "openai"])
    async def responses_agent(self, request):
        raw_param = request.param

        if isinstance(raw_param, str):
            agent_type, params = raw_param, {}
        elif isinstance(raw_param, tuple) and len(raw_param) == 2:
            agent_type, params = raw_param
        else:
            raise ValueError(f"Unsupported param format: {raw_param}")

        tools, plugins, text = [], [], None

        if agent_type == "azure":
            client, model = AzureResponsesAgent.setup_resources()
            AgentClass = AzureResponsesAgent
        else:  # agent_type == "openai"
            client, model = OpenAIResponsesAgent.setup_resources()
            AgentClass = OpenAIResponsesAgent

        if params.get("enable_web_search"):
            web_search_tool = OpenAIResponsesAgent.configure_web_search_tool()
            tools.append(web_search_tool)

        if params.get("enable_structured_outputs"):
            text = OpenAIResponsesAgent.configure_response_format(Reasoning)

        if params.get("enable_file_search"):
            pdf_file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
            )
            with open(pdf_file_path, "rb") as file:
                file = await client.files.create(file=file, purpose="assistants")
            vector_store = await client.vector_stores.create(
                name="responses_file_search_int_tests",
                file_ids=[file.id],
            )
            file_search_tool = (
                AzureResponsesAgent.configure_file_search_tool(vector_store.id)
                if agent_type == "azure"
                else OpenAIResponsesAgent.configure_file_search_tool(vector_store.id)
            )
            tools.append(file_search_tool)

        if params.get("enable_kernel_function"):
            plugins.append(WeatherPlugin())

        agent = AgentClass(
            ai_model_id=model,
            client=client,
            name="SKPythonIntegrationTestResponsesAgent",
            instructions="You are a helpful agent that help users with their questions.",
            plugins=plugins,
            tools=tools,
            text=text,
        )

        yield agent  # yield agent for test method to use

    # region Simple 'Hello' messages tests

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test get response of the agent."""
        response = await agent_test_base.get_response_with_retry(responses_agent, messages="Hello")
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_get_response_with_thread(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test get response of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            response = await agent_test_base.get_response_with_retry(
                responses_agent, messages=user_message, thread=thread
            )
            thread = response.thread
            assert thread is not None
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

        await thread.delete() if thread else None

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent."""
        async for response in responses_agent.invoke(messages="Hello"):
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_with_thread(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test invoke of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_with_retry(
                responses_agent, messages=user_message, thread=thread
            )
            assert len(responses) > 0
            for response in responses:
                thread = response.thread
                assert thread is not None
                assert isinstance(response.message, ChatMessageContent)
                assert response.message.role == AuthorRole.ASSISTANT
                assert response.message.content is not None

        await thread.delete() if thread else None

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test invoke stream of the agent."""
        responses = await agent_test_base.get_invoke_stream_with_retry(responses_agent, messages="Hello")
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert response.message.content is not None

    @pytest.mark.parametrize("responses_agent", ["azure", "openai"], indirect=True, ids=["azure", "openai"])
    async def test_invoke_stream_with_thread(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test invoke stream of the agent with a thread."""
        thread = None
        user_messages = ["Hello, I am John Doe.", "What is my name?"]
        for user_message in user_messages:
            responses = await agent_test_base.get_invoke_stream_with_retry(
                responses_agent, messages=user_message, thread=thread
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

    # region Web Search tests

    @pytest.mark.parametrize(
        "responses_agent",
        [
            # Azure OpenAI Responses API doesn't yet support the web search tool
            ("openai", {"enable_web_search": True}),
        ],
        indirect=["responses_agent"],
        ids=["openai-web-search-get-response"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable when using the web search tool.")
    async def test_web_search_get_response(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = "Find articles about the latest AI trends."
        response = await responses_agent.get_response(messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content is not None

    # endregion

    # region File search tests

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-file-search-get-response", "openai-file-search-get-response"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable and is throwing 500s.")
    async def test_file_search_get_response(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        response = await agent_test_base.get_response_with_retry(responses_agent, messages=input_text)
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-file-search-invoke", "openai-file-search-invoke"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable and is throwing 500s.")
    async def test_file_search_invoke(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test code interpreter."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_with_retry(responses_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_file_search": True}),
            ("openai", {"enable_file_search": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-file-search-invoke-stream", "openai-file-search-invoke-stream"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable and is throwing 500s.")
    async def test_file_search_invoke_stream(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test code interpreter streaming."""
        input_text = "Who is the youngest employee?"
        responses = await agent_test_base.get_invoke_stream_with_retry(responses_agent, messages=input_text)
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT

    # endregion

    # region Function calling tests

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-function-calling-get-response", "openai-function-calling-get-response"],
    )
    async def test_function_calling_get_response(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test function calling."""
        response = await agent_test_base.get_response_with_retry(
            responses_agent,
            messages="What is the weather in Seattle?",
        )
        assert isinstance(response.message, ChatMessageContent)
        assert all(isinstance(item, TextContent) for item in response.items)
        assert response.message.role == AuthorRole.ASSISTANT
        assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-function-calling-invoke", "openai-function-calling-invoke"],
    )
    async def test_function_calling_invoke(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test function calling."""
        responses = await agent_test_base.get_invoke_with_retry(
            responses_agent,
            messages="What is the weather in Seattle?",
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert all(isinstance(item, TextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            assert "sunny" in response.message.content

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_kernel_function": True}),
            ("openai", {"enable_kernel_function": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-function-calling-invoke-stream", "openai-function-calling-invoke-stream"],
    )
    async def test_function_calling_stream(self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase):
        """Test function calling streaming."""
        full_message: str = ""
        responses = await agent_test_base.get_invoke_stream_with_retry(
            responses_agent, messages="What is the weather in Seattle?"
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert all(isinstance(item, StreamingTextContent) for item in response.items)
            assert response.message.role == AuthorRole.ASSISTANT
            full_message += response.message.content
        assert "sunny" in full_message

    # endregion

    # region Structured Outputs

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_structured_outputs": True}),
            ("openai", {"enable_structured_outputs": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-structured-outputs-get-response", "openai-structured-outputs-get-response"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable when configuring structured outputs.")
    async def test_structured_outputs_get_response(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test structured outputs get response."""
        response = await agent_test_base.get_response_with_retry(
            responses_agent,
            messages="how can I solve 8x + 7y = -23, and 4x=12?",
        )
        assert isinstance(response.message, ChatMessageContent)
        assert response.message.role == AuthorRole.ASSISTANT
        assert Reasoning.model_validate_json(response.message.content)

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_structured_outputs": True}),
            ("openai", {"enable_structured_outputs": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-structured-outputs-invoke", "openai-structured-outputs-invoke"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable when configuring structured outputs.")
    async def test_structured_outputs_invoke(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test structured outputs invoke."""
        responses = await agent_test_base.get_invoke_with_retry(
            responses_agent,
            messages="how can I solve 8x + 7y = -23, and 4x=12?",
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, ChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            assert Reasoning.model_validate_json(response.message.content)

    @pytest.mark.parametrize(
        "responses_agent",
        [
            ("azure", {"enable_structured_outputs": True}),
            ("openai", {"enable_structured_outputs": True}),
        ],
        indirect=["responses_agent"],
        ids=["azure-structured-outputs-invoke-stream", "openai-structured-outputs-invoke-stream"],
    )
    @pytest.mark.xfail(reason="The Responses API is unstable when configuring structured outputs.")
    async def test_structured_outputs_stream(
        self, responses_agent: OpenAIResponsesAgent, agent_test_base: AgentTestBase
    ):
        """Test structured outputs streaming."""
        full_message: str = ""
        responses = await agent_test_base.get_invoke_stream_with_retry(
            responses_agent,
            messages="how can I solve 8x + 7y = -23, and 4x=12?",
        )
        assert len(responses) > 0
        for response in responses:
            assert isinstance(response.message, StreamingChatMessageContent)
            assert response.message.role == AuthorRole.ASSISTANT
            full_message += response.message.content
        assert Reasoning.model_validate_json(full_message)

    # endregion
