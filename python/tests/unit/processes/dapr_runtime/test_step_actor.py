# Copyright (c) Microsoft. All rights reserved.

import json
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dapr.actor import ActorId, ActorProxy

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import (
    ProcessFunctionNotFoundException,
)
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.step_actor import StepActor
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_event import ProcessEvent
from semantic_kernel.processes.process_message import ProcessMessage


class FakeStep:
    async def activate(self, state):
        self.activated_state = state


class FakeState:
    pass


@pytest.fixture
def actor_context():
    ctx = MagicMock()
    actor_id = ActorId("test_actor")
    kernel = MagicMock()
    return StepActor(ctx, actor_id, kernel, factories={})


async def test_initialize_step(actor_context):
    input_data = json.dumps({
        "step_info": {
            "state": {"name": "TestStep", "version": "1.0", "id": "step_1"},
            "inner_step_python_type": "SomeStepType",
            "edges": {},
        },
        "parent_process_id": "parent_1",
    })

    with (
        patch.object(actor_context._state_manager, "try_add_state", new=AsyncMock()) as mock_try_add_state,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
    ):
        await actor_context.initialize_step(input_data)

        assert actor_context.step_info is not None
        mock_try_add_state.assert_any_call("DaprStepInfo", actor_context.step_info.model_dump_json())
        mock_save_state.assert_called_once()


async def test_prepare_incoming_messages(actor_context):
    message = ProcessMessage(
        source_id="source_1",
        destination_id="dest_1",
        function_name="test_function",
        values={"param1": "value1"},
    )
    mock_message_json = json.dumps(message.model_dump())

    expected_state_key = "incomingMessagesState"

    with (
        patch("dapr.actor.ActorProxy.create", new=MagicMock()) as mock_actor_proxy,
        patch.object(actor_context._state_manager, "try_add_state", new=AsyncMock()) as mock_try_add_state,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
    ):
        mock_queue = AsyncMock()
        mock_queue.dequeue_all.return_value = [mock_message_json]
        mock_actor_proxy.return_value = mock_queue

        incoming_message_count = await actor_context.prepare_incoming_messages()

        assert incoming_message_count == 1
        assert actor_context.incoming_messages.qsize() == 1
        mock_try_add_state.assert_called_with(expected_state_key, [mock_message_json])
        mock_save_state.assert_called_once()


async def test_process_incoming_messages(actor_context):
    actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="Test Step", version="1.0", id="step_123"),
        inner_step_python_type="SomeStepType",
        edges={},
    )

    message = ProcessMessage(
        source_id="source_1",
        destination_id="dest_1",
        function_name="test_function",
        values={"param1": "value1"},
    )
    actor_context.incoming_messages.put(message)

    with (
        patch.object(actor_context, "handle_message", new=AsyncMock()) as mock_handle_message,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
        patch.object(
            actor_context._state_manager, "try_add_state", new=AsyncMock(return_value=True)
        ) as mock_try_add_state,
    ):
        await actor_context.process_incoming_messages()
        mock_handle_message.assert_called_once_with(message)
        mock_save_state.assert_called_once()
        expected_messages = []
        expected_messages = [json.dumps(msg.model_dump()) for msg in list(actor_context.incoming_messages.queue)]
        mock_try_add_state.assert_any_call("incomingMessagesState", expected_messages)


async def test_activate_step_with_factory_creates_state(actor_context):
    fake_step_instance = FakeStep()
    fake_step_instance.activate = AsyncMock(side_effect=fake_step_instance.activate)

    fake_plugin = MagicMock()
    fake_plugin.functions = {"test_function": lambda x: x}

    with (
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.get_generic_state_type",
            return_value=FakeState,
        ),
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.get_fully_qualified_name",
            return_value="FakeStateFullyQualified",
        ),
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.find_input_channels",
            return_value={"channel": {"input": "value"}},
        ),
    ):
        actor_context.factories = {"FakeStep": lambda: fake_step_instance}
        actor_context.inner_step_type = "FakeStep"
        actor_context.step_info = DaprStepInfo(
            state=KernelProcessStepState(name="default_name", version="2.0", id="step_123"),
            inner_step_python_type="FakeStep",
            edges={},
        )
        actor_context.kernel.add_plugin = MagicMock(return_value=fake_plugin)
        actor_context._state_manager.try_add_state = AsyncMock()
        actor_context._state_manager.save_state = AsyncMock()

        await actor_context.activate_step()

        actor_context.kernel.add_plugin.assert_called_once_with(fake_step_instance, "default_name")
        assert actor_context.functions == fake_plugin.functions
        assert actor_context.initial_inputs == {"channel": {"input": "value"}}
        assert actor_context.inputs == {"channel": {"input": "value"}}
        assert actor_context.step_state is not None
        assert actor_context.step_state.version == "2.0"
        assert isinstance(actor_context.step_state.state, FakeState)
        fake_step_instance.activate.assert_awaited_once_with(actor_context.step_state)


