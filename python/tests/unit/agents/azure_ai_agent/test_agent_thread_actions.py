# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from azure.ai.agents.models import (
    MessageTextContent,
    MessageTextDetails,
    RequiredFunctionToolCall,
    RequiredFunctionToolCallDetails,
    RunStep,
    RunStepCodeInterpreterToolCall,
    RunStepCodeInterpreterToolCallDetails,
    RunStepFunctionToolCall,
    RunStepFunctionToolCallDetails,
    RunStepMessageCreationDetails,
    RunStepMessageCreationReference,
    RunStepToolCallDetails,
    SubmitToolOutputsAction,
    SubmitToolOutputsDetails,
    ThreadMessage,
    ThreadRun,
)
from azure.ai.projects.aio import AIProjectClient
from pytest import fixture

from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent, TextContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel


@fixture
def mock_client():
    mock_thread = AsyncMock()
    mock_thread.id = "thread123"

    mock_threads = MagicMock()
    mock_threads.create = AsyncMock(return_value=mock_thread)

    mock_message = AsyncMock()
    mock_message.id = "message456"

    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value="someMessage")

    mock_agents = MagicMock()
    mock_agents.threads = mock_threads
    mock_agents.messages = mock_messages

    mock_client = AsyncMock(spec=AIProjectClient)
    mock_client.agents = mock_agents

    return mock_client


async def test_agent_thread_actions_create_thread(mock_client):
    thread_id = await AgentThreadActions.create_thread(mock_client)
    assert thread_id == "thread123"


async def test_agent_thread_actions_create_message(mock_client):
    msg = ChatMessageContent(role=AuthorRole.USER, content="some content")
    out = await AgentThreadActions.create_message(mock_client, "threadXYZ", msg)
    assert out == "someMessage"


async def test_agent_thread_actions_create_message_no_content():
    class FakeAgentClient:
        create_message = AsyncMock(return_value="should_not_be_called")

    class FakeClient:
        agents = FakeAgentClient()

    message = ChatMessageContent(role=AuthorRole.USER, content="   ")
    out = await AgentThreadActions.create_message(FakeClient(), "threadXYZ", message)
    assert out is None
    assert FakeAgentClient.create_message.await_count == 0


