# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar

from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant

from semantic_kernel.agents.openai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.agents.openai.open_ai_assistant_configuration import OpenAIAssistantConfiguration
from semantic_kernel.agents.openai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.contents import AuthorRole

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


class OpenAIAssistantAgent(OpenAIAssistantBase, OpenAIConfigBase):
    assistant: Assistant | None = None
    client: AsyncOpenAI | None = None
    config: OpenAIAssistantConfiguration | None = None
    definition: OpenAIAssistantDefinition | None = None

    allowed_message_roles: ClassVar[list[str]] = [AuthorRole.USER, AuthorRole.ASSISTANT]
    error_message_states: ClassVar[list[str]] = ["failed", "canceled", "expired"]

    _is_deleted: bool = False

    # region Agent Initialization

    def __init__(
        self,
        default_headers: Mapping[str, str] | None = None,
        name: str | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OpenAIAssistant service."""
        if configuration is None:
            configuration = OpenAIAssistantConfiguration()

        if definition is None:
            definition = OpenAIAssistantDefinition()

        args: dict[str, Any] = {
            "api_key": configuration.api_key,
            "org_id": configuration.org_id,
            "ai_model_id": configuration.ai_model_id,
            "service_id": configuration.service_id,
            "client": configuration.client,
            "name": name,
            "description": description,
            "instructions": instructions,
            "config": configuration,
            "definition": definition,
            "env_file_path": env_file_path,
            "env_file_encoding": env_file_encoding,
            "default_headers": default_headers,
        }

        if id is not None:
            args["id"] = id
        if kernel is not None:
            args["kernel"] = kernel
        super().__init__(**args)

    @classmethod
    async def create(
        cls,
        *,
        name: str | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
    ) -> "OpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent."""
        agent = cls(
            name=name,
            description=description,
            id=id,
            instructions=instructions,
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
        configuration: OpenAIAssistantConfiguration | None = None,
        definition: OpenAIAssistantDefinition | None = None,
    ) -> Assistant:
        """Create the assistant."""
        self.assistant = await self.client.beta.assistants.create(
            model=self.ai_model_id,
            instructions=self.instructions,
            name=self.name,
        )
        return self.assistant

    # endregion
