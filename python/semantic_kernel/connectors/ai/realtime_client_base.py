# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod
from asyncio import Queue
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import Field

if sys.version_info >= (3, 11):
    from asyncio import TaskGroup
else:
    from taskgroup import TaskGroup

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.realtime_event import RealtimeEvent
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory


@experimental_class
class RealtimeClientBase(AIServiceClientBase, ABC):
    """Base class for a realtime client."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False
    send_buffer: Queue[RealtimeEvent] = Field(default_factory=Queue)

    async def send(self, event: RealtimeEvent) -> None:
        """Send an event to the service.

        Args:
            event: The event to send.
            kwargs: Additional arguments.
        """
        await self.send_buffer.put(event)

    async def start_streaming(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvent, None]:
        """Start streaming, will start both listening and sending.

        This method, start tasks for both listening and sending.

        The arguments are passed to the start_listening method.

        Args:
            settings: Prompt execution settings.
            chat_history: Chat history.
            kwargs: Additional arguments.
        """
        await self.update_session(settings=settings, chat_history=chat_history, **kwargs)
        async with TaskGroup() as tg:
            tg.create_task(self.start_sending(**kwargs))
            yield from tg.create_task(self.start_listening())

    @abstractmethod
    async def start_listening(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvent, None]:
        """Starts listening for messages from the service, generates events.

        Args:
            settings: Prompt execution settings.
            chat_history: Chat history.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    @abstractmethod
    async def start_sending(
        self,
    ) -> None:
        """Start sending items from the input_buffer to the service."""
        raise NotImplementedError

    @abstractmethod
    async def create_session(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service.

        Args:
            settings: Prompt execution settings.
            chat_history: Chat history.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_session(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> None:
        """Update a session in the service.

        Can be used when using the context manager instead of calling create_session with these same arguments.

        Args:
            settings: Prompt execution settings.
            chat_history: Chat history.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    @abstractmethod
    async def close_session(self) -> None:
        """Close the session in the service."""
        pass

    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        """Return the callback function to update the settings from a function call configuration.

        Override this method to provide a custom callback function to
        update the settings from a function call configuration.
        """
        return lambda configuration, settings, choice_type: None

    async def __aenter__(self) -> "RealtimeClientBase":
        """Enter the context manager.

        Default implementation calls the create session method.
        """
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        await self.close_session()
