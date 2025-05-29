# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import logging
import uuid
from collections.abc import Callable
from queue import Queue
from typing import TYPE_CHECKING, Any

from pydantic import Field

from semantic_kernel.exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.const import END_PROCESS_ID
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.local_runtime.local_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
    LocalEvent,
)
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.processes.local_runtime.local_message_factory import LocalMessageFactory
from semantic_kernel.processes.local_runtime.local_step import LocalStep
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class LocalProcess(LocalStep):
    """A local process that contains a collection of steps."""

    kernel: Kernel
    steps: list[LocalStep] = Field(default_factory=list)
    step_infos: list[KernelProcessStepInfo] = Field(default_factory=list)
    process: "KernelProcess"
    initialize_task: bool | None = False
    external_event_queue: Queue = Field(default_factory=Queue)
    process_task: asyncio.Task | None = None
    factories: dict[str, Callable] = Field(default_factory=dict)
    max_supersteps: int = Field(
        default=100, ge=1, description="Maximum number of supersteps to execute before stopping the process."
    )

    def __init__(
        self,
        process: "KernelProcess",
        kernel: Kernel,
        factories: dict[str, Callable] | None = None,
        parent_process_id: str | None = None,
        max_supersteps: int | None = None,
    ):
        """Initializes the local process."""
        args: dict[str, Any] = {
            "step_info": process,
            "kernel": kernel,
            "parent_process_id": parent_process_id,
            "step_infos": list(process.steps),
            "process": process,
            "initialize_task": False,
        }

        if max_supersteps is not None:
            args["max_supersteps"] = max_supersteps

        if factories:
            args["factories"] = factories

        super().__init__(**args)

    def ensure_initialized(self):
        """Ensures the process is initialized lazily (synchronously)."""
        if not self.initialize_task:
            self.initialize_process()
            self.initialize_task = True

    async def start(self, keep_alive: bool = True) -> None:
        """Starts the process with an initial event.

        Args:
            keep_alive: Indicates if the process should wait for external events after it's finished processing.
        """
        self.ensure_initialized()
        self.process_task = asyncio.create_task(
            self.internal_execute(max_supersteps=self.max_supersteps, keep_alive=keep_alive)
        )

    async def run_once(self, process_event: KernelProcessEvent):
        """Starts the process with an initial event and waits for it to finish.

        Args:
            process_event: The KernelProcessEvent to start the process with.
        """
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")
        self.external_event_queue.put(process_event)
        await self.start(keep_alive=False)
        if self.process_task:
            await self.process_task

    async def stop(self):
        """Stops a running process."""
        if not self.process_task or self.process_task.done():
            return  # Task is already finished or hasn't started

        self.process_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self.process_task

    async def initialize_step(self):
        """Initializes the step."""
        # The process does not need any further initialization
        pass

    async def send_message(self, process_event: KernelProcessEvent):
        """Sends a message to the process."""
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")
        self.external_event_queue.put(process_event)

    async def get_process_info(self) -> "KernelProcess":
        """Gets the process information."""
        return await self.to_kernel_process()

    def initialize_process(self):
        """Initializes the input and output edges for the process and initializes the steps."""
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

        # Initialize the input and output edges for the process
        self.output_edges = {kvp[0]: list(kvp[1]) for kvp in self.process.edges.items()}

        # Initialize the steps within this process
        for step in self.step_infos:
            local_step = None

            # The current step should already have a name.
            assert step.state and step.state.name is not None  # nosec

            if isinstance(step, KernelProcess):
                # The process will only have an Id if it's already been executed.
                if not step.state.id:
                    step.state.id = str(uuid.uuid4().hex)

                # Create a new LocalProcess for the step
                process = LocalProcess(
                    process=step,
                    kernel=self.kernel,
                    factories=self.factories,
                    parent_process_id=self.id,
                )

                local_step = process
            else:
                # The current step should already have an Id.
                assert step.state and step.state.id is not None  # nosec

                # Create a LocalStep for the step
                local_step = LocalStep(  # type: ignore
                    step_info=step,
                    kernel=self.kernel,
                    factories=self.factories,
                    parent_process_id=self.id,
                )

            # Add the local step to the list of steps
            self.steps.append(local_step)

    async def handle_message(self, message: LocalMessage):
        """Handles a LocalMessage that has been sent to the process."""
        if not message.target_event_id:
            error_message = (
                "Internal Process Error: The target event id must be specified when sending a message to a step."
            )
            logger.error(error_message)
            raise KernelException(error_message)

        event_id = message.target_event_id
        if event_id in self.output_edges:
            nested_event = KernelProcessEvent(
                id=event_id, data=message.target_event_data, visibility=KernelProcessEventVisibility.Internal
            )
            await self.run_once(nested_event)

    async def internal_execute(self, max_supersteps: int = 100, keep_alive: bool = True):
        """Internal execution logic for the process."""
        message_channel: Queue[LocalMessage] = Queue()

        logger.debug(f"Running process for {max_supersteps} supersteps.")

        try:
            for _ in range(max_supersteps):
                self.enqueue_external_messages(message_channel)
                for step in self.steps:
                    await self.enqueue_step_messages(step, message_channel)

                messages_to_process: list[LocalMessage] = []
                while not message_channel.empty():
                    messages_to_process.append(message_channel.get())

                if not messages_to_process and (not keep_alive or self.external_event_queue.empty()):
                    break

                message_tasks = []
                for message in messages_to_process:
                    if message.destination_id == END_PROCESS_ID:
                        break

                    destination_step = next(step for step in self.steps if step.id == message.destination_id)
                    message_tasks.append(destination_step.handle_message(message))

                await asyncio.gather(*message_tasks)

        except Exception as ex:
            logger.error(f"An error occurred while running the process: {ex}.")
            raise

    async def to_kernel_process(self) -> "KernelProcess":
        """Builds a KernelProcess from the current LocalProcess."""
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

        process_state = KernelProcessState(name=self.name, version=self.step_state.version, id=self.id)
        step_tasks = [step.to_kernel_process_step_info() for step in self.steps]
        steps = await asyncio.gather(*step_tasks)
        return KernelProcess(state=process_state, steps=steps, edges=self.output_edges)

    async def to_kernel_process_step_info(self) -> "KernelProcessStepInfo":
        """Extracts the current state of the step and returns it as a KernelProcessStepInfo."""
        return await self.to_kernel_process()

    def enqueue_external_messages(self, message_channel: Queue[LocalMessage]):
        """Processes external events that have been sent to the process."""
        while not self.external_event_queue.empty():
            external_event: KernelProcessEvent = self.external_event_queue.get_nowait()
            if external_event.id in self.output_edges:
                edges = self.output_edges[external_event.id]
                for edge in edges:
                    message = LocalMessageFactory.create_from_edge(edge, external_event.data)
                    message_channel.put(message)

    async def enqueue_step_messages(self, step: LocalStep, message_channel: Queue[LocalMessage]):
        """Processes events emitted by the given step and enqueues them."""
        all_step_events = step.get_all_events()
        for step_event in all_step_events:
            # must come first because emitting the step event modifies its namespace
            for edge in step.get_edge_for_event(step_event.id):
                message = LocalMessageFactory.create_from_edge(edge, step_event.data)
                message_channel.put(message)

            if step_event.visibility == KernelProcessEventVisibility.Public:
                if isinstance(step_event, KernelProcessEvent):
                    await self.emit_event(step_event)  # type: ignore
                elif isinstance(step_event, LocalEvent):
                    await self.emit_local_event(step_event)  # type: ignore

    def dispose(self):
        """Clean up resources."""
        if self.process_task:
            self.process_task.cancel()
