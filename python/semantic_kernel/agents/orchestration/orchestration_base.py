# Copyright (c) Microsoft. All rights reserved.

import asyncio
import inspect
import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Generic, Union, get_args

from pydantic import Field
from typing_extensions import TypeVar

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)


DefaultTypeAlias = Union[ChatMessageContent, list[ChatMessageContent]]

TIn = TypeVar("TIn", default=DefaultTypeAlias)
TOut = TypeVar("TOut", default=DefaultTypeAlias)


class OrchestrationResult(KernelBaseModel, Generic[TOut]):
    """The result of an invocation of an orchestration."""

    value: TOut | None = None
    exception: BaseException | None = None
    event: asyncio.Event = Field(default_factory=lambda: asyncio.Event())
    cancellation_token: CancellationToken = Field(default_factory=lambda: CancellationToken())

    async def get(self, timeout: float | None = None) -> TOut:
        """Get the result of the invocation.

        If a timeout is specified, the method will wait for the result for the specified time.
        If the result is not available within the timeout, a TimeoutError will be raised but the
        invocation will not be aborted.

        Args:
            timeout (int | None): The timeout (seconds) for getting the result. If None, wait indefinitely.

        Returns:
            TOut: The result of the invocation.
        """
        if timeout is not None:
            await asyncio.wait_for(self.event.wait(), timeout=timeout)
        else:
            await self.event.wait()

        if self.value is None:
            if self.cancellation_token.is_cancelled():
                raise RuntimeError("The invocation was canceled before it could complete.")
            if self.exception is not None:
                raise self.exception
            raise RuntimeError("The invocation did not produce a result.")
        return self.value

    def cancel(self) -> None:
        """Cancel the invocation.

        This method will cancel the invocation.
        Actors that have received messages will continue to process them, but no new messages will be processed.
        """
        if self.cancellation_token.is_cancelled():
            raise RuntimeError("The invocation has already been canceled.")
        if self.event.is_set():
            raise RuntimeError("The invocation has already been completed.")

        self.cancellation_token.cancel()
        self.event.set()


class OrchestrationBase(ABC, Generic[TIn, TOut]):
    """Base class for multi-agent orchestration."""

    t_in: type[TIn] | None = None
    t_out: type[TOut] | None = None

    def __init__(
        self,
        members: list[Agent],
        name: str | None = None,
        description: str | None = None,
        input_transform: Callable[[TIn], Awaitable[DefaultTypeAlias] | DefaultTypeAlias] | None = None,
        output_transform: Callable[[DefaultTypeAlias], Awaitable[TOut] | TOut] | None = None,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
    ) -> None:
        """Initialize the orchestration base.

        Args:
            members (list[Agent]): The list of agents to be used.
            name (str | None): A unique name of the orchestration. If None, a unique name will be generated.
            description (str | None): The description of the orchestration. If None, use a default description.
            input_transform (Callable | None): A function that transforms the external input message.
            output_transform (Callable | None): A function that transforms the internal output message.
            agent_response_callback (Callable | None): A function that is called when a response is produced
                by the agents.
        """
        if not members:
            raise ValueError("The members list cannot be empty.")
        self._members = members

        self.name = name or f"{self.__class__.__name__}_{uuid.uuid4().hex}"
        self.description = description or "A multi-agent orchestration."

        self._input_transform = input_transform or self._default_input_transform
        self._output_transform = output_transform or self._default_output_transform

        self._agent_response_callback = agent_response_callback

    def _set_types(self) -> None:
        """Set the external input and output types from the class arguments.

        This method can only be run after the class has been initialized because it relies on the
        `__orig_class__` attributes to determine the type parameters.

        This method will first try to get the type parameters from the class itself. The `__orig_class__`
        attribute will contain the external input and output types if they are explicitly given, for example:
        ```
        class MyOrchestration(OrchestrationBase[TIn, TOut]):
            pass


        my_orchestration = MyOrchestration[str, str](...)
        ```
        If the type parameters are not explicitly given, for example when the TypeVars has defaults, for example:
        ```
        TIn = TypeVar("TIn", default=str)
        TOut = TypeVar("TOut", default=str)


        class MyOrchestration(OrchestrationBase[TIn, TOut]):
            pass


        my_orchestration = MyOrchestration(...)
        ```
        The type parameters can be inferred from the `__orig_bases__` attribute.
        """
        if all([self.t_in is not None, self.t_out is not None]):
            return

        try:
            args = self.__orig_class__.__args__  # type: ignore[attr-defined]
            if len(args) != 2:
                raise TypeError("Orchestration must have input and output types.")
            self.t_in = args[0]
            self.t_out = args[1]
        except AttributeError:
            args = get_args(self.__orig_bases__[0])  # type: ignore[attr-defined]

            if len(args) != 2:
                raise TypeError("Orchestration must be subclassed with two type parameters.")
            self.t_in = args[0] if isinstance(args[0], type) else getattr(args[0], "__default__", None)  # type: ignore[assignment]
            self.t_out = args[1] if isinstance(args[1], type) else getattr(args[1], "__default__", None)  # type: ignore[assignment]

        if any([self.t_in is None, self.t_out is None]):
            raise TypeError("Orchestration must have concrete types for all type parameters.")

    async def invoke(
        self,
        task: str | DefaultTypeAlias | TIn,
        runtime: CoreRuntime,
    ) -> OrchestrationResult[TOut]:
        """Invoke the multi-agent orchestration.

        This method is non-blocking and will return immediately.
        To wait for the result, use the `get` method of the `OrchestrationResult` object.

        Args:
            task (str, DefaultTypeAlias, TIn): The task to be executed by the agents.
            runtime (CoreRuntime): The runtime environment for the agents.
        """
        self._set_types()

        orchestration_result = OrchestrationResult[self.t_out]()  # type: ignore[name-defined]

        async def result_callback(result: DefaultTypeAlias) -> None:
            nonlocal orchestration_result
            if inspect.iscoroutinefunction(self._output_transform):
                transformed_result = await self._output_transform(result)
            else:
                transformed_result = self._output_transform(result)

            orchestration_result.value = transformed_result
            orchestration_result.event.set()

        # This unique topic type is used to isolate the orchestration run from others.
        internal_topic_type = uuid.uuid4().hex

        await self._prepare(
            runtime,
            internal_topic_type=internal_topic_type,
            result_callback=result_callback,
        )

        if isinstance(task, str):
            prepared_task = ChatMessageContent(role=AuthorRole.USER, content=task)
        elif isinstance(task, ChatMessageContent) or (
            isinstance(task, list) and all(isinstance(item, ChatMessageContent) for item in task)
        ):
            prepared_task = task  # type: ignore[assignment]
        else:
            if inspect.iscoroutinefunction(self._input_transform):
                prepared_task = await self._input_transform(task)  # type: ignore[arg-type]
            else:
                prepared_task = self._input_transform(task)  # type: ignore[arg-type,assignment]

        background_task = asyncio.create_task(
            self._start(
                prepared_task,
                runtime,
                internal_topic_type,
                orchestration_result.cancellation_token,
            )
        )

        # Add a callback to surface any exceptions that occur during the task execution.
        def exception_callback(task: asyncio.Task) -> None:
            nonlocal orchestration_result
            try:
                task.result()
            except BaseException as e:
                orchestration_result.exception = e
                orchestration_result.event.set()

        background_task.add_done_callback(exception_callback)

        return orchestration_result

    @abstractmethod
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the multi-agent orchestration.

        Args:
            task (ChatMessageContent | list[ChatMessageContent]): The task to be executed by the agents.
            runtime (CoreRuntime): The runtime environment for the agents.
            internal_topic_type (str): The internal topic type for the orchestration that this actor is part of.
            cancellation_token (CancellationToken): The cancellation token for the orchestration.
        """
        pass

    @abstractmethod
    async def _prepare(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Register the actors and orchestrations with the runtime and add the required subscriptions.

        Args:
            runtime (CoreRuntime): The runtime environment for the agents.
            internal_topic_type (str): The internal topic type for the orchestration that this actor is part of.
            external_topic_type (str | None): The external topic type for the orchestration.
            direct_actor_type (str | None): The direct actor type for which this actor will relay the output message to.
            result_callback (Callable): A function that is called when the result is available.
        """
        pass

    def _default_input_transform(self, input_message: TIn) -> DefaultTypeAlias:
        """Default input transform function.

        This function transforms the external input message to chat message content(s).
        If the input message is already in the correct format, it is returned as is.

        Args:
            input_message (TIn): The input message to be transformed.

        Returns:
            DefaultTypeAlias: The transformed input message.
        """
        if isinstance(input_message, ChatMessageContent):
            return input_message

        if isinstance(input_message, list) and all(isinstance(item, ChatMessageContent) for item in input_message):
            return input_message

        if isinstance(input_message, self.t_in):  # type: ignore[arg-type]
            return ChatMessageContent(
                role=AuthorRole.USER,
                content=json.dumps(input_message.__dict__),
            )

        raise TypeError(f"Invalid input message type: {type(input_message)}. Expected {self.t_in}.")

    def _default_output_transform(self, output_message: DefaultTypeAlias) -> TOut:
        """Default output transform function.

        This function transforms the internal output message to the external output message.
        If the output message is already in the correct format, it is returned as is.

        Args:
            output_message (DefaultTypeAlias): The output message to be transformed.

        Returns:
            TOut: The transformed output message.
        """
        if self.t_out == DefaultTypeAlias or self.t_out in get_args(DefaultTypeAlias):
            if isinstance(output_message, ChatMessageContent) or (
                isinstance(output_message, list)
                and all(isinstance(item, ChatMessageContent) for item in output_message)
            ):
                return output_message  # type: ignore[return-value]
            raise TypeError(f"Invalid output message type: {type(output_message)}. Expected {self.t_out}.")

        if isinstance(output_message, ChatMessageContent):
            return self.t_out(**json.loads(output_message.content))  # type: ignore[misc]

        raise TypeError(f"Unable to transform output message of type {type(output_message)} to {self.t_out}.")
