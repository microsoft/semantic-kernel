# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Mapping
from typing import Any
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
from typing import Dict, Mapping, Optional, overload
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from typing import Dict, Mapping, Optional, overload
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from typing import Dict, Mapping, Optional, overload
>>>>>>> main
=======
>>>>>>> head

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import (
    OpenAISettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletion(OpenAITextCompletionBase, OpenAIConfigBase):
    """OpenAI Text Completion class."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
=======
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        service_id: Optional[str] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
        """

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Initialize an OpenAITextCompletion service.

        Args:
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError(
                "Failed to create OpenAI settings.", ex
            ) from ex
        if not openai_settings.text_model_id:
            raise ServiceInitializationError("The OpenAI text model ID is required.")
        super().__init__(
            ai_model_id=openai_settings.text_model_id,
            service_id=service_id,
            api_key=(
                openai_settings.api_key.get_secret_value()
                if openai_settings.api_key
                else None
            ),
            org_id=openai_settings.org_id,

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    @overload
    def __init__(
        self,
        ai_model_id: str,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
        async_client: AsyncOpenAI,
        service_id: Optional[str] = None,
=======
        api_key: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
        async_client: AsyncOpenAI,
        service_id: Optional[str] = None,
>>>>>>> Stashed changes
=======
        api_key: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
>>>>>>> Stashed changes
>>>>>>> head
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head
            async_client {AsyncOpenAI} -- An existing client to use.
        """

    @overload
<<<<<<< div
=======
=======
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        """

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
>>>>>>> head
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    ) -> None:
        """Initialize an OpenAITextCompletion service.

        Args:
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError(
                "Failed to create OpenAI settings.", ex
            ) from ex
        if not openai_settings.text_model_id:
            raise ServiceInitializationError("The OpenAI text model ID is required.")
        super().__init__(
            ai_model_id=openai_settings.text_model_id,
            service_id=service_id,
            api_key=(
                openai_settings.api_key.get_secret_value()
                if openai_settings.api_key
                else None
            ),
            org_id=openai_settings.org_id,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    @overload
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< div
=======
        async_client: Optional[AsyncOpenAI] = None,
>>>>>>> main
=======
<<<<<<< Updated upstream
=======
        async_client: Optional[AsyncOpenAI] = None,
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
>>>>>>> head
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        """

=======
>>>>>>> Stashed changes
    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
>>>>>>> origin/main
    ) -> None:
        """Initialize an OpenAITextCompletion service.

        Args:
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
<<<<<<< main
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
=======
            api_key {Optional[str]} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys (Optional)
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
<<<<<<< div
<<<<<<< div
>>>>>>> origin/main
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError(
                "Failed to create OpenAI settings.", ex
            ) from ex
        if not openai_settings.text_model_id:
            raise ServiceInitializationError("The OpenAI text model ID is required.")
        super().__init__(
<<<<<<< main
            ai_model_id=openai_settings.text_model_id,
            service_id=service_id,
            api_key=(
                openai_settings.api_key.get_secret_value()
                if openai_settings.api_key
                else None
            ),
            org_id=openai_settings.org_id,
=======
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            service_id=service_id,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ai_model_type=OpenAIModelTypes.TEXT,
            default_headers=default_headers,
            client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "OpenAITextCompletion":
        """Initialize an Open AI service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
        """
        if "default_headers" in settings and isinstance(
            settings["default_headers"], str
        ):
            settings["default_headers"] = json.loads(settings["default_headers"])
        return OpenAITextCompletion(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            org_id=settings.get("org_id"),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )
