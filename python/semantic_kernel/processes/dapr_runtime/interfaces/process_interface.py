# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dapr.actor import ActorInterface, actormethod

from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent


@experimental
class ProcessInterface(ActorInterface, ABC):
    """Abstract base class for a process that follows the ActorInterface."""

    @abstractmethod
    @actormethod(name="initialize_process")
    async def initialize_process(self, input: dict) -> None:
        """Initializes the process with the specified instance of DaprProcessInfo.

        :param process_info: Used to initialize the process.
        :param parent_process_id: The parent ID of the process if one exists.
        """
        ...

    @abstractmethod
    @actormethod(name="start")
    async def start(self, keep_alive: bool) -> None:
        """Starts an initialized process.

        :param keep_alive: Indicates if the process should wait for external events after it's finished processing.
        """
        ...

    @abstractmethod
    @actormethod(name="run_once")
    async def run_once(self, process_event: "KernelProcessEvent | str | None") -> None:
        """Starts the process with an initial event and then waits for the process to finish.

        :param process_event: Required. The KernelProcessEvent to start the process with.
        """
        ...

    @abstractmethod
    @actormethod(name="stop")
    async def stop(self) -> None:
        """Stops a running process, canceling and waiting for it to complete before returning."""
        ...

    @abstractmethod
    @actormethod(name="send_message")
    async def send_message(self, process_event: "KernelProcessEvent") -> None:
        """Sends a message to the process without starting it if it is not already running.

        :param process_event: Required. The KernelProcessEvent to queue for the process.
        """
        ...

    @abstractmethod
    @actormethod(name="get_process_info")
    async def get_process_info(self) -> dict:
        """Retrieves the process information as a dict of DaprProcessInfo.

        :return: An instance of DaprProcessInfo.
        """
        ...
