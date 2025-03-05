# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod

from dapr.actor import ActorInterface, actormethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class StepInterface(ActorInterface, ABC):
    """Abstract base class for a step in the process workflow."""

    @abstractmethod
    @actormethod(name="initialize_step")
    async def initialize_step(self, input: str) -> None:
        """Initializes the step with the provided step information.

        Args:
            input: the DaprStepinfo and ParentProcessId dictionary as a str
        """
        ...

    @abstractmethod
    @actormethod(name="prepare_incoming_messages")
    async def prepare_incoming_messages(self) -> int:
        """Triggers the step to dequeue all pending messages and prepare for processing.

        Returns:
            The number of messages that were dequeued.
        """
        ...

    @abstractmethod
    @actormethod(name="process_incoming_messages")
    async def process_incoming_messages(self) -> None:
        """Triggers the step to process all prepared messages."""
        ...

    @abstractmethod
    @actormethod(name="to_dapr_step_info")
    async def to_dapr_step_info(self) -> str:
        """Builds the current state of the step into a DaprStepInfo.

        Returns:
            The DaprStepInfo representing the current state of the step.
        """
        ...
