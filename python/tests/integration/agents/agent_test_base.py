# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Generic, Protocol, TypeVar

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.contents import ChatMessageContent

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1


class ChatResponseProtocol(Protocol):
    """Represents a single response item returned by the agent."""

    @property
    def message(self) -> ChatMessageContent: ...

    @property
    def thread(self) -> AgentThread | None: ...


class ChatAgentProtocol(Protocol):
    """Protocol describing the common agent interface used by the tests."""

    async def get_response(
        self, messages: str | list[str] | None, thread: object | None = None
    ) -> ChatResponseProtocol: ...

    def invoke(
        self, messages: str | list[str] | None, thread: object | None = None
    ) -> AsyncIterator[ChatResponseProtocol]: ...

    def invoke_stream(
        self, messages: str | list[str] | None, thread: object | None = None
    ) -> AsyncIterator[ChatResponseProtocol]: ...


TAgent = TypeVar("TAgent", bound=ChatAgentProtocol)


async def run_with_retry(
    coro: Callable[..., Awaitable[Any]],
    *args,
    attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    **kwargs,
) -> AgentResponseItem[ChatMessageContent]:
    """
    Execute an async callable with retry/backoff logic.

    Args:
        coro: The async function to call
        args: Positional args to pass to the function
        attempts: How many times to attempt before giving up
        backoff_seconds: The initial backoff in seconds, doubled after each failure
        kwargs: Keyword args to pass to the function

    Returns:
        Whatever the async function returns

    Raises:
        Exception: If the function fails after the specified number of attempts
    """
    delay = backoff_seconds
    for attempt in range(1, attempts + 1):
        try:
            return await coro(*args, **kwargs)
        except Exception:
            if attempt == attempts:
                raise
            await asyncio.sleep(delay)
            delay *= 2
    raise RuntimeError("Unexpected error: run_with_retry exit.")


class AgentTestBase(Generic[TAgent]):
    """Common test base that wraps all agent invocation patterns with retry logic.

    Each integration test can inherit from this or use its methods directly.
    """

    async def get_response_with_retry(
        self,
        agent: Agent,
        messages: str | list[str] | None,
        thread: Any | None = None,
        attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Wraps agent.get_response(...) in run_with_retry."""
        return await run_with_retry(
            agent.get_response, messages=messages, thread=thread, attempts=attempts, backoff_seconds=backoff_seconds
        )

    async def get_invoke_with_retry(
        self,
        agent: Any,
        messages: str | list[str] | None,
        thread: Any | None = None,
        attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ) -> list[AgentResponseItem[ChatMessageContent]]:
        """Wraps agent.invoke(...) in run_with_retry.

        Collects generator results in a list before returning them.
        """
        return await run_with_retry(
            self._collect_from_invoke,
            agent,
            messages,
            thread=thread,
            attempts=attempts,
            backoff_seconds=backoff_seconds,
        )

    async def get_invoke_stream_with_retry(
        self,
        agent: Any,
        messages: str | list[str] | None,
        thread: Any | None = None,
        attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ) -> list[AgentResponseItem[ChatMessageContent]]:
        """Wraps agent.invoke_stream(...) in run_with_retry.

        Collects streaming results in a list before returning them."""
        return await run_with_retry(
            self._collect_from_invoke_stream,
            agent,
            messages,
            thread=thread,
            attempts=attempts,
            backoff_seconds=backoff_seconds,
        )

    async def _collect_from_invoke(
        self, agent: Agent, messages: str | list[str] | None, thread: Any | None = None
    ) -> list[AgentResponseItem[ChatMessageContent]]:
        results: list[AgentResponseItem[ChatMessageContent]] = []
        async for response in agent.invoke(messages=messages, thread=thread):
            results.append(response)
        return results

    async def _collect_from_invoke_stream(
        self, agent: Agent, messages: str | list[str] | None, thread: Any | None = None
    ) -> list[AgentResponseItem[ChatMessageContent]]:
        results: list[AgentResponseItem[ChatMessageContent]] = []
        async for response in agent.invoke_stream(messages=messages, thread=thread):
            results.append(response)
        return results
