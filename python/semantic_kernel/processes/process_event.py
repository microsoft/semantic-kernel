# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)


class ProcessEvent(KernelBaseModel):
    """A wrapper around KernelProcessEvent that helps to manage the namespace of the event."""

    namespace: str | None = None
    inner_event: KernelProcessEvent

    @property
    def id(self) -> str:
        """The Id of the event."""
        return f"{self.namespace}.{self.inner_event.id}"

    @property
    def data(self) -> Optional[object]:
        """The data of the event."""
        return self.inner_event.data

    @property
    def visibility(self) -> "KernelProcessEventVisibility":
        """The visibility of the event."""
        return self.inner_event.visibility

    @classmethod
    def from_kernel_process_event(cls, kernel_process_event: KernelProcessEvent, namespace: str) -> "ProcessEvent":
        """Creates a new ProcessEvent from a KernelProcessEvent."""
        return cls(namespace=namespace, inner_event=kernel_process_event)
