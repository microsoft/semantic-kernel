# Copyright (c) Microsoft. All rights reserved.


from dapr.actor import ActorInterface, actormethod

from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo


class Step(ActorInterface):
    """Abstract base class for a step in the process workflow."""

    @actormethod(name="initialize_step")
    # async def initialize_step(self, step_info: "DaprStepInfo", parent_process_id: str | None = None) -> None:
    async def initialize_step(self, input: dict) -> None:
        """Initializes the step with the provided step information.

        :param step_info: The DaprStepInfo object to initialize the step with.
        :param parent_process_id: Optional parent process ID if one exists.
        :raises KernelException: If an error occurs during initialization.
        """
        pass

    @actormethod(name="start")
    async def prepare_incoming_messages(self) -> int:
        """Triggers the step to dequeue all pending messages and prepare for processing.

        :return: An integer indicating the number of messages prepared for processing.
        """
        pass

    @actormethod(name="run_once")
    async def process_incoming_messages(self) -> None:
        """Triggers the step to process all prepared messages."""
        pass

    @actormethod(name="to_dapr_step_info")
    async def to_dapr_step_info(self) -> "DaprStepInfo":
        """Builds the current state of the step into a DaprStepInfo.

        :return: An instance of DaprStepInfo representing the step's current state.
        """
        pass
