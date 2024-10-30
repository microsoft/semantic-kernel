# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from queue import Queue
from typing import Any, Type

from dapr.actor import Actor, ActorId, ActorProxy
from dapr.actor.runtime.context import ActorRuntimeContext
from pydantic import Field

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import (
    ProcessFunctionNotFoundException,
    ProcessTargetFunctionNameMismatchException,
)
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.message_buffer_actor import MessageBufferActor
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.dapr_runtime.message_buffer import MessageBuffer
from semantic_kernel.processes.dapr_runtime.step import Step
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_event import ProcessEvent
from semantic_kernel.processes.process_message import ProcessMessage
from semantic_kernel.processes.process_message_factory import ProcessMessageFactory
from semantic_kernel.processes.process_types import get_generic_state_type
from semantic_kernel.processes.step_utils import find_input_channels
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class StepActor(Actor, Step, KernelProcessMessageChannel, KernelBaseModel):
    """Represents a step actor that follows the Step abstract class."""

    kernel: Kernel
    parent_process_id: str | None = None
    step_info: DaprStepInfo | None = None
    initialize_task: bool | None = False
    event_namespace: str | None = None
    inner_step_type: Type | None = None
    incoming_messages: Queue = Field(default_factory=Queue)
    step_state: KernelProcessStepState | None = None
    step_state_type: Type | None = None
    output_edges: dict[str, list[KernelProcessEdge]] = Field(default_factory=dict)
    functions: dict[str, KernelFunction] = Field(default_factory=dict)
    inputs: dict[str, dict[str, Any | None]] = Field(default_factory=dict)
    initial_inputs: dict[str, dict[str, Any | None]] = Field(default_factory=dict)
    init_lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId, kernel: Kernel):
        """Initializes a new instance of StepActor."""
        super().__init__(ctx, actor_id)
        self.kernel = kernel
        self.activate_task = self.activate_step()

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        return self.step_info.state.name

    async def initialize_step(self, step_info: DaprStepInfo, parent_process_id: str | None = None) -> None:
        """Initializes the step with the provided step information."""
        if step_info is None:
            raise ValueError("step_info must not be None")

        if self.initialize_task:
            return

        await self._int_initialize_step(step_info, parent_process_id)

        await self._state_manager.add_or_update_state(ActorStateKeys.StepInfoState.value, step_info)
        await self._state_manager.add_or_update_state(ActorStateKeys.StepParentProcessId.value, parent_process_id)

    async def _int_initialize_step(self, step_info: DaprStepInfo, parent_process_id: str | None = None) -> None:
        """Internal method to initialize the step with the provided step information.

        Args:
            step_info: The DaprStepInfo object to initialize the step with.
            parent_process_id: Optional parent process ID if one exists.
        """
        # TODO(evmattso): investigate this
        self.inner_step_type = step_info.inner_step_python_type

        self.parent_process_id = parent_process_id
        self.step_info = step_info
        self.step_state = self.step_info.state
        self.output_edges = {k: v for k, v in step_info.edges.items()}
        self.event_namespace = f"{self.step_info.state.name}_{self.step_info.state.id}"

        self.initialize_task = True

    async def prepare_incoming_messages(self) -> int:
        """Triggers the step to dequeue all pending messages and prepare for processing.

        Returns:
            An integer indicating the number of messages prepared for processing.
        """
        message_queue: MessageBuffer = ActorProxy.create(
            actor_type=f"{MessageBufferActor.__name__}", actor_id=self.id.id, actor_interface=MessageBufferActor
        )
        incoming = await message_queue.dequeue_all()
        for message in incoming:
            self.incoming_messages.put(message)

        await self._state_manager.set_state(ActorStateKeys.StepIncomingMessagesState.value, self.incoming_messages)
        await self._state_manager.save_state()

        return len(self.incoming_messages)

    async def process_incoming_messages(self) -> None:
        """Triggers the step to process all prepared messages."""
        while not self.incoming_messages.empty():
            message = self.incoming_messages.get()
            await self.handle_message(message)

        await self._state_manager.set_state(ActorStateKeys.StepIncomingMessagesState.value, self.incoming_messages)
        await self._state_manager.save_state()

    async def activate_step(self):
        """Initializes the step."""
        # Instantiate an instance of the inner step object
        step_cls = self.inner_step_type

        step_instance: KernelProcessStep = step_cls()  # type: ignore

        kernel_plugin = self.kernel.add_plugin(
            step_instance, self.step_info.state.name if self.step_info.state else "default_name"
        )

        # Load the kernel functions
        for name, f in kernel_plugin.functions.items():
            self.functions[name] = f

        # Initialize the input channels
        self.initial_inputs = find_input_channels(channel=self, functions=self.functions)
        self.inputs = {k: {kk: vv for kk, vv in v.items()} if v else {} for k, v in self.initial_inputs.items()}

        # Use the existing state or create a new one if not provided
        state_object = self.step_info.state

        # Extract TState from inner_step_type
        t_state = get_generic_state_type(step_cls)

        if t_state is not None:
            # Create state_type as KernelProcessStepState[TState]
            state_type = KernelProcessStepState[t_state]

            if state_object is None:
                state_object = state_type(
                    name=step_cls.__name__,
                    id=step_cls.__name__,
                    state=None,
                )
            else:
                # Make sure state_object is an instance of state_type
                if not isinstance(state_object, KernelProcessStepState):
                    error_message = "State object is not of the expected type."
                    raise KernelException(error_message)

            # Make sure that state_object.state is not None
            if state_object.state is None:
                try:
                    state_object.state = t_state()
                except Exception as e:
                    error_message = f"Cannot instantiate state of type {t_state}: {e}"
                    raise KernelException(error_message)
        else:
            # The step has no user-defined state; use the base KernelProcessStepState
            state_type = KernelProcessStepState

            if state_object is None:
                state_object = state_type(
                    name=step_cls.__name__,
                    id=step_cls.__name__,
                    state=None,
                )

        if state_object is None:
            error_message = "The state object for the KernelProcessStep could not be created."
            raise KernelException(error_message)

        # Set the step state and activate the step with the state object
        self.step_state = state_object
        await step_instance.activate(state_object)

    async def handle_message(self, message: ProcessMessage):
        """Handles a LocalMessage that has been sent to the step."""
        if message is None:
            raise ValueError("The message is None.")

        if not self.initialize_task:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.initialize_task:
                    await self.activate_step()
                    self.initialize_task = True

        if self.functions is None or self.inputs is None or self.initial_inputs is None:
            raise ValueError("The step has not been initialized.")

        message_log_parameters = ", ".join(f"{k}: {v}" for k, v in message.values.items())
        logger.info(
            f"Received message from `{message.source_id}` targeting function "
            f"`{message.function_name}` and parameters `{message_log_parameters}`."
        )

        # Add the message values to the inputs for the function
        for k, v in message.values.items():
            if self.inputs.get(message.function_name) and self.inputs[message.function_name].get(k):
                logger.info(
                    f"Step {self.name} already has input for `{message.function_name}.{k}`, "
                    f"it is being overwritten with a message from Step named `{message.source_id}`."
                )

            if message.function_name not in self.inputs:
                self.inputs[message.function_name] = {}

            self.inputs[message.function_name][k] = v

        invocable_functions = [
            k
            for k, v in self.inputs.items()
            if v is not None and (v == {} or all(val is not None for val in v.values()))
        ]
        missing_keys = [
            f"{outer_key}.{inner_key}"
            for outer_key, outer_value in self.inputs.items()
            for inner_key, inner_value in outer_value.items()
            if inner_value is None
        ]

        if not invocable_functions:
            logger.info(f"No invocable functions, missing keys: {', '.join(missing_keys)}")
            return

        target_function = next((name for name in invocable_functions if name == message.function_name), None)

        if not target_function:
            raise ProcessTargetFunctionNameMismatchException(
                f"A message targeting function `{message.function_name}` has resulted in a different function "
                f"`{invocable_functions[0]}` becoming invocable. Check the function names."
            )

        logger.info(
            f"Step with Id '{self.id}' received all required input for function [{target_function}] and is executing."
        )

        # Concatenate all inputs and run the function
        arguments = self.inputs[target_function]
        function = self.functions.get(target_function)

        if function is None:
            raise ProcessFunctionNotFoundException(f"Function {target_function} not found in plugin {self.name}")

        invoke_result = None
        event_name = None
        event_value = None

        try:
            logger.info(
                f"Invoking plugin `{function.plugin_name}` and function `{function.name}` with arguments: {arguments}"
            )
            invoke_result = await self.invoke_function(function, self.kernel, arguments)
            event_name = f"{target_function}.OnResult"
            event_value = invoke_result.value

            state_dict = self.step_state.model_dump()
            await self._state_manager.set_state(ActorStateKeys.StepStateJson.value, state_dict)
            await self._state_manager.save_state()
        except Exception as ex:
            logger.error(f"Error in Step {self.name}: {ex!s}")
            event_name = f"{target_function}.OnError"
            event_value = str(ex)
        finally:
            await self.emit_event(KernelProcessEvent(id=event_name, data=event_value))

            # Reset the inputs for the function that was just executed
            self.inputs[target_function] = self.initial_inputs.get(target_function, {}).copy()

    async def invoke_function(self, function: "KernelFunction", kernel: "Kernel", arguments: dict[str, Any]):
        """Invokes the function."""
        return await kernel.invoke(function, **arguments)

    async def emit_event(self, process_event: KernelProcessEvent):
        """Emits an event from the step."""
        await self.emit_local_event(ProcessEvent.from_kernel_process_event(process_event, self.event_namespace))

    async def emit_process_event(self, dapr_event: ProcessEvent):
        """Emits an event from the step."""
        scoped_event = self.scoped_event(dapr_event)

        if dapr_event.visibility == KernelProcessEventVisibility.Public and self.parent_process_id is not None:
            parent_process: EventBufferActor = ActorProxy.create(
                actor_type=f"{EventBufferActor.__name__}",
                actor_id=self.parent_process_id,
                actor_interface=EventBufferActor,
            )
            await parent_process.enqueue(scoped_event)

        for edge in self.get_edge_for_event(dapr_event.id):
            message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, dapr_event.data)
            scoped_step_id = self._scoped_actor_id(ActorId(edge.output_target.step_id))
            target_step: MessageBuffer = ActorProxy.create(
                actor_id=scoped_step_id,
                actor_interface=MessageBuffer,
                actor_type=f"{MessageBuffer.__name__}",
            )
            await target_step.enqueue(message)

    async def to_dapr_step_info(self) -> DaprStepInfo:
        """Converts the step to a DaprStepInfo object."""
        if not self.initialize_task:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.initialize_task:
                    await self.activate_step()
                    self.initialize_task = True

        return DaprStepInfo(
            inner_step_python_type=self.inner_step_type, state=self.step_info.state, edges=self.step_info.edges
        )

    async def _on_activate(self) -> None:
        """Override the Actor's on_activate method."""
        has_value, existing_step_info = await self._state_manager.try_get_state(ActorStateKeys.StepInfoState.value)
        if has_value:
            parent_process_id = await self._state_manager.get_state(ActorStateKeys.StepParentProcessId.value)
            await self._int_initialize_step(existing_step_info, parent_process_id=parent_process_id)

            # Load persisted incoming messages
            exists, incoming_messages = await self._state_manager.try_get_state(
                ActorStateKeys.StepIncomingMessagesState.value
            )
            if exists:
                self.incoming_messages = incoming_messages

    def scoped_event(self, dapr_event: "ProcessEvent") -> "ProcessEvent":
        """Generates a scoped event for the step."""
        if dapr_event is None:
            raise ValueError("The Dapr event must be specified.")
        dapr_event.namespace = f"{self.name}_{self.id.id}"
        return dapr_event

    def _scoped_actor_id(self, actor_id: ActorId) -> ActorId:
        """Generates a scoped actor ID for the step."""
        return ActorId(f"{self.parent_process_id}.{actor_id.id}")

    def get_edge_for_event(self, event_id: str) -> list["KernelProcessEdge"]:
        """Retrieves all edges that are associated with the provided event Id."""
        if not self.output_edges:
            return []

        return self.output_edges.get(event_id, [])
