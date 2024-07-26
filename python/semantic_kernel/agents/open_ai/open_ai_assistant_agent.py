# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from copy import copy
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI

from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.agents.open_ai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.open_ai.open_ai_assistant_execution_options import OpenAIAssistantExecutionOptions
from semantic_kernel.agents.open_ai.open_ai_service_configuration import OpenAIServiceConfiguration
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from openai.resources.beta.assistants import Assistant

    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantAgent(OpenAIAssistantBase):
    """OpenAI Assistant Agent class.

    Provides the ability to interact with OpenAI Assistants.
    """

    _options_metadata_key: str = "__run_options"

    # region Agent Initialization

    def __init__(
        self,
        kernel: "Kernel",
        configuration: OpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> None:
        """Initialize an OpenAIAssistant service.

        Args:
            kernel: The Kernel instance.
            configuration: The OpenAI Service Configuration.
            definition: The OpenAI Assistant Definition

        Raises:
            AgentInitializationError: If the api_key is not provided in the configuration.
        """
        client = self._create_client_from_configuration(configuration)
        service_id = configuration.service_id if configuration.service_id else DEFAULT_SERVICE_NAME

        args: dict[str, Any] = {
            "kernel": kernel,
            "api_key": configuration.api_key if configuration.api_key else None,
            "org_id": configuration.org_id,
            "ai_model_id": configuration.ai_model_id,
            "service_id": service_id,
            "client": client,
            "name": definition.name,
            "description": definition.description,
            "instructions": definition.instructions,
            "configuration": configuration,
            "definition": definition,
        }

        if definition.id is not None:
            args["id"] = definition.id
        super().__init__(**args)

    @classmethod
    def create_client(
        cls,
        configuration: OpenAIServiceConfiguration,
    ) -> AsyncOpenAI:
        """Create the OpenAI client.

        Args:
            configuration: The OpenAI Service Configuration.

        Returns:
            An OpenAI client instance.
        """
        return cls._create_client_from_configuration(configuration)

    @classmethod
    async def create(
        cls,
        *,
        kernel: "Kernel",
        configuration: OpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> "OpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent.

        Args:
            kernel: The Kernel instance.
            configuration: The OpenAI Service Configuration.
            definition: The OpenAI Assistant Definition.

        Returns:
            An OpenAIAssistantAgent instance.
        """
        agent = cls(
            kernel=kernel,
            configuration=configuration,
            definition=definition,
        )
        agent.assistant = await agent.create_assistant()
        return agent

    @staticmethod
    def _create_client_from_configuration(
        configuration: OpenAIServiceConfiguration,
    ) -> AsyncOpenAI:
        """Create the OpenAI client from configuration.

        Args:
            configuration: The OpenAI Service Configuration.

        Returns:
            An OpenAI client instance.
        """
        merged_headers = dict(copy(configuration.default_headers)) if configuration.default_headers else {}
        if configuration.default_headers:
            merged_headers.update(configuration.default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not configuration.api_key:
            raise AgentInitializationError("Please provide an OpenAI api_key")

        return AsyncOpenAI(
            api_key=configuration.api_key,
            organization=configuration.org_id,
            default_headers=merged_headers,
        )

    def _create_open_ai_assistant_definition(self, assistant: "Assistant") -> OpenAIAssistantDefinition:
        """Create an OpenAI Assistant Definition from an OpenAI Assistant.

        Args:
            assistant: The OpenAI Assistant.

        Returns:
            An OpenAIAssistantDefinition instance.
        """
        settings: OpenAIAssistantExecutionOptions | None = None
        if isinstance(assistant.metadata, dict) and self._options_metadata_key in assistant.metadata:
            settings = OpenAIAssistantExecutionOptions(**assistant.metadata[self._options_metadata_key])

        tool_resources = getattr(assistant, "tool_resources", None)
        file_ids = []
        vector_store_id = None
        if tool_resources:
            file_ids = tool_resources.get("code_interpreter", {}).get("file_ids", [])
            file_search_resource = tool_resources.get("file_search", {})
            vector_store_ids = file_search_resource.get("vector_store_ids", [])
            if vector_store_ids:
                vector_store_id = vector_store_ids[0]
        enable_json_response = assistant.response_format == {"type": "json_object"}

        return OpenAIAssistantDefinition(
            ai_model_id=assistant.model,
            description=assistant.description,
            id=assistant.id,
            instructions=assistant.instructions,
            name=assistant.name,
            enable_code_interpreter="code_interpreter" in assistant.tools,
            enable_file_search="file_search" in assistant.tools,
            enable_json_response=enable_json_response,
            file_ids=file_ids,
            temperature=assistant.temperature,
            top_p=assistant.top_p,
            vector_store_ids=[vector_store_id] if vector_store_id else None,
            metadata=assistant.metadata,
            execution_settings=settings,
        )

    async def list_definitions(
        self,
        configuration: OpenAIServiceConfiguration,
    ) -> AsyncIterable[OpenAIAssistantDefinition]:
        """List the assistant definitions.

        Args:
            configuration: The OpenAI Service Configuration.

        Yields:
            An AsyncIterable of OpenAIAssistantDefinition.
        """
        client = self._create_client_from_configuration(configuration)
        assistants = await client.beta.assistants.list(order="desc")
        for assistant in assistants.data:
            yield self._create_open_ai_assistant_definition(assistant)

    async def retrieve(
        self, kernel: "Kernel", configuration: OpenAIServiceConfiguration, id: str
    ) -> "OpenAIAssistantAgent":
        """Retrieve an assistant by ID.

        Args:
            kernel: The Kernel instance.
            configuration: The OpenAI Service Configuration.
            id: The assistant ID.

        Returns:
            An OpenAIAssistantAgent instance.
        """
        client = self._create_client_from_configuration(configuration)
        assistant = await client.beta.assistants.retrieve(id)
        definition = self._create_open_ai_assistant_definition(assistant)
        return OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    # endregion