async def test_agent_thread_actions_invoke(ai_project_client: AIProjectClient, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    # Properly construct nested mocks without re-spec'ing from a mock
    mock_thread_run = ThreadRun(
        id="run123",
        thread_id="thread123",
        status="running",
        instructions="test agent",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        model="model",
    )

    agent.client.agents.runs = MagicMock()
    agent.client.agents.runs.create = AsyncMock(return_value=mock_thread_run)
    agent.client.agents.runs.get = AsyncMock(return_value=mock_thread_run)

    async def mock_poll_run_status(*args, **kwargs):
        yield RunStep(
            type="message_creation",
            id="msg123",
            thread_id="thread123",
            run_id="run123",
            created_at=int(datetime.now(timezone.utc).timestamp()),
            completed_at=int(datetime.now(timezone.utc).timestamp()),
            status="completed",
            agent_id="agent123",
            step_details=RunStepMessageCreationDetails(
                message_creation=RunStepMessageCreationReference(
                    message_id="msg123",
                ),
            ),
        )

    agent.client.agents.run_steps = MagicMock()
    agent.client.agents.run_steps.list = mock_poll_run_status

    mock_message = ThreadMessage(
        id="msg123",
        thread_id="thread123",
        run_id="run123",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        status="completed",
        agent_id="agent123",
        role="assistant",
        content=[MessageTextContent(text=MessageTextDetails(value="some message", annotations=[]))],
    )

    agent.client.agents.messages = MagicMock()
    agent.client.agents.messages.get = AsyncMock(return_value=mock_message)

    async for is_visible, message in AgentThreadActions.invoke(
        agent=agent, thread_id="thread123", kernel=AsyncMock(spec=Kernel)
    ):
        assert str(message.content) == "some message"
        break


async def test_agent_thread_actions_invoke_with_requires_action(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    agent.client.agents = MagicMock()

    mock_thread_run = ThreadRun(
        id="run123",
        thread_id="thread123",
        status="running",
        instructions="test agent",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        model="model",
    )

    agent.client.agents = MagicMock()

    agent.client.agents.runs = MagicMock()
    agent.client.agents.runs.create = AsyncMock(return_value=mock_thread_run)
    agent.client.agents.runs.get = AsyncMock(return_value=mock_thread_run)
    agent.client.agents.runs.submit_tool_outputs = AsyncMock()

    poll_count = 0

    async def mock_poll_run_status(*args, **kwargs):
        nonlocal poll_count
        if poll_count == 0:
            mock_thread_run.status = "requires_action"
            mock_thread_run.required_action = SubmitToolOutputsAction(
                submit_tool_outputs=SubmitToolOutputsDetails(
                    tool_calls=[
                        RequiredFunctionToolCall(
                            id="tool_call_id",
                            function=RequiredFunctionToolCallDetails(
                                name="mock_function_call", arguments={"arg": "value"}
                            ),
                        )
                    ]
                )
            )
        else:
            mock_thread_run.status = "completed"
        poll_count += 1
        return mock_thread_run

    def mock_get_function_call_contents(run: ThreadRun, function_steps: dict):
        function_call_content = FunctionCallContent(
            name="mock_function_call",
            arguments={"arg": "value"},
            id="tool_call_id",
        )
        function_steps[function_call_content.id] = function_call_content
        return [function_call_content]

    mock_run_step_tool_calls = RunStep(
        type="tool_calls",
        id="tool_step123",
        thread_id="thread123",
        run_id="run123",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        status="completed",
        agent_id="agent123",
        step_details=RunStepToolCallDetails(
            tool_calls=[
                # 1. This will yield FunctionResultContent
                RunStepFunctionToolCall(
                    id="tool_call_id",
                    function=RunStepFunctionToolCallDetails({
                        "name": "mock_function_call",
                        "arguments": '{"arg": "value"}',
                        "output": "some output",
                    }),
                ),
                # 2. This will yield TextContent
                RunStepCodeInterpreterToolCall(
                    id="tool_call_id",
                    code_interpreter=RunStepCodeInterpreterToolCallDetails(
                        input="some code",
                    ),
                ),
            ]
        ),
    )

    mock_run_step_message_creation = RunStep(
        type="message_creation",
        id="msg_step123",
        thread_id="thread123",
        run_id="run123",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        status="completed",
        agent_id="agent123",
        step_details=RunStepMessageCreationDetails(
            message_creation=RunStepMessageCreationReference(message_id="msg123")
        ),
    )

    mock_run_steps = [mock_run_step_tool_calls, mock_run_step_message_creation]

    async def mock_list_run_steps(*args, **kwargs):
        for step in mock_run_steps:
            yield step

    agent.client.agents.run_steps = MagicMock()
    agent.client.agents.run_steps.list = mock_list_run_steps

    mock_message = ThreadMessage(
        id="msg123",
        thread_id="thread123",
        run_id="run123",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        status="completed",
        agent_id="agent123",
        role="assistant",
        content=[MessageTextContent(text=MessageTextDetails(value="some message", annotations=[]))],
    )
    agent.client.agents.runs.get = AsyncMock(return_value=mock_message)

    agent.client.agents.runs.submit_tool_outputs = AsyncMock()

    with (
        patch.object(AgentThreadActions, "_poll_run_status", side_effect=mock_poll_run_status),
        patch(
            "semantic_kernel.agents.azure_ai.agent_thread_actions.get_function_call_contents",
            side_effect=mock_get_function_call_contents,
        ),
        patch.object(AgentThreadActions, "_invoke_function_calls", return_value=[None]),
    ):
        messages = []
        async for is_visible, content in AgentThreadActions.invoke(
            agent=agent,
            thread_id="thread123",
            kernel=AsyncMock(spec=Kernel),
        ):
            messages.append((is_visible, content))

    assert len(messages) == 3, "There should be three yields in total."

    assert isinstance(messages[0][1].items[0], FunctionCallContent)
    assert isinstance(messages[1][1].items[0], FunctionResultContent)
    assert isinstance(messages[2][1].items[0], TextContent)

    agent.client.agents.runs.submit_tool_outputs.assert_awaited_once()


class MockEvent:
    def __init__(self, event, data):
        self.event = event
        self.data = data

    def __iter__(self):
        return iter((self.event, self.data, None))


class MockRunData:
    def __init__(self, id, status):
        self.id = id
        self.status = status


class MockAsyncIterable:
    def __init__(self, items):
        self.items = items.copy()

    def __aiter__(self):
        self._iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockStream:
    def __init__(self, events):
        self.events = events

    async def __aenter__(self):
        return MockAsyncIterable(self.events)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_agent_thread_actions_invoke_stream(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    agent.client.agents = AsyncMock()

    events = [
        MockEvent("thread.run.created", MockRunData(id="run_1", status="queued")),
        MockEvent("thread.run.in_progress", MockRunData(id="run_1", status="in_progress")),
        MockEvent("thread.run.completed", MockRunData(id="run_1", status="completed")),
    ]

    main_run_stream = MockStream(events)
    agent.client.agents.create_stream.return_value = main_run_stream

    with (
        patch.object(AgentThreadActions, "_invoke_function_calls", return_value=None),
        patch.object(AgentThreadActions, "_format_tool_outputs", return_value=[{"type": "mock_tool_output"}]),
    ):
        collected_messages = []
        async for content in AgentThreadActions.invoke_stream(
            agent=agent,
            thread_id="thread123",
            kernel=AsyncMock(spec=Kernel),
        ):
            collected_messages.append(content)
