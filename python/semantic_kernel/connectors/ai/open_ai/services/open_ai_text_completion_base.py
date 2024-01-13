# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAITextRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)

if TYPE_CHECKING:
    from semantic_kernel.models.contents.kernel_content import KernelContent
    from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
        OpenAIRequestSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletionBase(TextCompletionClientBase, OpenAIHandler):
    async def complete(
        self,
        prompt: str,
        settings: "OpenAIRequestSettings",
        **kwargs,
    ) -> "KernelContent":
        """Executes a completion request and returns the result.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAIRequestSettings} -- The settings to use for the completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        if isinstance(settings, OpenAITextRequestSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        return response

    async def complete_stream(
        self,
        prompt: str,
        settings: "OpenAIRequestSettings",
        **kwargs,
    ) -> "KernelContent":
        """
        Executes a completion request and streams the result.
        Supports both chat completion and text completion.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAIRequestSettings} -- The settings to use for the completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        if "prompt" in settings.model_fields:
            settings.prompt = prompt
        if "messages" in settings.model_fields:
            if not settings.messages:
                settings.messages = [{"role": "user", "content": prompt}]
            else:
                settings.messages.append({"role": "user", "content": prompt})
        settings.ai_model_id = self.ai_model_id
        settings.stream = True
        response = await self._send_request(request_settings=settings)
        return response

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAITextRequestSettings
