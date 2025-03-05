# Copyright (c) Microsoft. All rights reserved.

import asyncio
import importlib
import json
import logging
from collections.abc import Callable
from inspect import isawaitable
from queue import Queue
from typing import Any

from dapr.actor import Actor, ActorId, ActorProxy
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import (
    ProcessFunctionNotFoundException,
    ProcessTargetFunctionNameMismatchException,
)
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.message_buffer_actor import MessageBufferActor
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.dapr_runtime.interfaces.event_buffer_interface import EventBufferInterface
from semantic_kernel.processes.dapr_runtime.interfaces.message_buffer_interface import MessageBufferInterface
from semantic_kernel.processes.dapr_runtime.interfaces.step_interface import StepInterface
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
from semantic_kernel.processes.step_utils import find_input_channels, get_fully_qualified_name
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class StepActor(Actor, StepInterface, KernelProcessMessageChannel):
    """Represents a step actor that follows the Step abstract class."""

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId, kernel: Kernel, factories: dict[str, Callable]):
        """Initializes a new instance of StepActor.

        Args:
            ctx: The actor runtime context.
            actor_id: The unique ID for the actor.
            kernel: The Kernel dependency to be injected.
            factories: The factory dictionary to use for creating the step.
        """
        super().__init__(ctx, actor_id)
        self.kernel = kernel
        self.factories: dict[str, Callable] = factories
        self.parent_process_id: str | None = None
        self.step_info: DaprStepInfo | None = None
        self.initialize_task: bool | None = False
        self.event_namespace: str | None = None
        self.inner_step_type: str | None = None
        self.incoming_messages: Queue = Queue()
        self.step_state: KernelProcessStepState | None = None
        self.step_state_type: type | None = None
        self.output_edges: dict[str, list[KernelProcessEdge]] = {}
        self.functions: dict[str, KernelFunction] = {}
        self.inputs: dict[str, dict[str, Any | None]] = {}
        self.initial_inputs: dict[str, dict[str, Any | None]] = {}
        self.init_lock: asyncio.Lock = asyncio.Lock()
        self.step_activated: bool = False

    @property
    def name(self) -> str:
        """Gets the name of the step."""
        if self.step_info is None or self.step_info.state is None or self.step_info.state.name is None:
            error_message = "The step must be initialized before accessing the name property."
            logger.error(error_message)
            raise KernelException(error_message)
        return self.step_info.state.name

    async def initialize_step(self, input: str) -> None:
        """Initializes the step with the provided step information."""
        if input is None:
            raise ValueError("step_info must not be None")

        if self.initialize_task:
            return

        try:
            input_dict: dict[str, Any] = json.loads(input)
        except (json.JSONDecodeError, TypeError):
            raise ValueError("Input must be a valid JSON string representing a dictionary")

        step_info = DaprStepInfo.model_validate(input_dict.get("step_info"))

        await self._int_initialize_step(step_info, input_dict.get("parent_process_id"))

        try:
            await self._state_manager.try_add_state(ActorStateKeys.StepInfoState.value, step_info)
            await self._state_manager.try_add_state(
                ActorStateKeys.StepParentProcessId.value, input_dict.get("parent_process_id")
            )
            await self._state_manager.save_state()
        except Exception as ex:
            logger.error(f"Error in Step {self.name}: {ex!s}")
            raise ex

    async def _int_initialize_step(self, step_info: DaprStepInfo, parent_process_id: str | None = None) -> None:
        """Internal method to initialize the step with the provided step information.

        Args:
            step_info: The DaprStepInfo object to initialize the step with.
            parent_process_id: Optional parent process ID if one exists.
        """
        self.inner_step_type = step_info.inner_step_python_type

        self.parent_process_id = parent_process_id
        self.step_info = step_info
        self.step_state = self.step_info.state
        self.output_edges = {k: v for k, v in step_info.edges.items()}
        self.event_namespace = f"{self.step_info.state.name}_{self.step_info.state.id}"

        self.initialize_task = True

    async def prepare_incoming_messages(self) -> int:
        """Prepares the incoming messages for processing."""
        try:
            message_queue: MessageBufferInterface = ActorProxy.create(  # type: ignore
                actor_type=f"{MessageBufferActor.__name__}",
                actor_id=ActorId(self.id.id),
                actor_interface=MessageBufferInterface,
            )
            incoming = await message_queue.dequeue_all()

            messages = []
            for message in incoming:
                process_message = ProcessMessage.model_validate(json.loads(message))
                messages.append(process_message)

            for msg in messages:
                self.incoming_messages.put(msg)

            await self._state_manager.try_add_state(
                ActorStateKeys.StepIncomingMessagesState.value,
                incoming,
            )
            await self._state_manager.save_state()

            return self.incoming_messages.qsize() if self.incoming_messages else 0
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in prepare_incoming_messages: {error_message}")
            raise Exception(error_message)

    async def process_incoming_messages(self):
        """Processes the incoming messages for the step."""
        while not self.incoming_messages.empty():
            message = self.incoming_messages.get()
            await self.handle_message(message)

        messages_to_save = [json.dumps(msg.model_dump()) for msg in list(self.incoming_messages.queue)]
        await self._state_manager.try_add_state(ActorStateKeys.StepIncomingMessagesState.value, messages_to_save)
        await self._state_manager.save_state()

    def _get_class_from_string(self, full_class_name: str):
        """Gets a class from a string."""
        module_name, class_name = full_class_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    async def activate_step(self):
        """Initializes the step."""
        # Instantiate an instance of the inner step object and retrieve its class reference.
        if self.factories and self.inner_step_type in self.factories:
            step_object = self.factories[self.inner_step_type]()
            if isawaitable(step_object):
                step_object = await step_object
            step_cls = step_object.__class__
            step_instance: KernelProcessStep = step_object  # type: ignore
        else:
            step_cls = self._get_class_from_string(self.inner_step_type)
            step_instance: KernelProcessStep = step_cls()  # type: ignore

        kernel_plugin = self.kernel.add_plugin(
            step_instance,
            self.step_info.state.name if self.step_info.state else "default_name",
        )

        # Load the kernel functions.
        for name, f in kernel_plugin.functions.items():
            self.functions[name] = f

        # Initialize the input channels.
        self.initial_inputs = find_input_channels(channel=self, functions=self.functions)
        self.inputs = {k: {kk: vv for kk, vv in v.items()} if v else {} for k, v in self.initial_inputs.items()}

        # Use the existing state or create a new one if not provided.
        state_object = self.step_info.state

        # Extract TState from inner_step_type using the class reference.
        t_state = get_generic_state_type(step_cls)

        if t_state is not None:
            # Create state_type as KernelProcessStepState[TState].
            state_type = KernelProcessStepState[t_state]

            if state_object is None:
                state_object = state_type(
                    name=step_cls.__name__,
                    id=step_cls.__name__,
                    state=None,
                )
            else:
                # Ensure that state_object is an instance of the expected type.
                if not isinstance(state_object, KernelProcessStepState):
                    error_message = "State object is not of the expected type."
                    raise KernelException(error_message)

                await self._state_manager.try_add_state(
                    ActorStateKeys.StepStateType.value,
                    get_fully_qualified_name(t_state),
                )
                await self._state_manager.try_add_state(
                    ActorStateKeys.StepStateJson.value,
                    json.dumps(state_object.model_dump()),
                )
                await self._state_manager.save_state()

            # Initialize state_object.state if it is not already set.
            if state_object.state is None:
                try:
                    state_object.state = t_state()
                except Exception as e:
                    error_message = f"Cannot instantiate state of type {t_state}: {e}"
                    raise KernelException(error_message)
        else:
            # The step has no user-defined state; use the base KernelProcessStepState.
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

        # Set the step state and activate the step with the state object.
        self.step_state = state_object
        await step_instance.activate(state_object)

    async def handle_message(self, message: ProcessMessage):
        """Handles a LocalMessage that has been sent to the step."""
        if message is None:
            raise ValueError("The message is None.")

        logger.info(f"Received message from `{message.source_id}` targeting function `{message.function_name}`.")

        if not self.step_activated:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.step_activated:
                    await self.activate_step()
                    self.step_activated = True

        if self.functions is None or self.inputs is None or self.initial_inputs is None:
            logger.error(f"The step `{self.name}` has not been initialized.")
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
        event_name: str = ""
        event_value = None

        try:
            logger.info(
                f"Invoking plugin `{function.plugin_name}` and function `{function.name}` with arguments: {arguments}"
            )
            invoke_result = await self.invoke_function(function, self.kernel, arguments)
            if invoke_result is None:
                raise KernelException(f"Function {target_function} returned None.")
            event_name = f"{target_function}.OnResult"
            event_value = invoke_result.value

            if self.step_state is not None:
                state_dict = self.step_state.model_dump()
                await self._state_manager.set_state(ActorStateKeys.StepStateJson.value, json.dumps(state_dict))
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
        if self.event_namespace is None:
            raise ValueError("The event namespace must be initialized before emitting an event.")

        await self.emit_process_event(ProcessEvent(inner_event=process_event, namespace=self.event_namespace))

    async def emit_process_event(self, dapr_event: ProcessEvent):
        """Emits an event from the step."""
        if dapr_event.visibility == KernelProcessEventVisibility.Public and self.parent_process_id is not None:
            parent_process: EventBufferActor = ActorProxy.create(  # type: ignore
                actor_type=f"{EventBufferActor.__name__}",
                actor_id=ActorId(self.parent_process_id),
                actor_interface=EventBufferInterface,
            )
            await parent_process.enqueue(dapr_event.model_dump_json())

        for edge in self.get_edge_for_event(dapr_event.id):
            message: ProcessMessage = ProcessMessageFactory.create_from_edge(edge, dapr_event.data)
            scoped_step_id = self._scoped_actor_id(ActorId(edge.output_target.step_id))
            target_step: MessageBufferInterface = ActorProxy.create(  # type: ignore
                actor_type=f"{MessageBufferActor.__name__}",
                actor_id=scoped_step_id,
                actor_interface=MessageBufferInterface,
            )
            await target_step.enqueue(message.model_dump_json())

    async def to_dapr_step_info(self) -> dict:
        """Converts the step to a DaprStepInfo object."""
        if not self.step_activated:
            async with self.init_lock:
                # Second check to ensure that initialization happens only once
                # This avoids a race condition where multiple coroutines might
                # reach the first check at the same time before any of them acquire the lock.
                if not self.step_activated:
                    await self.activate_step()
                    self.step_activated = True

        if self.step_info is None:
            raise ValueError("The step must be initialized before converting to DaprStepInfo.")

        if self.inner_step_type is None:
            raise ValueError("The inner step type must be initialized before converting to DaprStepInfo.")

        if self.step_state is not None:
            self.step_info.state = self.step_state

        step_info = DaprStepInfo(
            inner_step_python_type=self.inner_step_type,
            state=self.step_info.state,
            edges=self.step_info.edges,
        )

        return step_info.model_dump()

    async def _on_activate(self) -> None:
        """Override the Actor's on_activate method."""
        try:
            has_value, existing_step_info = await self._state_manager.try_get_state(ActorStateKeys.StepInfoState.value)
        except Exception as ex:
            logger.error(f"Error in Step {self.name}: {ex!s}")
            raise ex
        if has_value:
            parent_process_id = await self._state_manager.get_state(ActorStateKeys.StepParentProcessId.value)
            step_info = DaprStepInfo.model_validate(json.loads(existing_step_info))  # type: ignore
            await self._int_initialize_step(step_info, parent_process_id=parent_process_id)

            # Load persisted incoming messages
            has_value, incoming_messages = await self._state_manager.try_get_state(
                ActorStateKeys.StepIncomingMessagesState.value
            )
            if has_value:
                messages = json.loads(incoming_messages)  # type: ignore
                for msg in messages:
                    process_message = ProcessMessage.model_validate(json.loads(msg))
                    self.incoming_messages.put(process_message)

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
