# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import uuid
from queue import Queue
from typing import Any

from pydantic import Field, model_validator

from semantic_kernel import Kernel
from semantic_kernel.exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import (
    ProcessFunctionNotFoundException,
    ProcessTargetFunctionNameMismatchException,
)
from semantic_kernel.functions import KernelFunction
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import LocalEvent
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.processes.process_types import get_generic_state_type
from semantic_kernel.processes.step_utils import find_input_channels
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class LocalStep(KernelProcessMessageChannel, KernelBaseModel):
    """A local step that is part of a local process."""

    kernel: "Kernel"
    step_info: "KernelProcessStepInfo"
    outgoing_event_queue: Queue[LocalEvent] = Field(default_factory=Queue)
    initialize_task: bool | None = False
    event_namespace: str
    step_state: KernelProcessStepState
    inputs: dict[str, dict[str, Any | None]] = Field(default_factory=dict)
    initial_inputs: dict[str, dict[str, Any | None]] = Field(default_factory=dict)
    functions: dict[str, KernelFunction] = Field(default_factory=dict)
    output_edges: dict[str, list[KernelProcessEdge]] = Field(default_factory=dict)
    parent_process_id: str | None = None
    init_lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def parse_initial_configuration(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Parses the initial configuration of the step."""
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

        step_info = data.get("step_info")
        assert step_info is not None  # nosec

        if step_info and isinstance(step_info, KernelProcess) and step_info.state.id is None:
            step_info.state.id = str(uuid.uuid4().hex)

        data["step_state"] = step_info.state
        data["output_edges"] = {k: v for k, v in step_info.edges.items()}
        data["event_namespace"] = f"{step_info.state.name}_{step_info.state.id}"

        return data

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        return self.step_info.state.name

    @property
    def id(self) -> str:
        """Gets the ID of the step."""
        return self.step_info.state.id if self.step_info.state.id else ""

    async def handle_message(self, message: LocalMessage):
        """Handles a LocalMessage that has been sent to the step."""
        if message is None:
            raise ValueError("The message is None.")

        if not self.initialize_task:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.initialize_task:
                    await self.initialize_step()
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
        await self.emit_local_event(LocalEvent.from_kernel_process_event(process_event, self.event_namespace))

    async def emit_local_event(self, local_event: "LocalEvent"):
        """Emits an event from the step."""
        scoped_event = self.scoped_event(local_event)
        self.outgoing_event_queue.put(scoped_event)

    async def initialize_step(self):
        """Initializes the step."""
        # Instantiate an instance of the inner step object
        step_cls = self.step_info.inner_step_type

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

    def get_all_events(self) -> list["LocalEvent"]:
        """Retrieves all events that have been emitted by this step in the previous superstep."""
        all_events = []
        while not self.outgoing_event_queue.empty():
            all_events.append(self.outgoing_event_queue.get())
        return all_events

    def get_edge_for_event(self, event_id: str) -> list["KernelProcessEdge"]:
        """Retrieves all edges that are associated with the provided event Id."""
        if not self.output_edges:
            return []

        return self.output_edges.get(event_id, [])

    async def to_kernel_process_step_info(self) -> "KernelProcessStepInfo":
        """Extracts the current state of the step and returns it as a KernelProcessStepInfo."""
        if not self.initialize_task:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.initialize_task:
                    await self.initialize_step()
                    self.initialize_task = True

        return KernelProcessStepInfo(
            inner_step_type=self.step_info.inner_step_type, state=self.step_state, output_edges=self.output_edges
        )

    def scoped_event(self, local_event: "LocalEvent") -> "LocalEvent":
        """Generates a scoped event for the step."""
        if local_event is None:
            raise ValueError("The local event must be specified.")
        local_event.namespace = f"{self.name}_{self.id}"
        return local_event

    def scoped_event_from_kernel_process(self, process_event: "KernelProcessEvent") -> "LocalEvent":
        """Generates a scoped event for the step from a KernelProcessEvent."""
        if process_event is None:
            raise ValueError("The process event must be specified.")
        return LocalEvent.from_kernel_process_event(process_event, f"{self.name}_{self.id}")
