# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.local_runtime.local_event import LocalEvent


def test_initialization_with_namespace():
    # Arrange
    namespace = "test_namespace"
    inner_event = MagicMock(spec=KernelProcessEvent)
    inner_event.id = "event_001"
    inner_event.data = {"key": "value"}
    inner_event.visibility = KernelProcessEventVisibility.Public

    # Act
    local_event = LocalEvent(namespace=namespace, inner_event=inner_event)

    # Assert
    assert local_event.namespace == namespace
    assert local_event.inner_event == inner_event
    assert local_event.id == f"{namespace}.event_001"
    assert local_event.data == {"key": "value"}
    assert local_event.visibility == KernelProcessEventVisibility.Public


def test_initialization_without_namespace():
    # Arrange
    namespace = None
    inner_event = MagicMock(spec=KernelProcessEvent)
    inner_event.id = "event_002"
    inner_event.data = {"key": "value"}
    inner_event.visibility = KernelProcessEventVisibility.Internal

    # Act
    local_event = LocalEvent(namespace=namespace, inner_event=inner_event)

    # Assert
    assert local_event.namespace is None
    assert local_event.inner_event == inner_event
    assert local_event.id == "event_002"
    assert local_event.data == {"key": "value"}
    assert local_event.visibility == KernelProcessEventVisibility.Internal


def test_from_kernel_process_event():
    # Arrange
    namespace = "namespace_from_method"
    kernel_process_event = MagicMock(spec=KernelProcessEvent)
    kernel_process_event.id = "event_003"
    kernel_process_event.data = {"key": "value"}
    kernel_process_event.visibility = KernelProcessEventVisibility.Public

    # Act
    local_event = LocalEvent.from_kernel_process_event(kernel_process_event=kernel_process_event, namespace=namespace)

    # Assert
    assert local_event.namespace == namespace
    assert local_event.inner_event == kernel_process_event
    assert local_event.id == f"{namespace}.event_003"
    assert local_event.data == {"key": "value"}
    assert local_event.visibility == KernelProcessEventVisibility.Public
