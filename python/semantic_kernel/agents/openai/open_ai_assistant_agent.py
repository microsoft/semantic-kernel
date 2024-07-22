# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import ValidationError

from semantic_kernel.agents.openai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.agents.openai.open_ai_assistant_configuration import OpenAIAssistantConfiguration
from semantic_kernel.agents.openai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if TYPE_CHECKING:
    from openai.resources.beta.assistants import Assistant

    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


class OpenAIAssistantAgent(OpenAIAssistantBase):
    """OpenAI Assistant Agent class."""

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    error_message_states: ClassVar[list[str]] = ["failed", "canceled", "expired"]

    _is_deleted: bool = False

    # region Agent Initialization

    def __init__(
        self,
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
        kernel: "Kernel | None" = None,
        default_headers: Mapping[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OpenAIAssistant service."""
        if configuration is None:
            configuration = OpenAIAssistantConfiguration()

        if definition is None:
            definition = OpenAIAssistantDefinition()

        try:
            openai_settings = OpenAISettings.create(
                api_key=configuration.api_key,
                org_id=configuration.org_id,
                chat_model_id=configuration.ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex

        if not configuration.client and not openai_settings.api_key:
            raise ServiceInitializationError("The OpenAI API key is required.")
        if not openai_settings.chat_model_id:
            raise ServiceInitializationError("The OpenAI model ID is required.")

        args: dict[str, Any] = {
            "api_key": openai_settings.api_key.get_secret_value(),
            "org_id": openai_settings.org_id,
            "ai_model_id": openai_settings.chat_model_id,
            "service_id": configuration.service_id,
            "client": configuration.client,
            "name": definition.name,
            "description": definition.description,
            "instructions": definition.instructions,
            "configuration": configuration,
            "definition": definition,
            "default_headers": default_headers,
        }

        if definition.id is not None:
            args["id"] = definition.id
        if kernel is not None:
            args["kernel"] = kernel
        super().__init__(**args)

    @classmethod
    async def create(
        cls,
        *,
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
        kernel: "Kernel | None" = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "OpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent."""
        if configuration is None:
            configuration = OpenAIAssistantConfiguration()

        if definition is None:
            definition = OpenAIAssistantDefinition()

        agent = cls(
            name=definition.name,
            description=definition.description,
            id=definition.id,
            instructions=definition.instructions,
            kernel=kernel,
            configuration=configuration,
            definition=definition,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        agent.assistant = await agent.create_assistant()
        return agent

    async def create_assistant(
        self,
    ) -> "Assistant":
        """Create the assistant."""
        kw_args: dict[str, Any] = {}

        kw_args["tools"] = []
        if self.definition.enable_code_interpreter:
            kw_args["tools"].append({"type": "code_interpreter"})
        if self.definition.enable_file_search:
            kw_args["tools"].append({"type": "file_search"})

        kw_args["tool_resources"] = []
        if self.definition.file_ids:
            kw_args["tool_resources"].append({"code_interpreter": {"file_ids": self.definition.file_ids}})
        if self.definition.vector_store_id:
            kw_args["tool_resources"].append({"file_search": {"vector_store_ids": [self.definition.vector_store_id]}})

        self.assistant = await self.client.beta.assistants.create(
            model=self.ai_model_id,
            instructions=self.instructions,
            name=self.name,
            **kw_args,
        )
        return self.assistant

    # endregion