async def test_activate_step_with_factory_uses_existing_state(actor_context):
    fake_step_instance = FakeStep()
    fake_step_instance.activate = AsyncMock(side_effect=fake_step_instance.activate)

    fake_plugin = MagicMock()
    fake_plugin.functions = {"test_function": lambda x: x}

    pre_existing_state = KernelProcessStepState(name="ExistingState", version="v1.0", id="ExistingState", state=None)

    with (
        patch.object(
            KernelProcessStepState,
            "model_dump",
            return_value={"name": "ExistingState", "id": "ExistingState", "state": None},
        ),
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.get_generic_state_type",
            return_value=FakeState,
        ),
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.get_fully_qualified_name",
            return_value="FakeStateFullyQualified",
        ),
        patch(
            "semantic_kernel.processes.dapr_runtime.actors.step_actor.find_input_channels",
            return_value={"channel": {"input": "value"}},
        ),
    ):
        actor_context.factories = {"FakeStep": lambda: fake_step_instance}
        actor_context.inner_step_type = "FakeStep"
        actor_context.step_info = DaprStepInfo(state=pre_existing_state, inner_step_python_type="FakeStep", edges={})
        actor_context.kernel.add_plugin = MagicMock(return_value=fake_plugin)
        actor_context._state_manager.try_add_state = AsyncMock()
        actor_context._state_manager.save_state = AsyncMock()

        await actor_context.activate_step()

        actor_context.kernel.add_plugin.assert_called_once_with(fake_step_instance, pre_existing_state.name)
        assert actor_context.functions == fake_plugin.functions
        assert actor_context.initial_inputs == {"channel": {"input": "value"}}
        assert actor_context.inputs == {"channel": {"input": "value"}}
        assert actor_context.step_state is not None
        assert actor_context.step_state.version == "v1.0"
        actor_context._state_manager.try_add_state.assert_any_await(
            ActorStateKeys.StepStateType.value, "FakeStateFullyQualified"
        )
        actor_context._state_manager.try_add_state.assert_any_await(
            ActorStateKeys.StepStateJson.value, json.dumps(pre_existing_state.model_dump())
        )
        actor_context._state_manager.save_state.assert_awaited_once()
        assert isinstance(actor_context.step_state.state, FakeState)
        fake_step_instance.activate.assert_awaited_once_with(actor_context.step_state)


@pytest.fixture
def mock_actor_context():
    """Provides a fresh StepActor instance with mocked dependencies."""
    ctx = MagicMock()
    actor_id = ActorId("test_actor")
    kernel = MagicMock()
    actor = StepActor(ctx, actor_id, kernel, factories={})
    actor._state_manager = MagicMock()
    return actor


def test_name_property_before_init_raises(mock_actor_context):
    """Accessing .name before initialization raises KernelException"""
    with pytest.raises(KernelException):
        _ = mock_actor_context.name


async def test_name_property_after_init_returns_name(mock_actor_context):
    """After setting step_info, name returns the state's name"""
    step_state = KernelProcessStepState(name="MyStep", version="v1", id="id1")
    mock_actor_context.step_info = DaprStepInfo(
        state=step_state,
        inner_step_python_type="Any",
        edges={},
    )
    # should return MyStep
    assert mock_actor_context.name == "MyStep"


