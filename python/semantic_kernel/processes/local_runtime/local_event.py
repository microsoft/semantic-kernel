# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class LocalEvent(KernelBaseModel):
    """An event that is local to a namespace."""

    namespace: str | None
    inner_event: KernelProcessEvent

    @property
    def id(self) -> str:
        """The ID of the event."""
        return f"{self.namespace}.{self.inner_event.id}" if self.namespace else self.inner_event.id

    @property
    def data(self) -> Any:
        """The data of the event."""
        return self.inner_event.data

    @property
    def visibility(self) -> KernelProcessEventVisibility:
        """The visibility of the event."""
        return self.inner_event.visibility

    @classmethod
    def from_kernel_process_event(cls, kernel_process_event: KernelProcessEvent, namespace: str) -> "LocalEvent":
        """Create a local event from a kernel process event."""
        return cls(namespace=namespace, inner_event=kernel_process_event)
