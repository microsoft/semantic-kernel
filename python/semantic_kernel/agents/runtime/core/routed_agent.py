# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable, Coroutine, Sequence
from functools import wraps
from typing import Any, DefaultDict, Literal, Protocol, TypeVar, cast, get_type_hints, overload, runtime_checkable

from semantic_kernel.agents.runtime.core.base_agent import BaseAgent
from semantic_kernel.agents.runtime.core.exceptions import CantHandleException
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.serialization import MessageSerializer, try_get_known_serializers_for_type
from semantic_kernel.agents.runtime.core.type_helpers import AnyType, get_types
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger("agent_runtime.core")

AgentT = TypeVar("AgentT")
ReceivesT = TypeVar("ReceivesT")
ProducesT = TypeVar("ProducesT", covariant=True)

# TODO(evmattso): Generic typevar bound binding U to agent type
# Can't do because python doesnt support it

# region MessageHandler Protocol and Methods


# Pyright and mypy disagree on the variance of ReceivesT. Mypy thinks it should be contravariant here.
# Revisit this later to see if we can remove the ignore.
@experimental
@runtime_checkable
class MessageHandler(Protocol[AgentT, ReceivesT, ProducesT]):  # type: ignore
    """A protocol for message handlers."""

    target_types: Sequence[type]
    produces_types: Sequence[type]
    is_message_handler: Literal[True]
    router: Callable[[ReceivesT, MessageContext], bool]

    # agent_instance binds to self in the method
    @staticmethod
    async def __call__(agent_instance: AgentT, message: ReceivesT, ctx: MessageContext) -> ProducesT:
        """Override the __call__ method to make this a callable class."""
        ...


# NOTE: this works on concrete types and not inheritance
# TODO(evmattso): Use a protocol for the outer function to check checked arg names


@experimental
@overload
def message_handler(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]],
) -> MessageHandler[AgentT, ReceivesT, ProducesT]: ...


@experimental
@overload
def message_handler(
    func: None = None,
    *,
    match: None = ...,
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
    MessageHandler[AgentT, ReceivesT, ProducesT],
]: ...


@experimental
@overload
def message_handler(
    func: None = None,
    *,
    match: Callable[[ReceivesT, MessageContext], bool],
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
    MessageHandler[AgentT, ReceivesT, ProducesT],
]: ...


@experimental
def message_handler(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]] | None = None,
    *,
    strict: bool = True,
    match: Callable[[ReceivesT, MessageContext], bool] | None = None,
) -> (
    Callable[
        [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
        MessageHandler[AgentT, ReceivesT, ProducesT],
    ]
    | MessageHandler[AgentT, ReceivesT, ProducesT]
):
    """Decorator for generic message handlers.

    Add this decorator to methods in a :class:`RoutedAgent` class that are intended to handle both
    event and RPC messages.

    These methods must have a specific signature that needs to be followed for it to be valid:

    - The method must be an `async` method.
    - The method must be decorated with the `@message_handler` decorator.
    - The method must have exactly 3 arguments:
        1. `self`
        2. `message`: The message to be handled, this must be type-hinted with the message type that it is
            intended to handle.
        3. `ctx`: A :class:`agent_runtime.core.MessageContext` object.
    - The method must be type hinted with what message types it can return as a response, or it can return `None` if
    it does not return anything.

    Handlers can handle more than one message type by accepting a Union of the message types. It can also return more
    than one message type by returning a Union of the message types.

    Args:
        func: The function to be decorated.
        strict: If `True`, the handler will raise an exception if the message type or return type is not in the target
            types. If `False`, it will log a warning instead.
        match: A function that takes the message and the context as arguments and returns a boolean. This is used for
            secondary routing after the message type. For handlers addressing the same message type, the match function
            is applied in alphabetical order of the handlers and the first matching handler will be called while the
            rest are skipped. If `None`, the first handler in alphabetical order matching the same message type will
            be called.
    """

    def decorator(
        func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]],
    ) -> MessageHandler[AgentT, ReceivesT, ProducesT]:
        type_hints = get_type_hints(func)
        if "message" not in type_hints:
            raise AssertionError("message parameter not found in function signature")

        if "return" not in type_hints:
            raise AssertionError("return not found in function signature")

        # Get the type of the message parameter
        target_types = get_types(type_hints["message"])
        if target_types is None:
            raise AssertionError("Message type not found")

        return_types = get_types(type_hints["return"])

        if return_types is None:
            raise AssertionError("Return type not found")

        # Convert target_types to list and stash

        @wraps(func)
        async def wrapper(self: AgentT, message: ReceivesT, ctx: MessageContext) -> ProducesT:
            if type(message) not in target_types:
                if strict:
                    raise CantHandleException(f"Message type {type(message)} not in target types {target_types}")
                logger.warning(f"Message type {type(message)} not in target types {target_types}")

            return_value = await func(self, message, ctx)

            if AnyType not in return_types and type(return_value) not in return_types:
                if strict:
                    raise ValueError(f"Return type {type(return_value)} not in return types {return_types}")
                logger.warning(f"Return type {type(return_value)} not in return types {return_types}")

            return return_value

        wrapper_handler = cast(MessageHandler[AgentT, ReceivesT, ProducesT], wrapper)
        wrapper_handler.target_types = list(target_types)
        wrapper_handler.produces_types = list(return_types)
        wrapper_handler.is_message_handler = True
        wrapper_handler.router = match or (lambda _message, _ctx: True)

        return wrapper_handler

    if func is None and not callable(func):
        return decorator
    if callable(func):
        return decorator(func)
    raise ValueError("Invalid arguments")


# endregion

# region Message Handler Decorators


@experimental
@overload
def event(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]],
) -> MessageHandler[AgentT, ReceivesT, None]: ...


@experimental
@overload
def event(
    func: None = None,
    *,
    match: None = ...,
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]]],
    MessageHandler[AgentT, ReceivesT, None],
]: ...


@experimental
@overload
def event(
    func: None = None,
    *,
    match: Callable[[ReceivesT, MessageContext], bool],
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]]],
    MessageHandler[AgentT, ReceivesT, None],
]: ...


@experimental
def event(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]] | None = None,
    *,
    strict: bool = True,
    match: Callable[[ReceivesT, MessageContext], bool] | None = None,
) -> (
    Callable[
        [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]]],
        MessageHandler[AgentT, ReceivesT, None],
    ]
    | MessageHandler[AgentT, ReceivesT, None]
):
    """Decorator for event message handlers.

    Add this decorator to methods in a :class:`RoutedAgent` class that are intended to handle event messages.
    These methods must have a specific signature that needs to be followed for it to be valid:

    - The method must be an `async` method.
    - The method must be decorated with the `@message_handler` decorator.
    - The method must have exactly 3 arguments:
        1. `self`
        2. `message`: The event message to be handled, this must be type-hinted with the message type that it is
            intended to handle.
        3. `ctx`: A :class:`agent_runtime.core.MessageContext` object.
    - The method must return `None`.

    Handlers can handle more than one message type by accepting a Union of the message types.

    Args:
        func: The function to be decorated.
        strict: If `True`, the handler will raise an exception if the message type is not in the target types.
            If `False`, it will log a warning instead.
        match: A function that takes the message and the context as arguments and returns a boolean. This is used for
            secondary routing after the message type. For handlers addressing the same message type, the match function
            is applied in alphabetical order of the handlers and the first matching handler will be called while the
            rest are skipped. If `None`, the first handler in alphabetical order matching the same message type will be
            called.
    """

    def decorator(
        func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, None]],
    ) -> MessageHandler[AgentT, ReceivesT, None]:
        type_hints = get_type_hints(func)
        if "message" not in type_hints:
            raise AssertionError("message parameter not found in function signature")

        if "return" not in type_hints:
            raise AssertionError("return not found in function signature")

        # Get the type of the message parameter
        target_types = get_types(type_hints["message"])
        if target_types is None:
            raise AssertionError("Message type not found. Please provide a type hint for the message parameter.")

        return_types = get_types(type_hints["return"])

        if return_types is None:
            raise AssertionError("Return type not found. Please use `None` as the type hint of the return type.")

        # Convert target_types to list and stash

        @wraps(func)
        async def wrapper(self: AgentT, message: ReceivesT, ctx: MessageContext) -> None:
            if type(message) not in target_types:
                if strict:
                    raise CantHandleException(f"Message type {type(message)} not in target types {target_types}")
                logger.warning(f"Message type {type(message)} not in target types {target_types}")

            return_value = await func(self, message, ctx)  # type: ignore

            if return_value is not None:
                if strict:
                    raise ValueError(f"Return type {type(return_value)} is not None.")
                logger.warning(f"Return type {type(return_value)} is not None. It will be ignored.")

            return

        wrapper_handler = cast(MessageHandler[AgentT, ReceivesT, None], wrapper)
        wrapper_handler.target_types = list(target_types)
        wrapper_handler.produces_types = list(return_types)
        wrapper_handler.is_message_handler = True
        # Wrap the match function with a check on the is_rpc flag.
        wrapper_handler.router = lambda _message, _ctx: (not _ctx.is_rpc) and (match(_message, _ctx) if match else True)

        return wrapper_handler

    if func is None and not callable(func):
        return decorator
    if callable(func):
        return decorator(func)
    raise ValueError("Invalid arguments")


@experimental
@overload
def rpc(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]],
) -> MessageHandler[AgentT, ReceivesT, ProducesT]: ...


@experimental
@overload
def rpc(
    func: None = None,
    *,
    match: None = ...,
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
    MessageHandler[AgentT, ReceivesT, ProducesT],
]: ...


@experimental
@overload
def rpc(
    func: None = None,
    *,
    match: Callable[[ReceivesT, MessageContext], bool],
    strict: bool = ...,
) -> Callable[
    [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
    MessageHandler[AgentT, ReceivesT, ProducesT],
]: ...


@experimental
def rpc(
    func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]] | None = None,
    *,
    strict: bool = True,
    match: Callable[[ReceivesT, MessageContext], bool] | None = None,
) -> (
    Callable[
        [Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]]],
        MessageHandler[AgentT, ReceivesT, ProducesT],
    ]
    | MessageHandler[AgentT, ReceivesT, ProducesT]
):
    """Decorator for RPC message handlers.

    Add this decorator to methods in a :class:`RoutedAgent` class that are intended to handle RPC messages.
    These methods must have a specific signature that needs to be followed for it to be valid:

    - The method must be an `async` method.
    - The method must be decorated with the `@message_handler` decorator.
    - The method must have exactly 3 arguments:
        1. `self`
        2. `message`: The message to be handled, this must be type-hinted with the message type that it is intended to
            handle.
        3. `ctx`: A :class:`agent_runtime.core.MessageContext` object.
    - The method must be type hinted with what message types it can return as a response, or it can return `None` if
        it does not return anything.

    Handlers can handle more than one message type by accepting a Union of the message types. It can also return more
    than one message type by returning a Union of the message types.

    Args:
        func: The function to be decorated.
        strict: If `True`, the handler will raise an exception if the message type or return type is not in the target
            types. If `False`, it will log a warning instead.
        match: A function that takes the message and the context as arguments and returns a boolean. This is used for
            secondary routing after the message type. For handlers addressing the same message type, the match function
            is applied in alphabetical order of the handlers and the first matching handler will be called while the
            rest are skipped. If `None`, the first handler in alphabetical order matching the same message type will be
            called.
    """

    def decorator(
        func: Callable[[AgentT, ReceivesT, MessageContext], Coroutine[Any, Any, ProducesT]],
    ) -> MessageHandler[AgentT, ReceivesT, ProducesT]:
        type_hints = get_type_hints(func)
        if "message" not in type_hints:
            raise AssertionError("message parameter not found in function signature")

        if "return" not in type_hints:
            raise AssertionError("return not found in function signature")

        # Get the type of the message parameter
        target_types = get_types(type_hints["message"])
        if target_types is None:
            raise AssertionError("Message type not found")

        return_types = get_types(type_hints["return"])

        if return_types is None:
            raise AssertionError("Return type not found")

        # Convert target_types to list and stash

        @wraps(func)
        async def wrapper(self: AgentT, message: ReceivesT, ctx: MessageContext) -> ProducesT:
            if type(message) not in target_types:
                if strict:
                    raise CantHandleException(f"Message type {type(message)} not in target types {target_types}")
                logger.warning(f"Message type {type(message)} not in target types {target_types}")

            return_value = await func(self, message, ctx)

            if AnyType not in return_types and type(return_value) not in return_types:
                if strict:
                    raise ValueError(f"Return type {type(return_value)} not in return types {return_types}")
                logger.warning(f"Return type {type(return_value)} not in return types {return_types}")

            return return_value

        wrapper_handler = cast(MessageHandler[AgentT, ReceivesT, ProducesT], wrapper)
        wrapper_handler.target_types = list(target_types)
        wrapper_handler.produces_types = list(return_types)
        wrapper_handler.is_message_handler = True
        wrapper_handler.router = lambda _message, _ctx: (_ctx.is_rpc) and (match(_message, _ctx) if match else True)

        return wrapper_handler

    if func is None and not callable(func):
        return decorator
    if callable(func):
        return decorator(func)
    raise ValueError("Invalid arguments")


