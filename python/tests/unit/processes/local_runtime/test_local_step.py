# Copyright (c) Microsoft. All rights reserved.
from queue import Queue
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import (
    ProcessFunctionNotFoundException,
)
from semantic_kernel.functions import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import LocalEvent
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.processes.local_runtime.local_step import LocalStep


@pytest.fixture
def mocked_process_step_state():
    """Fixture for creating a mocked KernelProcessStepState object."""
    return KernelProcessStepState(name="my_step", id="123", state=None, version="1.0")


@pytest.fixture
def mocked_process_step_state_without_id():
    """Fixture for creating a mocked KernelProcessStepState object without id."""
    return KernelProcessStepState(name="my_step", id=None, state=None, version="1.0")


@pytest.fixture
def mocked_process_step_info(mocked_process_step_state):
    """Fixture for creating a mocked KernelProcessStepInfo object."""
    return KernelProcessStepInfo(inner_step_type=AsyncMock(spec=type), state=mocked_process_step_state, output_edges={})


@pytest.fixture
def mocked_process_step_info_without_id(mocked_process_step_state_without_id):
    """Fixture for creating a mocked KernelProcessStepInfo object."""
    return KernelProcessStepInfo(
        inner_step_type=AsyncMock(spec=type), state=mocked_process_step_state_without_id, output_edges={}
    )


async def test_parse_initial_configuration_adds_ids_if_missing():
    """Test that parse_initial_configuration sets the step_info.state.id if it is None."""
    edge = KernelProcessEdge(source_step_id="s1", output_target=AsyncMock(spec=KernelProcessFunctionTarget))
    data = {
        "step_info": KernelProcess(
            state=KernelProcessState(name="test_step", version="1.0"),  # noqa: F821
            steps=[AsyncMock(spec=KernelProcessStepInfo)],
            edges={"test_event": [edge]},
        ),
    }

    # Call the parse_initial_configuration
    processed_data = LocalStep.parse_initial_configuration(data)  # type: ignore

    # Assert that it sets the id
    assert processed_data["step_state"].id is not None
    assert processed_data["step_state"].id != ""
    assert processed_data["event_namespace"] == f"{processed_data['step_state'].name}_{processed_data['step_state'].id}"
    assert "output_edges" in processed_data
    assert processed_data["output_edges"] == {"test_event": [edge]}


async def test_parse_initial_configuration_id_already_set():
    """Test that parse_initial_configuration does not overwrite step_info.state.id if already set."""
    data = {
        "step_info": KernelProcess(
            state=KernelProcessState(name="test_step", id="test_id_set", version="1.0"),  # noqa: F821
            steps=[AsyncMock(spec=KernelProcessStepInfo)],
        ),
    }

    # Call the parse_initial_configuration
    processed_data = LocalStep.parse_initial_configuration(data)  # type: ignore

    assert processed_data["step_state"].id is not None
    assert processed_data["step_state"].id == "test_id_set"

    assert processed_data["event_namespace"] == f"{processed_data['step_state'].name}_{processed_data['step_state'].id}"
    assert "output_edges" in processed_data


