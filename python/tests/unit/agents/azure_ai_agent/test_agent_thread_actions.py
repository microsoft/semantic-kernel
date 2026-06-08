# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent, TextContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
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
    def __init__(self, id, status, content: str | None = None):
        self.id = id
        self.status = status
        self.content = content


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
        MockEvent("thread.message.created", MockRunData(id="msg_1", status="created", content="Hello")),
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
            assert isinstance(content, ChatMessageContent)
            assert content.metadata.get("message_id") == "msg_1"


# region Security tests for tools override and function_choice_behavior


async def test_validate_function_choice_behavior_rejects_required():
    """Required FCB is not supported for agent invocations."""
    with pytest.raises(AgentInvokeException, match="not supported"):
        AgentThreadActions._validate_function_choice_behavior(
            FunctionChoiceBehavior.Required()
        )


async def test_validate_function_choice_behavior_accepts_auto():
    """Auto FCB should be accepted without error."""
    AgentThreadActions._validate_function_choice_behavior(
        FunctionChoiceBehavior.Auto()
    )


async def test_validate_function_choice_behavior_rejects_none_invoke():
    """NoneInvoke FCB is not supported for agent invocations."""
    with pytest.raises(AgentInvokeException, match="not supported"):
        AgentThreadActions._validate_function_choice_behavior(
            FunctionChoiceBehavior.NoneInvoke()
        )


async def test_validate_function_choice_behavior_accepts_none():
    """None (no FCB) should be accepted."""
    AgentThreadActions._validate_function_choice_behavior(None)


async def test_validate_function_choice_behavior_rejects_auto_invoke_false():
    """Auto with auto_invoke=False is not supported for agent invocations."""
    with pytest.raises(AgentInvokeException, match="auto_invoke"):
        AgentThreadActions._validate_function_choice_behavior(
            FunctionChoiceBehavior.Auto(auto_invoke=False)
        )


async def test_validate_function_choice_behavior_rejects_empty_filters():
    """Empty filters dict should be rejected."""
    fcb = FunctionChoiceBehavior.Auto()
    fcb.filters = {}
    with pytest.raises(AgentInvokeException, match="must not be empty"):
        AgentThreadActions._validate_function_choice_behavior(fcb)


async def test_validate_function_choice_behavior_rejects_unknown_filter_keys():
    """Unknown filter keys should be rejected."""
    fcb = FunctionChoiceBehavior.Auto()
    # Bypass Pydantic validation to simulate a mistyped key reaching the validator
    object.__setattr__(fcb, "filters", {"include_functions": ["foo"]})
    with pytest.raises(AgentInvokeException, match="Unknown filter key"):
        AgentThreadActions._validate_function_choice_behavior(fcb)


async def test_validate_function_choice_behavior_accepts_valid_filters():
    """Valid filter keys should be accepted."""
    AgentThreadActions._validate_function_choice_behavior(
        FunctionChoiceBehavior.Auto(filters={"included_functions": ["plugin-func"]})
    )


async def test_get_tools_with_tools_override(ai_project_client, ai_agent_definition):
    """When tools_override is provided, it should replace agent.definition.tools."""
    from azure.ai.agents.models import CodeInterpreterToolDefinition

    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    kernel = MagicMock(spec=Kernel)
    kernel.get_full_list_of_function_metadata.return_value = []

    override_tool = CodeInterpreterToolDefinition()
    tools = AgentThreadActions._get_tools(
        agent=agent, kernel=kernel, tools_override=[override_tool]
    )
    # Should contain the override tool, not agent.definition.tools
    assert any(
        (isinstance(t, CodeInterpreterToolDefinition) or (isinstance(t, dict) and t.get("type") == "code_interpreter"))
        for t in tools
    )


async def test_get_tools_with_fcb_filters(ai_project_client, ai_agent_definition):
    """When function_choice_behavior has filters, only matching functions should be included."""
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    kernel = MagicMock(spec=Kernel)

    # Simulate filtered metadata
    mock_metadata = MagicMock()
    mock_metadata.fully_qualified_name = "Plugin-AllowedFunc"
    mock_metadata.name = "AllowedFunc"
    mock_metadata.plugin_name = "Plugin"
    mock_metadata.description = "An allowed function"
    mock_metadata.parameters = []
    mock_metadata.is_prompt = False
    mock_metadata.return_parameter = MagicMock()
    mock_metadata.return_parameter.description = ""
    mock_metadata.return_parameter.type_ = "str"
    mock_metadata.additional_properties = {}

    kernel.get_list_of_function_metadata.return_value = [mock_metadata]
    kernel.get_full_list_of_function_metadata.return_value = []

    fcb = FunctionChoiceBehavior.Auto(
        filters={"included_functions": ["Plugin-AllowedFunc"]}
    )
    AgentThreadActions._get_tools(
        agent=agent, kernel=kernel, function_choice_behavior=fcb
    )
    # Should have called get_list_of_function_metadata with the filters
    kernel.get_list_of_function_metadata.assert_called_once_with(fcb.filters)


async def test_get_tools_with_fcb_disable_kernel_functions(ai_project_client, ai_agent_definition):
    """When enable_kernel_functions=False, no kernel functions should be included."""
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    kernel = MagicMock(spec=Kernel)

    fcb = FunctionChoiceBehavior.Auto(enable_kernel_functions=False)
    AgentThreadActions._get_tools(
        agent=agent, kernel=kernel, function_choice_behavior=fcb
    )
    # Full list is called for validation, but filtered list should not be called
    kernel.get_full_list_of_function_metadata.assert_called_once()
    kernel.get_list_of_function_metadata.assert_not_called()


