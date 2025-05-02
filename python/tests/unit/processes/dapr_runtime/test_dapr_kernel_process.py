# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.dapr_runtime.dapr_kernel_process import start
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


class FakeDaprKernelProcessContext:
    def __init__(self, process, max_supersteps: int | None = None):
        self.process = process
        self.start_with_event = AsyncMock()
        self.max_supersteps = max_supersteps


async def test_start_with_valid_parameters():
    state = MagicMock(spec=KernelProcessState)
    state.name = "valid_state"
    state.id = "state_1"

    mock_step = MagicMock(spec=KernelProcessStepInfo)
    process = KernelProcess(state=state, steps=[mock_step])

    kernel = MagicMock(spec=Kernel)
    initial_event = KernelProcessEvent(id="event_1", data="data_1")

    with patch(
        "semantic_kernel.processes.dapr_runtime.dapr_kernel_process.DaprKernelProcessContext",
        new=FakeDaprKernelProcessContext,
    ):
        result = await start(process=process, kernel=kernel, initial_event=initial_event, max_supersteps=10)

        assert isinstance(result, FakeDaprKernelProcessContext)
        assert result.process == process
        assert result.max_supersteps == 10
        result.start_with_event.assert_called_once_with(initial_event)


async def test_start_with_invalid_process():
    kernel = MagicMock(spec=Kernel)
    initial_event = KernelProcessEvent(id="event_1", data="data_1")

    with pytest.raises(ProcessInvalidConfigurationException, match="process cannot be None"):
        await start(process=None, kernel=kernel, initial_event=initial_event)


async def test_start_with_invalid_initial_event():
    state = MagicMock(spec=KernelProcessState)
    type(state).name = PropertyMock(return_value="valid_state")
    mock_step = MagicMock(spec=KernelProcessStepInfo)
    process = KernelProcess(state=state, steps=[mock_step])
    kernel = MagicMock(spec=Kernel)

    with pytest.raises(ProcessInvalidConfigurationException, match="initial_event cannot be None"):
        await start(process=process, kernel=kernel, initial_event=None)


async def test_start_with_initial_event_as_string():
    state = MagicMock(spec=KernelProcessState)
    type(state).name = PropertyMock(return_value="valid_state")
    mock_step = MagicMock(spec=KernelProcessStepInfo)
    process = KernelProcess(state=state, steps=[mock_step])
    kernel = MagicMock(spec=Kernel)
    initial_event = "start_event"

    with patch(
        "semantic_kernel.processes.dapr_runtime.dapr_kernel_process.DaprKernelProcessContext", new=MagicMock()
    ) as mock_process_context_class:
        mock_process_context_instance = mock_process_context_class.return_value
        mock_process_context_instance.start_with_event = AsyncMock()

        result = await start(process=process, kernel=kernel, initial_event=initial_event, data="event_data")

        assert result == mock_process_context_instance
        mock_process_context_instance.start_with_event.assert_called_once()
        args, _ = mock_process_context_instance.start_with_event.call_args
        actual_event = args[0]
        assert isinstance(actual_event, KernelProcessEvent)
        assert actual_event.id == "start_event"
        assert actual_event.data == "event_data"