def test_name_property(mocked_process_step_state, mocked_process_step_info):
    """Test that the name property returns the name from the step_info.state."""
    step = LocalStep(
        kernel=MagicMock(spec=Kernel),
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    assert step.name == "my_step"


def test_id_property_with_id(mocked_process_step_state, mocked_process_step_info):
    """Test that the id property returns the ID if it is available."""
    step = LocalStep(
        kernel=MagicMock(spec=Kernel),
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    assert step.id == "123"


def test_id_property_without_id(mocked_process_step_state_without_id, mocked_process_step_info_without_id):
    """Test that the id property returns an empty string if ID is None."""
    step = LocalStep(
        kernel=MagicMock(spec=Kernel),
        step_info=mocked_process_step_info_without_id,
        event_namespace="ns",
        step_state=mocked_process_step_state_without_id,
        factories={},
    )

    assert step.id == ""


async def test_handle_message_raises_exception_when_message_is_none(
    mocked_process_step_state, mocked_process_step_info
):
    """Test handle_message raises ValueError when message is None."""
    step = LocalStep(
        kernel=MagicMock(spec=Kernel),
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    with pytest.raises(ValueError) as exc:
        await step.handle_message(cast(LocalMessage, None))
    assert "The message is None." in str(exc.value)


async def test_handle_message_initializes_step_if_not_initialized(mocked_process_step_state, mocked_process_step_info):
    """Test handle_message calls initialize_step if the step isn't yet initialized."""
    mock_kernel = MagicMock(spec=Kernel)
    step = LocalStep(
        kernel=mock_kernel,
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        functions={"other_func": AsyncMock(spec=KernelFunction)},
        inputs={
            "other_func": {"param": "ready_value"},
        },
        initial_inputs={
            "other_func": {"param": None},
        },
        initialize_task=False,
    )

    with patch.object(LocalStep, "initialize_step") as mock_initialize_step:
        msg = LocalMessage(
            source_id="source",
            destination_id="dest",
            function_name="other_func",
            values={"param": "value"},
            target_event_id=None,
            target_event_data=None,
        )

        await step.handle_message(msg)

        mock_initialize_step.assert_awaited_once()
        assert step.initialize_task is True


async def test_handle_message_raises_if_functions_not_initialized(mocked_process_step_state, mocked_process_step_info):
    """Test handle_message raises ValueError if step is not properly initialized."""
    # We simulate that after initialization, the step still doesn't have `functions`.
    mock_kernel = AsyncMock(spec=Kernel)

    step = LocalStep(
        kernel=mock_kernel,  # type: ignore
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        initialize_task=False,
    )

    # Force the initialize_step to not fill in functions.
    async def mocked_init_step():
        step.functions = {}
        step.inputs = {}
        step.initial_inputs = {}

    with patch.object(
        LocalStep,
        "initialize_step",
        return_value=AsyncMock(side_effect=mocked_init_step),
    ):
        msg = LocalMessage(
            source_id="source",
            destination_id="dest",
            function_name="any_func",
            values={"param": "value"},
        )

        with pytest.raises(ProcessFunctionNotFoundException) as exc:
            await step.handle_message(msg)

        assert "Function any_func not found in plugin my_step" in str(exc.value)


async def test_handle_message_updates_inputs_and_invokes_function(mocked_process_step_state, mocked_process_step_info):
    """Test that handle_message updates inputs with message values and invokes the function
    if all parameters are provided."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke = AsyncMock(return_value=MagicMock(value="result"))

    # Create a function that requires one parameter
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.name = "func"
    mock_function.plugin_name = "test_plugin"

    mock_function.metadata = AsyncMock(spec=KernelFunctionMetadata)
    mock_function.metadata.name = "func"
    mock_function.metadata.plugin_name = "test_plugin"
    mock_function.metadata.is_prompt = False

    step = LocalStep(
        kernel=mock_kernel,
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        functions={
            "func": mock_function,
        },
        inputs={"func": {"param": None}},
        initial_inputs={"func": {"param": None}},
        initialize_task=True,
    )

    with patch.object(LocalStep, "emit_event") as mock_emit_event:
        msg = LocalMessage(
            source_id="source",
            destination_id="dest",
            function_name="func",
            values={"param": "value"},
        )

        await step.handle_message(msg)

        # Function invoked with correct arguments
        mock_kernel.invoke.assert_awaited_once()
        mock_emit_event.assert_awaited()

        assert mock_emit_event.call_args.args[0].id == "func.OnResult"

        # After invocation, input is reset
        assert step.inputs["func"]["param"] is None


async def test_handle_message_raises_target_function_not_found(mocked_process_step_state, mocked_process_step_info):
    """Test handle_message raises an exception if the target function is not the one that is invocable."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke = AsyncMock(return_value=AsyncMock(value="result"))

    # Pretend we have two functions, and only "other_func" is fully ready
    step = LocalStep(
        kernel=mock_kernel,
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,  # type: ignore
        factories={},
        functions={"other_func": AsyncMock(spec=KernelFunction)},
        inputs={
            "other_func": {"param": "ready_value"},
        },
        initial_inputs={
            "other_func": {"param": None},
        },
        initialize_task=True,
    )

    msg = LocalMessage(
        source_id="source",
        destination_id="dest",
        function_name="mismatched_func",
        values={"param": "value"},
    )

    with pytest.raises(ProcessFunctionNotFoundException) as exc:
        await step.handle_message(msg)

    assert "Function mismatched_func not found in plugin my_step" in str(exc.value)


async def test_handle_message_raises_function_not_found_if_no_function(
    mocked_process_step_state, mocked_process_step_info
):
    """Test handle_message raises ProcessFunctionNotFoundException if the function is not found in the step."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke = AsyncMock(return_value=AsyncMock(value="result"))

    step = LocalStep(
        kernel=mock_kernel,
        step_info=mocked_process_step_info,  # type: ignore
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        functions={},
        inputs={"func": {"param": "ready_value"}},
        initial_inputs={"func": {"param": None}},
        initialize_task=True,
    )

    msg = LocalMessage(
        source_id="source",
        destination_id="dest",
        function_name="func",
        values={"param": "value"},
    )

    with pytest.raises(ProcessFunctionNotFoundException) as exc:
        await step.handle_message(msg)
    assert "Function func not found in plugin my_step" in str(exc.value)


async def test_handle_message_emits_error_event_on_exception(mocked_process_step_state, mocked_process_step_info):
    """Test handle_message emits an OnError event when the function invocation raises an exception."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke = AsyncMock(side_effect=KernelException("error"))

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.name = "func"
    mock_function.plugin_name = "test_plugin"

    mock_function.metadata = AsyncMock(spec=KernelFunctionMetadata)

    mock_function.metadata.name = "func"
    mock_function.metadata.plugin_name = "test_plugin"
    mock_function.metadata.is_prompt = False

    step = LocalStep(
        kernel=mock_kernel,  # type: ignore
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        functions={"func": mock_function},
        inputs={"func": {"param": "some_value"}},
        initial_inputs={"func": {"param": None}},
        initialize_task=True,
    )

    with patch.object(LocalStep, "emit_event") as mock_emit_event:
        msg = LocalMessage(
            source_id="source",
            destination_id="dest",
            function_name="func",
            values={},
        )

        await step.handle_message(msg)

        # The event name for error is "func.OnError"
        assert mock_emit_event.await_args is not None
        mock_emit_event.assert_awaited()
        assert mock_emit_event.call_args.args[0].id == "func.OnError"


async def test_invoke_function_calls_kernel_invoke():
    """Test invoke_function calls the kernel's invoke method with provided arguments."""
    mock_kernel = AsyncMock(spec=Kernel)
    mock_kernel.invoke = AsyncMock()

    mock_function = AsyncMock(spec=KernelFunction)

    mock_step_info = AsyncMock(spec=KernelProcessStepInfo)
    mock_step_info.edges = MagicMock(return_value={"edge1": "value1", "edge2": "value2"})
    mock_step_info.state = KernelProcessStepState(name="test", id="step-id", state={}, version="1.0")

    step = LocalStep(
        kernel=mock_kernel,  # type: ignore
        step_info=mock_step_info,
        outgoing_event_queue=Queue(),
        event_namespace="ns",
        step_state=mock_step_info.state,
        factories={},
    )

    args = {"key": "value"}
    await step.invoke_function(mock_function, mock_kernel, args)

    mock_kernel.invoke.assert_awaited_once_with(mock_function, **args)


async def test_emit_event_puts_local_event_into_queue():
    """Test emit_event creates a LocalEvent and puts it into the outgoing_event_queue."""
    queue_obj = Queue()
    mock_step_info = AsyncMock(spec=KernelProcessStepInfo)
    mock_step_info.edges = MagicMock(return_value={"edge1": "value1", "edge2": "value2"})
    mock_step_info.state = KernelProcessStepState(name="test", id="step-id", state={}, version="1.0")

    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),
        step_info=mock_step_info,
        outgoing_event_queue=queue_obj,
        event_namespace="ns",
        step_state=mock_step_info.state,
        factories={},
    )

    event = KernelProcessEvent(id="test_event", data="some_data")
    await step.emit_event(event)
    # The queue should contain a LocalEvent
    assert not queue_obj.empty()
    local_event = queue_obj.get()
    assert queue_obj.empty()
    assert isinstance(local_event, LocalEvent)
    assert local_event.inner_event is event
    assert local_event.namespace == "test_step-id"


async def test_emit_local_event_puts_into_queue():
    """Test emit_local_event directly places the local_event into the queue with updated namespace."""
    queue_obj = Queue()
    mock_step_info = AsyncMock(spec=KernelProcessStepInfo)
    mock_step_info.edges = MagicMock(return_value={"edge1": "value1", "edge2": "value2"})
    mock_step_info.state = KernelProcessStepState(name="test", id="step-id", state={}, version="1.0")

    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),
        step_info=mock_step_info,
        outgoing_event_queue=queue_obj,
        event_namespace="original_ns",
        step_state=mock_step_info.state,
        factories={},
    )

    local_event = LocalEvent(namespace="temp", inner_event=KernelProcessEvent(id="evt"))
    await step.emit_local_event(local_event)

    assert not queue_obj.empty()
    popped = queue_obj.get()
    assert popped is local_event
    # The namespace is updated by scoped_event
    assert popped.namespace == f"{step.name}_{step.id}"