async def test_invoke_function_calls_passes_function_behavior():
    """_invoke_function_calls should pass function_behavior to kernel.invoke_function_call."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke_function_call.return_value = None

    fcc = FunctionCallContent(name="Plugin-Func", arguments={}, id="call1")
    from semantic_kernel.contents.chat_history import ChatHistory

    chat_history = ChatHistory()
    fcb = FunctionChoiceBehavior.Auto(
        filters={"included_functions": ["Plugin-Func"]}
    )

    await AgentThreadActions._invoke_function_calls(
        kernel=mock_kernel,
        fccs=[fcc],
        chat_history=chat_history,
        arguments=KernelArguments(),
        function_choice_behavior=fcb,
    )

    mock_kernel.invoke_function_call.assert_awaited_once()
    call_kwargs = mock_kernel.invoke_function_call.call_args
    assert call_kwargs.kwargs.get("function_behavior") is fcb


async def test_invoke_function_calls_passes_disabled_kernel_functions():
    """_invoke_function_calls should pass enable_kernel_functions=False FCB to kernel."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke_function_call.return_value = None

    fcc = FunctionCallContent(name="Plugin-Func", arguments={}, id="call1")
    from semantic_kernel.contents.chat_history import ChatHistory

    chat_history = ChatHistory()
    fcb = FunctionChoiceBehavior.Auto(enable_kernel_functions=False)

    await AgentThreadActions._invoke_function_calls(
        kernel=mock_kernel,
        fccs=[fcc],
        chat_history=chat_history,
        arguments=KernelArguments(),
        function_choice_behavior=fcb,
    )

    mock_kernel.invoke_function_call.assert_awaited_once()
    call_kwargs = mock_kernel.invoke_function_call.call_args
    passed_behavior = call_kwargs.kwargs.get("function_behavior")
    assert passed_behavior is fcb
    assert not passed_behavior.enable_kernel_functions


async def test_invoke_function_calls_blocks_disallowed_function():
    """A real Kernel should block a function call not in the FCB allowlist.

    This verifies that the enforcement in kernel.invoke_function_call actually
    rejects a disallowed function name when filters are provided, rather than
    only asserting that the kwarg is forwarded.
    """
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod

    @kernel_function
    def allowed_func() -> str:
        return "allowed"

    @kernel_function
    def disallowed_func() -> str:
        return "disallowed"

    kernel = Kernel()
    kernel.add_plugin(
        KernelPlugin(
            name="Plugin",
            functions=[
                KernelFunctionFromMethod(method=allowed_func, plugin_name="Plugin"),
                KernelFunctionFromMethod(method=disallowed_func, plugin_name="Plugin"),
            ],
        )
    )

    fcb = FunctionChoiceBehavior.Auto(
        filters={"included_functions": ["Plugin-allowed_func"]}
    )

    # Call a function NOT in the allowlist
    fcc = FunctionCallContent(
        name="Plugin-disallowed_func", plugin_name="Plugin",
        function_name="disallowed_func", arguments={}, id="call1",
    )
    chat_history = ChatHistory()

    result = await kernel.invoke_function_call(
        function_call=fcc,
        chat_history=chat_history,
        function_behavior=fcb,
    )
    # invoke_function_call catches the FunctionExecutionException and returns None,
    # adding an error message to chat_history instead of raising.
    assert result is None
    assert len(chat_history.messages) == 1
    result_item = chat_history.messages[0].items[0]
    assert "not part of the provided tools" in str(result_item.result)


async def test_invoke_function_calls_allows_permitted_function():
    """A real Kernel should allow a function call that IS in the FCB allowlist."""
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod

    @kernel_function
    def allowed_func() -> str:
        return "ok"

    @kernel_function
    def other_func() -> str:
        return "other"

    kernel = Kernel()
    kernel.add_plugin(
        KernelPlugin(
            name="Plugin",
            functions=[
                KernelFunctionFromMethod(method=allowed_func, plugin_name="Plugin"),
                KernelFunctionFromMethod(method=other_func, plugin_name="Plugin"),
            ],
        )
    )

    fcb = FunctionChoiceBehavior.Auto(
        filters={"included_functions": ["Plugin-allowed_func"]}
    )

    fcc = FunctionCallContent(
        name="Plugin-allowed_func", plugin_name="Plugin",
        function_name="allowed_func", arguments={}, id="call1",
    )
    chat_history = ChatHistory()

    await kernel.invoke_function_call(
        function_call=fcc,
        chat_history=chat_history,
        function_behavior=fcb,
    )
    # Should succeed — the function result should be in chat_history
    assert len(chat_history.messages) == 1
    result_item = chat_history.messages[0].items[0]
    assert "ok" in str(result_item.result)

async def test_invoke_raises_for_non_auto_fcb(ai_project_client, ai_agent_definition):
    """Calling AgentThreadActions.invoke() with a non-Auto FCB should raise before any API call."""
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    agent.client.agents = AsyncMock()

    with pytest.raises(AgentInvokeException, match="not supported"):
        async for _ in AgentThreadActions.invoke(
            agent=agent,
            thread_id="thread123",
            kernel=Kernel(),
            function_choice_behavior=FunctionChoiceBehavior.Required(),
        ):
            pass

    # No API calls should have been made
    agent.client.agents.runs.create.assert_not_awaited()


async def test_invoke_stream_raises_for_non_auto_fcb(ai_project_client, ai_agent_definition):
    """Calling AgentThreadActions.invoke_stream() with a non-Auto FCB should raise before any API call."""
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    agent.client.agents = AsyncMock()

    with pytest.raises(AgentInvokeException, match="not supported"):
        async for _ in AgentThreadActions.invoke_stream(
            agent=agent,
            thread_id="thread123",
            kernel=Kernel(),
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke(),
        ):
            pass

    # No API calls should have been made
    agent.client.agents.create_stream.assert_not_called()


# endregion
