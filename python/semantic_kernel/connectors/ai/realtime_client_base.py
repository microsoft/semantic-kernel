# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

####
# TODO (eavanvalkenburg): Move to ADR
# Receiving:
# Option 1: Events and Contents split
#    - content received through main receive_content method
#    - events received through event callback handlers
# Option 2: Everything is Content
#    - content (events as new Content Type) received through main receive_content method
# Option 3: Everything is Event (current)
#    - receive_content method is removed
#    - events received through main listen method
#    - default event handlers added for things like errors and function calling
#   - built-in vs custom event handling - separate or not?
# Sending:
# Option 1: Events and Contents split
#    - send_content and send_event
# Option 2: Everything is Content
#    - single method needed, with EventContent type support
# Option 3: Everything is Event (current)
#    - send_event method only, Content is part of event data
####


@experimental_class
class RealtimeClientBase(AIServiceClientBase, ABC):
    """Base class for a realtime client."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    async def __aenter__(self) -> "RealtimeClientBase":
        """Enter the context manager.

        Default implementation calls the create session method.
        """
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        await self.close_session()

    @abstractmethod
    async def close_session(self) -> None:
        """Close the session in the service."""
        pass

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
    async def event_listener(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> AsyncGenerator["StreamingChatMessageContent", Any]:
        """Get text contents from audio.

        Args:
            settings: Prompt execution settings.
            chat_history: Chat history.
            kwargs: Additional arguments.

        Yields:
            StreamingChatMessageContent messages
        """
        raise NotImplementedError

    @abstractmethod
    async def send_event(
        self,
        event: str,
        event_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send an event to the session.

        Args:
            event: Event name, can be a string or a Enum value.
            event_data: Event data.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        """Return the callback function to update the settings from a function call configuration.

        Override this method to provide a custom callback function to
        update the settings from a function call configuration.
        """
        return lambda configuration, settings, choice_type: None