def test_get_all_events_returns_all_events_from_queue(mocked_process_step_state, mocked_process_step_info):
    """Test get_all_events drains the outgoing_event_queue and returns them."""
    queue_obj = Queue()
    event1 = LocalEvent(namespace="ns1", inner_event=KernelProcessEvent(id="e1"))
    event2 = LocalEvent(namespace="ns2", inner_event=KernelProcessEvent(id="e2"))
    queue_obj.put(event1)
    queue_obj.put(event2)

    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),  # type: ignore
        step_info=mocked_process_step_info,
        outgoing_event_queue=queue_obj,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    events = step.get_all_events()
    assert len(events) == 2
    assert events[0] == event1
    assert events[1] == event2
    # Queue should be empty now
    assert queue_obj.empty()


def test_get_edge_for_event_returns_edge_list(mocked_process_step_state):
    """Test that get_edge_for_event returns the edges from output_edges that match the event id."""
    edge = KernelProcessEdge(source_step_id="s1", output_target=AsyncMock(spec=KernelProcessFunctionTarget))
    mock_info = KernelProcessStepInfo(
        inner_step_type=AsyncMock(spec=type),
        state=mocked_process_step_state,
        output_edges={"test_event": [edge]},
    )
    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),  # type: ignore
        step_info=mock_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    edges = step.get_edge_for_event("test_event")
    assert len(edges) == 1
    assert edges[0] == edge

    output = step.output_edges["test_event"]
    assert output[0] is edge

    # For a non-existing event, expect empty list
    assert step.get_edge_for_event("not_found") == []


