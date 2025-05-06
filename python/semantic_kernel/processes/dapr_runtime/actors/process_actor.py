# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import Callable, MutableSequence
from queue import Queue
from typing import Any

from dapr.actor import ActorId, ActorProxy
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.const import END_PROCESS_ID
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.external_event_buffer_actor import ExternalEventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.message_buffer_actor import MessageBufferActor
from semantic_kernel.processes.dapr_runtime.actors.step_actor import StepActor
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.dapr_runtime.interfaces.event_buffer_interface import EventBufferInterface
from semantic_kernel.processes.dapr_runtime.interfaces.external_event_buffer_interface import (
    ExternalEventBufferInterface,
)
from semantic_kernel.processes.dapr_runtime.interfaces.message_buffer_interface import MessageBufferInterface
from semantic_kernel.processes.dapr_runtime.interfaces.process_interface import ProcessInterface
from semantic_kernel.processes.dapr_runtime.interfaces.step_interface import StepInterface
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.process_event import ProcessEvent
from semantic_kernel.processes.process_message import ProcessMessage
from semantic_kernel.processes.process_message_factory import ProcessMessageFactory
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class ProcessActor(StepActor, ProcessInterface):
    """A local process that contains a collection of steps."""

    max_supersteps: int = 100

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId, kernel: Kernel, factories: dict[str, Callable]):
        """Initializes a new instance of ProcessActor.

        Args:
            ctx: The actor runtime context.
            actor_id: The unique ID for the actor.
            kernel: The Kernel dependency to be injected.
            factories: The factory dictionary that contains step types to factory methods.
        """
        super().__init__(ctx, actor_id, kernel, factories)
        self.kernel = kernel
        self.factories = factories
        self.steps: MutableSequence[StepInterface] = []
        self.step_infos: MutableSequence[DaprStepInfo] = []
        self.initialize_task: bool | None = False
        self.external_event_queue: Queue = Queue()
        self.process_task: asyncio.Task | None = None
        self.process: DaprProcessInfo | None = None

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        if self.process is None or self.process.state is None or self.process.state.name is None:
            error_message = "The process must be initialized before accessing the name property."
            logger.error(error_message)
            raise KernelException(error_message)
        return self.process.state.name

    async def initialize_process(self, input: dict | str) -> None:
        """Initializes the process."""
        if isinstance(input, str):
            input = json.loads(input)

        if not isinstance(input, dict):
            raise TypeError("input must be a JSON string or a dictionary")

        process_info_data = input.get("process_info")
        parent_process_id = input.get("parent_process_id")
        max_supersteps = input.get("max_supersteps", None)

        if process_info_data is None:
            raise ValueError("The process info is not defined.")

        if max_supersteps is not None:
            self.max_supersteps = max_supersteps

        if isinstance(process_info_data, str):
            process_info_dict = json.loads(process_info_data)
        elif isinstance(process_info_data, dict):
            process_info_dict = process_info_data
        else:
            raise TypeError("process_info must be a JSON string or a dictionary")

        dapr_process_info = DaprProcessInfo.model_validate(process_info_dict)

        if dapr_process_info.steps is None:
            raise ValueError("The process info does not contain any steps.")

        if self.initialize_task:
            return

        await self._initialize_process_actor(dapr_process_info, parent_process_id)

        try:
            # Serialize dapr_process_info before saving
            process_info_serialized = dapr_process_info.model_dump()

            await self._state_manager.try_add_state(ActorStateKeys.ProcessInfoState.value, process_info_serialized)
            await self._state_manager.try_add_state(
                ActorStateKeys.StepParentProcessId.value, parent_process_id if parent_process_id else ""
            )
            await self._state_manager.try_add_state(ActorStateKeys.StepActivatedState.value, True)
            await self._state_manager.save_state()

            logger.info(f"Initialized process for: {dapr_process_info} and parent process ID: {parent_process_id}")
        except Exception as ex:
            error_message = str(ex)
            logger.error(f"Error in initialize_process: {error_message}")
            raise Exception(error_message)

    async def start(self, keep_alive: bool = True) -> None:
        """Starts the process."""
        if not self.initialize_task:
            raise ValueError("The process has not been initialized.")

        # Only create the task if it doesn't already exist or is not running
        if not self.process_task or self.process_task.done():
            self.process_task = asyncio.create_task(
                self.internal_execute(max_supersteps=self.max_supersteps, keep_alive=keep_alive)
            )

    async def run_once(self, process_event: KernelProcessEvent | str | None) -> None:
        """Starts the process with an initial event and waits for it to finish.

        Args:
            process_event: The initial event to start the process represented as a string of a KernelProcessEvent
        """
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")

        external_event_queue: ExternalEventBufferActor = ActorProxy.create(  # type: ignore
            actor_type=f"{ExternalEventBufferActor.__name__}",
            actor_id=ActorId(self.id.id),
            actor_interface=ExternalEventBufferInterface,
        )
        try:
            await external_event_queue.enqueue(
                process_event.model_dump_json() if isinstance(process_event, KernelProcessEvent) else process_event
            )

            logger.info(f"Run once for process event: {process_event}")

            await self.start(keep_alive=False)
            if self.process_task:
                try:
                    await self.process_task
                except asyncio.CancelledError:
                    logger.error("Process task was cancelled")
        except Exception as ex:
            logger.error(f"Error in run_once: {ex}")
            raise ex

    async def stop(self):
        """Stops a running process."""
        if not self.process_task or self.process_task.done():
            return  # Task is already finished or hasn't started

        self.process_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self.process_task

    async def initialize_step(self, input: str) -> None:
        """Initializes the step."""
        # The process does not need any further initialization
        pass

    async def activate_step(self):
        """Overrides the step's activate_step method."""
        # The process does not need any further initialization
        pass

    async def _on_activate(self) -> None:
        """Called when the actor is activated."""
        try:
            has_value, existing_process_info = await self._state_manager.try_get_state(
                ActorStateKeys.ProcessInfoState.value
            )
            if has_value and existing_process_info:
                has_value, parent_process_id = await self._state_manager.try_get_state(
                    ActorStateKeys.StepParentProcessId.value
                )
                combined_input = {
                    "process_info": existing_process_info,
                    "parent_process_id": parent_process_id,
                }
                await self.initialize_process(combined_input)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in _on_activate: {error_message}")
            raise Exception(error_message)

    async def send_message(self, process_event: KernelProcessEvent):
        """Sends a message to the process."""
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")
        self.external_event_queue.put(process_event)

    async def get_process_info(self) -> dict:
        """Gets the process information."""
        return await self.to_dapr_process_info()

    async def to_dapr_process_info(self) -> dict:
        """Converts the process to a Dapr process info."""
        if self.process is None:
            raise ValueError("The process must be initialized before converting to DaprProcessInfo.")
        if self.process.inner_step_python_type is None:
            raise ValueError("The inner step type must be defined before converting to DaprProcessInfo.")

        process_state = KernelProcessState(name=self.name, version=self.process.state.version, id=self.id.id)

        step_tasks = [step.to_dapr_step_info() for step in self.steps]
        steps_as_dicts = await asyncio.gather(*step_tasks)

        dapr_process_info = DaprProcessInfo(
            inner_step_python_type=self.process.inner_step_python_type,
            edges=self.process.edges,
            state=process_state,
            steps=steps_as_dicts,
        )
        return dapr_process_info.model_dump()

    async def handle_message(self, message: ProcessMessage) -> None:
        """Handles a message."""
        if message.target_event_id is None:
            raise KernelException(
                "Internal Process Error: The target event id must be specified when sending a message to a step."
            )

        event_id = message.target_event_id
        if event_id in self.output_edges and self.output_edges[event_id] is not None:
            for _ in self.output_edges[event_id]:
                nested_event = KernelProcessEvent(
                    id=event_id, data=message.target_event_data, visibility=KernelProcessEventVisibility.Internal
                )
                await self.run_once(nested_event.model_dump_json())

    async def _initialize_process_actor(
        self, process_info: DaprProcessInfo, parent_process_id: str | None = None
    ) -> None:
        """Initializes the process actor."""
        if process_info is None:
            raise ValueError("The process info is not defined.")

        if process_info.steps is None:
            raise ValueError("The process info does not contain any steps.")

        self.parent_process_id = parent_process_id
        self.process = process_info
        self.step_infos = list(self.process.steps)
        self.output_edges = {kvp[0]: list(kvp[1]) for kvp in self.process.edges.items()}

        for step in self.step_infos:
            step_actor: StepInterface | None = None

            # The current step should already have a name.
            assert step.state and step.state.name is not None  # nosec

            if isinstance(step, DaprProcessInfo):
                # The process will only have an Id if it's already been executed.
                if not step.state.id:
                    step.state.id = str(uuid.uuid4().hex)

                # Initialize the step as a process
                scoped_process_id = self._scoped_actor_id(ActorId(step.state.id))
                process_actor: ProcessInterface = ActorProxy.create(  # type: ignore
                    actor_type=f"{ProcessActor.__name__}",
                    actor_id=scoped_process_id,
                    actor_interface=ProcessInterface,
                )
                process_payload: dict[str, Any] = {
                    "process_info": step.model_dump_json(),
                    "parent_process_id": self.id.id,
                }
                await process_actor.initialize_process(process_payload)
                step_actor = ActorProxy.create(  # type: ignore
                    actor_type=f"{ProcessActor.__name__}",
                    actor_id=scoped_process_id,
                    actor_interface=StepInterface,
                )
            else:
                # The current step should already have an Id.
                assert step.state and step.state.id is not None  # nosec

                scoped_step_id = self._scoped_actor_id(ActorId(step.state.id))
                step_actor = ActorProxy.create(  # type: ignore
                    actor_type=f"{StepActor.__name__}",
                    actor_id=scoped_step_id,
                    actor_interface=StepInterface,
                )
                assert step_actor is not None  # nosec
                step_dict = step.model_dump()
                step_payload: dict[str, Any] = {"step_info": step_dict, "parent_process_id": self.id.id}
                try:
                    await step_actor.initialize_step(json.dumps(step_payload))
                except Exception as ex:
                    logger.error(f"Error initializing ProcessActor step: {ex}")
                    raise ex

            # Add the local step to the list of steps
            self.steps.append(step_actor)  # type: ignore

        self.initialize_task = True

    def _scoped_actor_id(self, actor_id: ActorId, scope_to_parent: bool = False) -> ActorId:
        """Creates a scoped actor ID."""
        if scope_to_parent and self.parent_process_id is None:
            raise ValueError("The parent process Id must be set before scoping to the parent process.")

        id = self.parent_process_id if scope_to_parent else self.id.id
        return ActorId(f"{id}.{actor_id.id}")

    async def internal_execute(self, max_supersteps: int = 100, keep_alive: bool = True):
        """Internal execution logic for the process."""
        logger.debug(f"Running process for {max_supersteps} supersteps.")

        try:
            for _ in range(max_supersteps):
                if await self._is_end_message_sent():
                    # Exit the loop without cancelling the task
                    break

                # Check for external events
                await self._enqueue_external_messages()

                # Prepare incoming messages for each step
                step_preparation_tasks = [step.prepare_incoming_messages() for step in self.steps]
                message_counts = await asyncio.gather(*step_preparation_tasks)

                if sum(message_counts) == 0 and (not keep_alive or self.external_event_queue.empty()):
                    # Exit the loop without cancelling the task
                    break

                # Process the incoming messages for each step
                step_processing_tasks = [step.process_incoming_messages() for step in self.steps]
                await asyncio.gather(*step_processing_tasks)

                # Handle public events
                await self.send_outgoing_public_events()

        except Exception as ex:
            logger.error(f"An error occurred while running the process: {ex}")
            raise

    def _scoped_event(self, dapr_event: ProcessEvent):
        if dapr_event is None:
            raise ValueError("The Dapr event must be specified.")

        if self.process is None or self.process.state is None:
            raise ValueError("The process must be initialized before scoping the event.")

        dapr_event.namespace = f"{self.name}_{self.process.state.id}"
        return dapr_event

    async def send_outgoing_public_events(self) -> None:
        """Sends outgoing public events."""
        if self.parent_process_id is not None:
            event_queue: EventBufferActor = ActorProxy.create(  # type: ignore
                actor_type=f"{EventBufferActor.__name__}",
                actor_id=ActorId(self.id.id),
                actor_interface=EventBufferInterface,
            )
            all_events: list[str] = await event_queue.dequeue_all()

            process_events = [ProcessEvent.model_validate(json.loads(e)) for e in all_events]

            for e in process_events:
                scoped_event = self._scoped_event(e)
                if scoped_event.id in self.output_edges and self.output_edges[scoped_event.id] is not None:
                    for edge in self.output_edges[scoped_event.id]:
                        message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, e.data)
                        scoped_message_buffer_id = self._scoped_actor_id(
                            ActorId(edge.output_target.step_id), scope_to_parent=True
                        )
                        message_queue: MessageBufferActor = ActorProxy.create(  # type: ignore
                            actor_id=scoped_message_buffer_id,
                            actor_type=f"{MessageBufferActor.__name__}",
                            actor_interface=MessageBufferInterface,
                        )

                        message_json = json.dumps(message.model_dump())

                        logger.info(f"Enqueueing message: {message_json}")

                        await message_queue.enqueue(message_json)

    async def _is_end_message_sent(self) -> bool:
        """Checks if the end message has been sent."""
        scoped_message_buffer_id = self._scoped_actor_id(ActorId(END_PROCESS_ID))
        end_message_queue: MessageBufferActor = ActorProxy.create(  # type: ignore
            actor_type=f"{MessageBufferActor.__name__}",
            actor_id=scoped_message_buffer_id,
            actor_interface=MessageBufferInterface,
        )
        messages: list[str] = await end_message_queue.dequeue_all()

        logger.info(f"End message sent: {len(messages) > 0}")

        return len(messages) > 0

    async def _enqueue_external_messages(self) -> None:
        """Enqueues external messages into the process."""
        external_event_queue: ExternalEventBufferActor = ActorProxy.create(  # type: ignore
            actor_type=f"{ExternalEventBufferActor.__name__}",
            actor_id=ActorId(self.id.id),
            actor_interface=ExternalEventBufferInterface,
        )

        external_events_json = await external_event_queue.dequeue_all()

        logger.info(f"External events dequeued: {len(external_events_json)} with json: {external_events_json}")

        external_events = [KernelProcessEvent.model_validate(json.loads(e)) for e in external_events_json]

        for external_event in external_events:
            if external_event.id in self.output_edges and self.output_edges[external_event.id] is not None:
                for edge in self.output_edges[external_event.id]:
                    message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, external_event.data)
                    scoped_message_buffer_id = self._scoped_actor_id(ActorId(edge.output_target.step_id))
                    message_queue: MessageBufferActor = ActorProxy.create(  # type: ignore
                        actor_type=f"{MessageBufferActor.__name__}",
                        actor_id=scoped_message_buffer_id,
                        actor_interface=MessageBufferInterface,
                    )
                    message_json = json.dumps(message.model_dump())

                    logger.info(f"Enqueueing message: {message_json}")

                    await message_queue.enqueue(message_json)
