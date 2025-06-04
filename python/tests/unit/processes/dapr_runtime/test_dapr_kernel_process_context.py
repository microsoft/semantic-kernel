# Copyright (c) Microsoft. All rights reserved.

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from semantic_kernel.processes.dapr_runtime.dapr_kernel_process_context import DaprKernelProcessContext
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.interfaces.process_interface import ProcessInterface
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState


class DummyInnerStepType:
    pass


@pytest.fixture
def process_context():
    state = KernelProcessState(name="TestProcess", version="1.0", id=str(uuid.uuid4()))

    step_state = KernelProcessStepState(name="TestStep", version="1.0", id="step1")

    step = KernelProcessStepInfo(
        state=step_state,
        inner_step_type=DummyInnerStepType,
        output_edges={},
    )

    steps = [step]
    process = KernelProcess(state=state, steps=steps)

    with patch("dapr.actor.ActorProxy.create") as mock_actor_proxy_create:
        mock_dapr_process = AsyncMock(spec=ProcessInterface)
        mock_actor_proxy_create.return_value = mock_dapr_process

        context = DaprKernelProcessContext(process=process)

        yield context, mock_dapr_process


async def test_start_with_event(process_context):
    context, mock_dapr_process = process_context

    initial_event = KernelProcessEvent(id="event1", data="some data")

    await context.start_with_event(initial_event)

    dapr_process_info = DaprProcessInfo.from_kernel_process(context.process)
    expected_payload = {
        "process_info": dapr_process_info.model_dump_json(),
        "parent_process_id": None,
        "max_supersteps": context.max_supersteps,
    }
    mock_dapr_process.initialize_process.assert_awaited_once_with(expected_payload)

    initial_event_json = initial_event.model_dump_json()
    mock_dapr_process.run_once.assert_awaited_once_with(initial_event_json)


async def test_send_event(process_context):
    context, mock_dapr_process = process_context

    event = KernelProcessEvent(id="event2", data="event data")

    await context.send_event(event)

    mock_dapr_process.send_message.assert_awaited_once_with(event)


async def test_stop(process_context):
    context, mock_dapr_process = process_context

    await context.stop()

    mock_dapr_process.stop.assert_awaited_once()


async def test_get_state(process_context):
    context, mock_dapr_process = process_context

    dapr_process_info = DaprProcessInfo.from_kernel_process(context.process)
    mock_dapr_process.get_process_info.return_value = dapr_process_info

    result = await context.get_state()

    mock_dapr_process.get_process_info.assert_awaited_once()

    assert isinstance(result, KernelProcess)
    assert result.state.id == context.process.state.id
    assert result.state.name == context.process.state.name
