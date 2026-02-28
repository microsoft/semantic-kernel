# Copyright (c) Microsoft. All rights reserved.

import logging
import os
from collections.abc import Mapping
from typing import Any

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

from .modelslab_settings import (
    MODELSLAB_CHAT_BASE_URL,
    MODELSLAB_CHAT_MODELS,
    MODELSLAB_DEFAULT_CHAT_MODEL,
)

logger: logging.Logger = logging.getLogger(__name__)


class ModelsLabChatCompletion(OpenAIChatCompletion):
    """ModelsLab Chat Completion connector for Semantic Kernel.

    Provides access to ModelsLab's uncensored large language models via an
    OpenAI-compatible endpoint.  Because ModelsLab's chat API is fully
    compatible with the OpenAI Chat Completions spec, this class simply
    subclasses :class:`OpenAIChatCompletion` and wires a custom
    ``AsyncOpenAI`` client that points at the ModelsLab endpoint — no
    additional request/response translation is needed.

    Supported models
    ----------------
    - ``llama-3.1-8b-uncensored``  (128 K context, default)
    - ``llama-3.1-70b-uncensored`` (128 K context)

    Quickstart
    ----------
    .. code-block:: python

        import asyncio
        from semantic_kernel import Kernel
        from semantic_kernel.connectors.ai.modelslab import ModelsLabChatCompletion
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
        from semantic_kernel.contents import ChatHistory

        kernel = Kernel()
        kernel.add_service(
            ModelsLabChatCompletion(
                ai_model_id="llama-3.1-70b-uncensored",
                api_key="YOUR_MODELSLAB_API_KEY",  # or set MODELSLAB_API_KEY env var
            )
        )

        chat = ChatHistory()
        chat.add_user_message("Write a short poem about open-source AI.")

        settings = OpenAIChatPromptExecutionSettings(max_tokens=256, temperature=0.7)

        async def main():
            chat_service = kernel.get_service(type=ModelsLabChatCompletion)
            result = await chat_service.get_chat_message_contents(chat, settings)
            print(result[0].content)

        asyncio.run(main())

    Environment variables
    ---------------------
    ``MODELSLAB_API_KEY``
        Your ModelsLab API key (required when ``api_key`` is not passed
        explicitly).
    ``MODELSLAB_CHAT_MODEL_ID``
        Model ID override (optional).
    ``MODELSLAB_CHAT_BASE_URL``
        API base URL override (optional, defaults to the official endpoint).
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize a ModelsLabChatCompletion service.

        Parameters
        ----------
        ai_model_id:
            ModelsLab model identifier.  Defaults to
            ``"llama-3.1-8b-uncensored"`` (or ``MODELSLAB_CHAT_MODEL_ID``
            env var).
        service_id:
            Optional service ID used when multiple chat services are
            registered with the same Kernel.
        api_key:
            ModelsLab API key.  Falls back to ``MODELSLAB_API_KEY`` env var.
        base_url:
            Override the default ModelsLab chat endpoint.  Falls back to
            ``MODELSLAB_CHAT_BASE_URL`` env var, then the official URL.
        default_headers:
            Extra HTTP headers to attach to every request.
        async_client:
            Bring-your-own ``AsyncOpenAI`` client (skips all key/URL
            resolution when provided).
        env_file_path:
            Path to a ``.env`` file for reading configuration.
        env_file_encoding:
            Encoding of the ``.env`` file (default: ``"utf-8"``).
        """
        resolved_api_key = (
            api_key
            or os.environ.get("MODELSLAB_API_KEY")
        )
        resolved_model = (
            ai_model_id
            or os.environ.get("MODELSLAB_CHAT_MODEL_ID")
            or MODELSLAB_DEFAULT_CHAT_MODEL
        )
        resolved_base_url = (
            base_url
            or os.environ.get("MODELSLAB_CHAT_BASE_URL")
            or MODELSLAB_CHAT_BASE_URL
        )

        if not async_client and not resolved_api_key:
            raise ServiceInitializationError(
                "ModelsLab API key is required.  Pass it via the `api_key` "
                "argument or set the MODELSLAB_API_KEY environment variable.  "
                "Get your key at https://modelslab.com/api-keys"
            )

        if resolved_model not in MODELSLAB_CHAT_MODELS:
            logger.warning(
                "Model '%s' is not in the known ModelsLab chat model list %s. "
                "Proceeding anyway — the API will reject unsupported models.",
                resolved_model,
                MODELSLAB_CHAT_MODELS,
            )

        # Build the OpenAI-compatible client pointed at ModelsLab
        if async_client is None:
            async_client = AsyncOpenAI(
                api_key=resolved_api_key,
                base_url=resolved_base_url,
            )

        # Delegate entirely to OpenAIChatCompletion — no extra wiring needed
        super().__init__(
            ai_model_id=resolved_model,
            service_id=service_id,
            default_headers=default_headers,
            async_client=async_client,
        )

        logger.info(
            "ModelsLabChatCompletion initialised (model=%s, endpoint=%s)",
            resolved_model,
            resolved_base_url,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "ModelsLabChatCompletion":
        """Construct a ``ModelsLabChatCompletion`` from a settings dict.

        Parameters
        ----------
        settings:
            Dictionary with optional keys: ``ai_model_id``, ``service_id``,
            ``api_key``, ``base_url``, ``default_headers``.
        """
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
            base_url=settings.get("base_url"),
            default_headers=settings.get("default_headers"),
        )
