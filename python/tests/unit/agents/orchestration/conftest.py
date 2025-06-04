# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import AsyncIterable, Awaitable, Callable

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class MockAgentThread(AgentThread):
    """A mock agent thread for testing purposes."""

    @override
    async def _create(self) -> str:
        return "mock_thread_id"

    @override
    async def _delete(self) -> None:
        pass

    @override
    async def _on_new_message(self, new_message: ChatMessageContent) -> None:
        pass


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        # Simulate some processing time
        await asyncio.sleep(0.1)
        return AgentResponseItem[ChatMessageContent](
            message=ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content="mock_response",
            ),
            thread=thread or MockAgentThread(),
        )

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        pass


class MockRuntime(CoreRuntime):
    """A mock agent runtime for testing purposes."""

    pass
