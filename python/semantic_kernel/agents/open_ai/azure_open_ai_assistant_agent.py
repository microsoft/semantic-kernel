# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from copy import copy
from typing import TYPE_CHECKING, Any

from openai import AsyncAzureOpenAI

from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.agents.open_ai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.open_ai.open_ai_assistant_execution_options import OpenAIAssistantExecutionOptions
from semantic_kernel.agents.open_ai.open_ai_service_configuration import (
    AzureOpenAIServiceConfiguration,
)
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from openai.resources.beta.assistants import Assistant

    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureOpenAIAssistantAgent(OpenAIAssistantBase):
    """Azure OpenAI Assistant Agent class.

    Provides the ability to interact with Azure OpenAI Assistants.
    """

    _options_metadata_key: str = "__run_options"

    # region Agent Initialization

    def __init__(
        self,
        kernel: "Kernel",
        configuration: AzureOpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> None:
        """Initialize an Azure OpenAI Assistant Agent.

        Args:
            kernel: The Kernel instance.
            configuration: The Azure OpenAI Service Configuration.
            definition: The OpenAI Assistant Definition

        Raises:
            AgentInitializationError: If the api_key is not provided in the configuration.
        """
        client = self._create_client_from_configuration(configuration)
        service_id = configuration.service_id if configuration.service_id else DEFAULT_SERVICE_NAME

        args: dict[str, Any] = {
            "kernel": kernel,
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
    async def create(
        cls,
        *,
        kernel: "Kernel",
        configuration: AzureOpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> "AzureOpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent.

        Args:
            kernel: The Kernel instance.
            configuration: The Azure OpenAI Service Configuration.
            definition: The OpenAI Assistant Definition.

        Returns:
            An instance of the AzureOpenAIAssistantAgent
        """
        agent = cls(
            kernel=kernel,
            configuration=configuration,
            definition=definition,
        )
        agent.assistant = await agent.create_assistant()
        return agent

    @classmethod
    def create_client(
        cls,
        configuration: AzureOpenAIServiceConfiguration,
    ) -> AsyncAzureOpenAI:
        """Create the OpenAI client.

        Args:
            configuration: The Azure OpenAI Service Configuration.

        Returns:
            An AsyncAzureOpenAI client instance
        """
        return cls._create_client_from_configuration(configuration)

    def _create_open_ai_assistant_definition(self, assistant: "Assistant") -> OpenAIAssistantDefinition:
        """Create an OpenAI Assistant Definition from an OpenAI Assistant.

        Args:
            assistant: The OpenAI Assistant instance.

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

    @staticmethod
    def _create_client_from_configuration(configuration: AzureOpenAIServiceConfiguration) -> AsyncAzureOpenAI:
        """Create the OpenAI client from configuration.

        Args:
            configuration: The Azure OpenAI Service Configuration.

        Returns:
            An AsyncAzureOpenAI client instance.
        """
        merged_headers = dict(copy(configuration.default_headers)) if configuration.default_headers else {}
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not configuration.api_key and not configuration.ad_token and not configuration.ad_token_provider:
            raise AgentInitializationError(
                "Please provide either AzureOpenAI api_key, an ad_token or an ad_token_provider or a client."
            )
        if not configuration.endpoint:
            raise AgentInitializationError("Please provide an AzureOpenAI endpoint.")
        return AsyncAzureOpenAI(
            azure_endpoint=str(configuration.endpoint),
            api_version=configuration.api_version,
            api_key=configuration.api_key,
            azure_ad_token=configuration.ad_token,
            azure_ad_token_provider=configuration.ad_token_provider,
            default_headers=merged_headers,
        )

    async def list_definitions(
        self,
        configuration: AzureOpenAIServiceConfiguration,
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
        self, kernel: "Kernel", configuration: AzureOpenAIServiceConfiguration, id: str
    ) -> "AzureOpenAIAssistantAgent":
        """Retrieve an assistant by ID."""
        client = self._create_client_from_configuration(configuration)
        assistant = await client.beta.assistants.retrieve(id)
        definition = self._create_open_ai_assistant_definition(assistant)
        return AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    # endregion
