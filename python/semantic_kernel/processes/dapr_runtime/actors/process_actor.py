# Copyright (c) Microsoft. All rights reserved.


import asyncio
import contextlib
import uuid
from queue import Queue
from typing import Any

from dapr.actor import ActorId, ActorProxy
from dapr.actor.runtime.context import ActorRuntimeContext
from pydantic import Field

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.const import END_PROCESS_ID
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.external_event_buffer_actor import ExternalEventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.step_actor import StepActor
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.dapr_runtime.process import Process
from semantic_kernel.processes.dapr_runtime.step import Step
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.process_message import ProcessMessage


class ProcessActor(StepActor):
    """A local process that contains a collection of steps."""

    kernel: Kernel
    steps: list[Step] = Field(default_factory=list)
    step_infos: list[DaprStepInfo] = Field(default_factory=list)
    initialize_task: bool | None = False
    external_event_queue: Queue = Field(default_factory=Queue)
    process_task: asyncio.Task | None = None
    process: DaprProcessInfo | None = None

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId, kernel: Kernel) -> None:
        """Initializes the local process."""
        args: dict[str, Any] = {
            "ctx": ctx,
            "actor_id": actor_id,
            "kernel": kernel,
            "initialize_task": False,
        }

        super().__init__(**args)

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        if self.process.state.name is None:
            raise KernelException("The process must be initialized before accessing the name property.")
        return self.step_info.state.name

    async def initialize_process(self, process_info: DaprProcessInfo, parent_process_id: str | None = None) -> None:
        """Initializes the process."""
        if process_info is None:
            raise ValueError("The process info is not defined.")

        if process_info.steps is None:
            raise ValueError("The process info does not contain any steps.")

        if self.initialize_task:
            return

        await self.initialize_process_actor(process_info, parent_process_id)

        await self._state_manager.add_or_update_state(ActorStateKeys.ProcessInfoState.value, process_info)
        await self._state_manager.add_or_update_state(ActorStateKeys.StepParentProcessId.value, parent_process_id)
        await self._state_manager.add_or_update_state(ActorStateKeys.StepActivatedState.value, True)
        await self._state_manager.save_state()

    async def start(self, keep_alive: bool = True) -> None:
        """Starts the process."""
        if not self.initialize_task:
            raise ValueError("The process has not been initialized.")

        self.process_task = asyncio.create_task(self.internal_execute(keep_alive))

    async def run_once(self, process_event: KernelProcessEvent):
        """Starts the process with an initial event and waits for it to finish."""
        if process_event is None:
            raise ProcessEventUndefinedException("The process event must be specified.")
        external_event_queue: ExternalEventBufferActor = ActorProxy.create(
            actor_type=f"{ExternalEventBufferActor.__name__}",
            actor_id=self.parent_process_id,
            actor_interface=ExternalEventBufferActor,
        )
        external_event_queue.put(process_event)
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

    async def get_process_info(self):
        """Gets the process information."""
        return await self.to_dapr_process_info()

    # private async Task<DaprProcessInfo> ToDaprProcessInfoAsync()
    # {
    #     var processState = new KernelProcessState(this.Name, this.Id.GetId());
    #     var stepTasks = this._steps.Select(step => step.ToDaprStepInfoAsync()).ToList();
    #     var steps = await Task.WhenAll(stepTasks).ConfigureAwait(false);
    #     return new DaprProcessInfo { InnerStepDotnetType = this._process!.InnerStepDotnetType, Edges = this._process!.Edges, State = processState, Steps = steps.ToList() };
    # }

    async def to_dapr_process_info(self) -> DaprProcessInfo:
        """Converts the process to a Dapr process info."""
        process_state = DaprProcessInfo(self.name, self.id.id)
        step_tasks = [step.to_dapr_step_info() for step in self.steps]
        steps = await asyncio.gather(*step_tasks)
        return DaprProcessInfo(
            inner_step_dotnet_type=self.inner_step_type, edges=self.process.edges, state=process_state, steps=steps
        )

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
                await process_actor.initialize_process(step, self.id.id)
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
                    actor_type=f"{ProcessActor.__name__}",
                    actor_interface=Step,
                )
                await step_actor.initialize_step(step, self.id.id)

            # Add the local step to the list of steps
            self.steps.append(step_actor)

        self.initialize_task = True

    def _scoped_actor_id(self, actor_id: ActorId) -> ActorId:
        """Creates a scoped actor ID."""
        return ActorId(f"{self.id}.{actor_id.id}")

    async def internal_execute(self, max_supersteps: int = 100, keep_alive: bool = True):
        """Internal execution logic for the process."""
        message_channel: Queue[ProcessMessage] = Queue()

        try:
            for _ in range(max_supersteps):
                self.enqueue_external_messages(message_channel)
                for step in self.steps:
                    await self.enqueue_step_messages(step, message_channel)

                messages_to_process: list = []
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
            print("An error occurred while running the process: %s.", ex)
            raise