def test_get_edge_for_event_empty(mock_actor_context):
    """get_edge_for_event returns empty when no edges set"""
    mock_actor_context.output_edges = {}
    assert mock_actor_context.get_edge_for_event("event") == []


def test_get_edge_for_event_present(mock_actor_context):
    """get_edge_for_event returns correct list"""
    edge = KernelProcessEdge(
        source_step_id="s1",
        output_target=KernelProcessFunctionTarget(
            step_id="t1", function_name="f", parameter_name=None, target_event_id="e1"
        ),
    )

    mock_actor_context.output_edges = {"e1": [edge]}
    assert mock_actor_context.get_edge_for_event("e1") == [edge]


def test_scoped_event_none_raises(mock_actor_context):
    """scoped_event with None raises ValueError"""
    # Use cast to satisfy type checker
    with pytest.raises(ValueError):
        mock_actor_context.scoped_event(cast(ProcessEvent, None))


def test_scoped_event_sets_namespace(mock_actor_context):
    """scoped_event updates event namespace correctly"""
    # prepare name and id
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="StepName", version="v1", id="id"),
        inner_step_python_type="Any",
        edges={},
    )
    # create event
    evt = ProcessEvent(inner_event=KernelProcessEvent(id="e", data="d"), namespace=None)
    result = mock_actor_context.scoped_event(evt)
    assert result.namespace == f"StepName_{mock_actor_context.id.id}"


async def test_invoke_function_calls_kernel_invoke(mock_actor_context):
    """invoke_function delegates to kernel.invoke with correct args"""
    fake_fn = MagicMock(name="f")
    fake_kernel = MagicMock()
    fake_kernel.invoke = AsyncMock(return_value="result")
    res = await mock_actor_context.invoke_function(fake_fn, fake_kernel, {"a": 1})
    fake_kernel.invoke.assert_awaited_once_with(fake_fn, a=1)
    assert res == "result"


async def test_emit_event_without_namespace_raises(mock_actor_context):
    """emit_event without setting event_namespace raises ValueError"""
    mock_actor_context.event_namespace = None
    with pytest.raises(ValueError):
        await mock_actor_context.emit_event(KernelProcessEvent(id="e", data="d"))


async def test_emit_process_event_public_and_edge(mock_actor_context):
    """emit_process_event enqueues event to parent buffer and sends messages to targets"""
    # setup event as public and parent process id
    mock_actor_context.parent_process_id = "parent1"
    # fake ActorProxy.create to return AsyncMock for enqueue
    mock_parent = AsyncMock(spec=EventBufferActor)
    mock_child = AsyncMock(spec=EventBufferActor)

    def fake_create(actor_type, actor_id, actor_interface):
        # first call is for EventBufferInterface, second for MessageBufferInterface
        if actor_interface.__name__ == "EventBufferInterface":
            return mock_parent
        return mock_child

    with patch.object(ActorProxy, "create", side_effect=fake_create):
        # create an edge for event
        target = KernelProcessFunctionTarget(
            step_id="child1", function_name="func", parameter_name="p", target_event_id="evt"
        )
        edge = KernelProcessEdge(source_step_id="src", output_target=target)

        mock_actor_context.output_edges = {"evt": [edge]}
        mock_actor_context.get_edge_for_event = MagicMock(return_value=[edge])

        # call
        evt = ProcessEvent(
            inner_event=KernelProcessEvent(id="evt", data="data", visibility=KernelProcessEventVisibility.Public),
            namespace="ns",
        )
        await mock_actor_context.emit_process_event(evt)
        # verify enqueue on parent and child
        mock_parent.enqueue.assert_awaited_once()
        mock_child.enqueue.assert_awaited_once()


@patch.object(StepActor, "activate_step", AsyncMock())
async def test_to_dapr_step_info_errors(mock_actor_context):
    """to_dapr_step_info raises if uninitialized"""
    # case: step_info not set
    mock_actor_context.step_activated = False
    mock_actor_context.step_info = None
    with pytest.raises(ValueError):
        await mock_actor_context.to_dapr_step_info()

    # case: inner_step_type not set
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="S", version="v", id="id"),
        inner_step_python_type="Type",
        edges={},
    )
    mock_actor_context.inner_step_type = None
    mock_actor_context.step_activated = True
    with pytest.raises(ValueError):
        await mock_actor_context.to_dapr_step_info()


