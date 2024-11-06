# Copyright (c) Microsoft. All rights reserved.


import asyncio
import contextlib
import json
import uuid
from queue import Queue

from dapr.actor import ActorId, ActorProxy
from pydantic import Field

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
from semantic_kernel.processes.dapr_runtime.external_event_buffer import ExternalEventBuffer
from semantic_kernel.processes.dapr_runtime.process import Process
from semantic_kernel.processes.dapr_runtime.step import Step
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.process_event import ProcessEvent
from semantic_kernel.processes.process_message import ProcessMessage
from semantic_kernel.processes.process_message_factory import ProcessMessageFactory


class ProcessActor(StepActor, Process):
    """A local process that contains a collection of steps."""

    kernel: Kernel | None = None
    _steps: list[StepActor] = []
    step_infos: list[DaprStepInfo] = Field(default_factory=list)
    initialize_task: bool | None = False
    external_event_queue: Queue = Field(default_factory=Queue)
    process_task: asyncio.Task | None = None
    process: DaprProcessInfo | None = None

    # def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId) -> None:
    #     """Initializes the local process."""
    #     args: dict[str, Any] = {
    #         "ctx": ctx,
    #         "actor_id": actor_id,
    #         # "kernel": kernel,
    #         "initialize_task": False,
    #     }

    #     super().__init__(**args)

    # def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId, **kwargs) -> None:
    #     """Initializes the local process."""
    #     # Initialize the Actor base class explicitly
    #     super(ProcessActor, self).__init__(ctx, actor_id)

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        if self.process.state.name is None:
            raise KernelException("The process must be initialized before accessing the name property.")
        return self.step_info.state.name

    # async def initialize_process(self, process_info: dict[str, Any], parent_process_id: str | None = None) -> None:
    async def initialize_process(self, input: dict) -> None:
        """Initializes the process."""
        if input is None:
            raise ValueError("The process info is not defined.")

        process_info = DaprProcessInfo.model_validate(input.get("process_info"))

        if process_info.steps is None:
            raise ValueError("The process info does not contain any steps.")

        if self.initialize_task:
            return

        await self._initialize_process_actor(process_info, input.get("parent_process_id"))

        try:
            await self._state_manager.try_add_state(ActorStateKeys.ProcessInfoState.value, process_info)
            await self._state_manager.try_add_state(
                ActorStateKeys.StepParentProcessId.value, input.get("parent_process_id")
            )
            await self._state_manager.try_add_state(ActorStateKeys.StepActivatedState.value, True)
            await self._state_manager.save_state()
        except Exception as ex:
            print(ex)
            raise ex

    async def start(self, keep_alive: bool = True) -> None:
        """Starts the process."""
        if not self.initialize_task:
            raise ValueError("The process has not been initialized.")

        self.process_task = asyncio.create_task(self.internal_execute(keep_alive=keep_alive))

    async def run_once(self, process_event_payload: str):
        """Starts the process with an initial event and waits for it to finish."""
        if process_event_payload is None:
            raise ProcessEventUndefinedException("The process event must be specified.")

        external_event_queue: ExternalEventBufferActor = ActorProxy.create(
            actor_type=f"{ExternalEventBufferActor.__name__}",
            actor_id=ActorId(self.id.id),
            actor_interface=ExternalEventBuffer,
        )
        try:
            await external_event_queue.enqueue(process_event_payload)
            await self.start(keep_alive=False)
            if self.process_task:
                await self.process_task
        except Exception as ex:
            print(ex)
            raise ex

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

    async def _on_activate(self) -> None:
        """Activates the process."""
        has_value, existing_process_info = await self._state_manager.try_get_state(
            ActorStateKeys.ProcessInfoState.value
        )
        if has_value:
            self.parent_process_id = await self._state_manager.get_state(ActorStateKeys.StepParentProcessId.value)
            await self._initialize_process_actor(existing_process_info, self.parent_process_id)

    async def send_message(self, process_event: KernelProcessEvent):
        """Sends a message to the process."""
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")
        self.external_event_queue.put(process_event)

    async def get_process_info(self):
        """Gets the process information."""
        return await self.to_dapr_process_info()

    async def to_dapr_process_info(self) -> DaprProcessInfo:
        """Converts the process to a Dapr process info."""
        process_state = DaprProcessInfo(self.name, self.id.id)
        step_tasks = [step.to_dapr_step_info() for step in self.steps]
        steps = await asyncio.gather(*step_tasks)
        return DaprProcessInfo(
            inner_step_dotnet_type=self.inner_step_type, edges=self.process.edges, state=process_state, steps=steps
        )

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
                await self.run_once(nested_event)

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
            step_actor: Step = None

            # The current step should already have a name.
            assert step.state and step.state.name is not None  # nosec

            if isinstance(step, DaprProcessInfo):
                # The process will only have an Id if it's already been executed.
                if not step.state.id:
                    step.state.id = str(uuid.uuid4().hex)

                # Initialize the step as a process
                scoped_process_id = self._scoped_actor_id(ActorId(step.state.id))
                process_actor: Process = ActorProxy.create(
                    actor_id=scoped_process_id,
                    actor_type=f"{ProcessActor.__name__}",
                    actor_interface=Process,
                )
                payload = {"process_info": step.model_dump(), "parent_process_id": self.id.id}
                await process_actor.initialize_process(payload)
                step_actor = ActorProxy.create(
                    actor_id=scoped_process_id,
                    actor_type=f"{ProcessActor.__name__}",
                    actor_interface=Step,
                )
            else:
                # The current step should already have an Id.
                assert step.state and step.state.id is not None  # nosec

                scoped_step_id = self._scoped_actor_id(ActorId(step.state.id))
                step_actor = ActorProxy.create(
                    actor_id=scoped_step_id,
                    actor_type=f"{StepActor.__name__}",
                    actor_interface=Step,
                )
                step_dict = step.model_dump()
                payload = {"step_info": step_dict, "parent_process_id": self.id.id}
                try:
                    await step_actor.initialize_step(json.dumps(payload))
                except Exception as ex:
                    print(ex)
                    raise ex

            # Add the local step to the list of steps
            self._steps.append(step_actor)

        self.initialize_task = True

    def _scoped_actor_id(self, actor_id: ActorId, scope_to_parent: bool = False) -> ActorId:
        """Creates a scoped actor ID."""
        if scope_to_parent and self.parent_process_id is None:
            raise ValueError("The parent process Id must be set before scoping to the parent process.")

        id = self.parent_process_id if scope_to_parent else self.id.id
        return ActorId(f"{id}.{actor_id.id}")

    async def internal_execute(self, max_supersteps: int = 100, keep_alive: bool = True):
        """Internal execution logic for the process."""
        try:
            for _ in range(max_supersteps):
                if await self._is_end_message_sent():
                    self.process_task.cancel()
                    break

                # Check for external events
                await self._enqueue_external_messages()

                # Reach out to all of the steps in the process and instrcut them to retrieve their pending
                # messages from their associated queues
                step_preparation_tasks = [step.prepare_incoming_messages() for step in self.steps]
                message_counts = await asyncio.gather(*step_preparation_tasks)

                if sum(message_counts) == 0 and (not keep_alive or self.external_event_queue.empty()):
                    self.process_task.cancel()
                    break

                # Process the incoming messages for each step
                step_processing_tasks = [step.process_incoming_messages() for step in self.steps]
                await asyncio.gather(*step_processing_tasks)

                # Handle public events that need to be bubbled out of the process
                await self.send_outgoing_public_events()

        except Exception as ex:
            print("An error occurred while running the process: %s.", ex)
            self.process_task.cancel()
            raise

    def _scoped_event(self, dapr_event: ProcessEvent):
        if dapr_event is None:
            raise ValueError("The Dapr event must be specified.")

        dapr_event.namespace = f"{self.name}_{self.process.state.id}"
        return dapr_event

    async def send_outgoing_public_events(self) -> None:
        """Sends outgoing public events."""
        if self.parent_process_id is not None:
            event_queue: EventBufferActor = ActorProxy.create(
                actor_id=ActorId(self.id.id),
                actor_type=f"{EventBufferActor.__name__}",
                actor_interface=EventBufferActor,
            )
            all_events: list[ProcessEvent] = await event_queue.dequeue_all()

            for e in all_events:
                scoped_event = self._scoped_event(e)
                if scoped_event.id in self.output_edges and self.output_edges[scoped_event.id] is not None:
                    for edge in self.output_edges[scoped_event.id]:
                        message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, e.data)
                        scoped_message_buffer_id = self._scoped_actor_id(
                            ActorId(edge.output_target.step_id), scope_to_parent=True
                        )
                        message_queue: MessageBufferActor = ActorProxy.create(
                            actor_id=scoped_message_buffer_id,
                            actor_type=f"{MessageBufferActor.__name__}",
                            actor_interface=MessageBufferActor,
                        )
                        await message_queue.enqueue(message)

    async def _is_end_message_sent(self) -> bool:
        """Checks if the end message has been sent."""
        scoped_message_buffer_id = self._scoped_actor_id(ActorId(END_PROCESS_ID))
        end_message_queue: MessageBufferActor = ActorProxy.create(
            actor_id=scoped_message_buffer_id,
            actor_type=f"{MessageBufferActor.__name__}",
            actor_interface=MessageBufferActor,
        )
        messages: list[ProcessMessage] = await end_message_queue.dequeue_all()
        return len(messages) > 0

    async def _enqueue_external_messages(self) -> None:
        """Enqueues external messages into the process."""
        external_event_queue: ExternalEventBufferActor = ActorProxy.create(
            actor_id=ActorId(self.id.id),
            actor_type=f"{ExternalEventBufferActor.__name__}",
            actor_interface=ExternalEventBufferActor,
        )

        external_events = await external_event_queue.dequeue_all()

        for external_event in external_events:
            if external_event.id in self.output_edges and self.output_edges[external_event.id] is not None:
                for edge in self.output_edges[external_event.id]:
                    message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, external_event.data)
                    scoped_message_buffer_id = self._scoped_actor_id(ActorId(edge.output_target.step_id))
                    message_queue: MessageBufferActor = ActorProxy.create(
                        actor_id=scoped_message_buffer_id,
                        actor_type=f"{MessageBufferActor.__name__}",
                        actor_interface=MessageBufferActor,
                    )
                    await message_queue.enqueue(message)