async def test_to_kernel_process_step_info_initializes_if_needed(mocked_process_step_state, mocked_process_step_info):
    """Test to_kernel_process_step_info calls initialize_step if not yet done."""
    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
        initialize_task=False,
    )

    with patch.object(LocalStep, "initialize_step") as mock_initialize_step:
        result = await step.to_kernel_process_step_info()

        mock_initialize_step.assert_awaited_once()
        assert result == mocked_process_step_info
        assert step.initialize_task is True


def test_scoped_event_updates_namespace(mocked_process_step_state, mocked_process_step_info):
    """Test scoped_event sets the local_event's namespace to name_id."""
    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    some_event = LocalEvent(namespace=None, inner_event=KernelProcessEvent(id="evt"))
    result = step.scoped_event(some_event)

    assert result.namespace == "my_step_123"


def test_scoped_event_from_kernel_process_creates_scoped_event(mocked_process_step_state, mocked_process_step_info):
    """Test scoped_event_from_kernel_process creates a local event from the kernel process event
    with the step's scope."""
    step = LocalStep(
        kernel=AsyncMock(spec=Kernel),  # type: ignore
        step_info=mocked_process_step_info,
        event_namespace="ns",
        step_state=mocked_process_step_state,
        factories={},
    )

    kpe = KernelProcessEvent(id="test_id", data="some_data")
    local_event = step.scoped_event_from_kernel_process(kpe)

    assert local_event.namespace == "my_step_123"
    assert local_event.inner_event == kpe
    assert local_event.inner_event is kpe