async def test_to_dapr_step_info_success(mock_actor_context):
    """to_dapr_step_info returns correct model_dump"""
    # setup valid step_info and inner_step_type
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="N", version="v", id="id"),
        inner_step_python_type="Type",
        edges={"e": []},
    )
    mock_actor_context.inner_step_type = "Type"
    mock_actor_context.step_activated = True
    result = await mock_actor_context.to_dapr_step_info()
    # check returned dict structure
    assert "inner_step_python_type" in result
    assert result["inner_step_python_type"] == "Type"
    assert result["edges"] == {"e": []}


async def test_handle_message_none_raises(mock_actor_context):
    """handle_message with None raises ValueError"""
    with pytest.raises(ValueError):
        await mock_actor_context.handle_message(None)


async def test_handle_message_no_function_found_raises(mock_actor_context):
    """handle_message raises when function exists in inputs but not in functions dict"""
    # prepare actor state
    mock_actor_context.step_activated = True
    mock_actor_context.functions = {}
    mock_actor_context.inputs = {"f1": {"a": "v"}}
    mock_actor_context.initial_inputs = {"f1": {"a": "v"}}
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="S", version="v", id="id"),
        inner_step_python_type="Type",
        edges={},
    )
    from semantic_kernel.processes.process_message import ProcessMessage

    msg = ProcessMessage(source_id="s", destination_id="d", function_name="f1", values={"a": "v"})
    with pytest.raises(ProcessFunctionNotFoundException):
        await mock_actor_context.handle_message(msg)


async def test_handle_message_function_returns_none_emits_error(mock_actor_context):
    """handle_message when invoke_function returns None emits an error event"""
    mock_actor_context.step_activated = True
    # ensure name property works by setting step_info
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="S", version="v", id="id"),
        inner_step_python_type="Type",
        edges={},
    )
    # prepare inputs and functions
    fake_kernel_fn = MagicMock(plugin_name="plug", name="f1")
    mock_actor_context.functions = {"f1": fake_kernel_fn}
    mock_actor_context.inputs = {"f1": {"x": 1}}
    mock_actor_context.initial_inputs = {"f1": {"x": None}}
    # patch invoke_function to return None
    mock_actor_context.invoke_function = AsyncMock(return_value=None)
    # capture emit_event
    mock_actor_context.emit_event = AsyncMock()
    from semantic_kernel.processes.process_message import ProcessMessage

    msg = ProcessMessage(source_id="s", destination_id="d", function_name="f1", values={"x": 1})
    await mock_actor_context.handle_message(msg)
    # should emit error event
    emitted = mock_actor_context.emit_event.call_args.args[0]
    assert isinstance(emitted, KernelProcessEvent)
    assert emitted.id == "f1.OnError"


async def test_handle_message_success_emits_result_and_resets_inputs(mock_actor_context):
    """handle_message successfully invokes function and emits result event"""
    # setup valid step_info and activation
    mock_actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="S", version="v", id="id"),
        inner_step_python_type="Type",
        edges={},
    )
    mock_actor_context.step_activated = True
    fake_kernel_fn = MagicMock(plugin_name="plug", name="f1")
    mock_actor_context.functions = {"f1": fake_kernel_fn}
    mock_actor_context.inputs = {"f1": {"x": 1}}
    mock_actor_context.initial_inputs = {"f1": {"x": None}}

    # define a dummy result class with a value attribute
    class DummyResult:
        def __init__(self, value):
            self.value = value

    r = DummyResult("out")
    mock_actor_context.invoke_function = AsyncMock(return_value=r)
    mock_actor_context.emit_event = AsyncMock()
    from semantic_kernel.processes.process_message import ProcessMessage

    msg = ProcessMessage(source_id="s", destination_id="d", function_name="f1", values={"x": 1})
    await mock_actor_context.handle_message(msg)
    # verify emitted result event and inputs reset
    emitted = mock_actor_context.emit_event.call_args.args[0]
    assert emitted.id == "f1.OnResult"
    assert emitted.data == "out"
    assert mock_actor_context.inputs["f1"] == {"x": None}
