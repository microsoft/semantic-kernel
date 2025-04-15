# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any, ClassVar

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from numpy import ndarray
from pydantic import ConfigDict, PrivateAttr

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.realtime_events import RealtimeEvents
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RealtimeClientBase(AIServiceClientBase, ABC):
    """Base class for a realtime client."""

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True
    )

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False
    audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None
    _chat_history: ChatHistory | None = PrivateAttr(default=None)
    _settings: PromptExecutionSettings | None = PrivateAttr(default=None)
    _kernel: Kernel | None = PrivateAttr(default=None)
    _create_kwargs: dict[str, Any] | None = PrivateAttr(default=None)

    @abstractmethod
    async def send(self, event: RealtimeEvents) -> None:
        """Send an event to the service.

        Args:
            event: The event to send.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    @abstractmethod
    def receive(
        self,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvents, None]:
        """Starts listening for messages from the service, generates events.

        Args:
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible.
                It is called first in both websockets and webrtc.
                Even when passed, the audio content will still be
                added to the receiving queue.
                This can also be set in the constructor.
                When supplied here it will override any value in the class.
            kwargs: Additional arguments.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_session(
        self,
        chat_history: "ChatHistory | None" = None,
        settings: "PromptExecutionSettings | None" = None,
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
        chat_history: "ChatHistory | None" = None,
        settings: "PromptExecutionSettings | None" = None,
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

    async def __aenter__(self) -> "Self":
        """Enter the context manager.

        Default implementation calls the create session method.
        """
        await self.create_session(self._chat_history, self._settings)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        await self.close_session()

    def __call__(
        self,
        chat_history: "ChatHistory | None" = None,
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> Self:
        """Call the service and set the chat history and settings.

        Args:
            chat_history: Chat history.
            settings: Prompt execution settings.
            kwargs: Additional arguments, can include `kernel` or `plugins` or specific settings for the service.
                Check the update_session method for the specific service for more details.
        """
        self._chat_history = chat_history
        self._settings = settings
        self._create_kwargs = kwargs
        return self
