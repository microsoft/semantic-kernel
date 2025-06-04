# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock

import pytest

from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent


class MockKernelProcessMessageChannel(KernelProcessMessageChannel):
    async def emit_event(self, process_event: KernelProcessEvent) -> None:
        pass


async def test_initialization():
    # Arrange
    channel = MockKernelProcessMessageChannel()

    # Act
    context = KernelProcessStepContext(channel=channel)

    # Assert
    assert context.step_message_channel == channel


async def test_emit_event():
    # Arrange
    channel = MockKernelProcessMessageChannel()
    channel.emit_event = AsyncMock()
    context = KernelProcessStepContext(channel=channel)
    event = KernelProcessEvent(id="event_001", data={"key": "value"})

    # Act
    await context.emit_event(event)

    # Assert
    channel.emit_event.assert_called_once_with(event)


async def test_emit_event_with_invalid_event():
    # Arrange
    channel = MockKernelProcessMessageChannel()
    channel.emit_event = AsyncMock()
    context = KernelProcessStepContext(channel=channel)

    # Act & Assert
    with pytest.raises(ProcessEventUndefinedException):
        await context.emit_event(None)