# endregion


# region RoutedAgent


@experimental
class RoutedAgent(BaseAgent):
    """A base class for agents that route messages to handlers.

    Messages are routed based on the type of the message and optional matching functions.

    To create a routed agent, subclass this class and add message handlers as methods decorated with
    either :func:`event` or :func:`rpc` decorator.
    """

    def __init__(self, description: str) -> None:
        """Initialize the routed agent.

        Args:
            description: The description of the agent.
        """
        # Self is already bound to the handlers
        self._handlers: DefaultDict[
            type[Any],
            list[MessageHandler[RoutedAgent, Any, Any]],
        ] = DefaultDict(list)

        handlers = self._discover_handlers()
        for message_handler in handlers:
            for target_type in message_handler.target_types:
                self._handlers[target_type].append(message_handler)

        super().__init__(description)

    async def on_message_impl(self, message: Any, ctx: MessageContext) -> Any | None:
        """Handle a message by routing it to the appropriate message handler.

        Do not override this method in subclasses. Instead, add message handlers as methods decorated with
        either the :func:`event` or :func:`rpc` decorator.
        """
        key_type: type[Any] = type(message)  # type: ignore
        handlers = self._handlers.get(key_type)  # type: ignore
        if handlers is not None:
            # Iterate over all handlers for this matching message type.
            # Call the first handler whose router returns True and then return the result.
            for h in handlers:
                if h.router(message, ctx):
                    return await h(self, message, ctx)
        return await self.on_unhandled_message(message, ctx)  # type: ignore

    async def on_unhandled_message(self, message: Any, ctx: MessageContext) -> None:
        """Called when a message is received that does not have a matching message handler.

        The default implementation logs an info message.

        Args:
            message: The message that was not handled.
            ctx: The context of the message.
        """
        logger.info(f"Unhandled message: {message}")

    @classmethod
    def _discover_handlers(cls) -> Sequence[MessageHandler[Any, Any, Any]]:
        handlers: list[MessageHandler[Any, Any, Any]] = []
        for attr in dir(cls):
            if callable(getattr(cls, attr, None)):
                # Since we are getting it from the class, self is not bound
                handler = getattr(cls, attr)
                if hasattr(handler, "is_message_handler"):
                    handlers.append(cast(MessageHandler[Any, Any, Any], handler))
        return handlers

    @classmethod
    def _handles_types(cls) -> list[tuple[type[Any], list[MessageSerializer[Any]]]]:
        # TODO(evmattso): handle deduplication
        handlers = cls._discover_handlers()
        types: list[tuple[type[Any], list[MessageSerializer[Any]]]] = []
        types.extend(cls.internal_extra_handles_types)
        for handler in handlers:
            for t in handler.target_types:
                # TODO(evmattso): support different serializers
                serializers = try_get_known_serializers_for_type(t)
                if len(serializers) == 0:
                    raise ValueError(f"No serializers found for type {t}.")

                types.append((t, try_get_known_serializers_for_type(t)))
        return types


# endregion
