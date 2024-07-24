# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from copy import copy
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI

from semantic_kernel.agents.openai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.agents.openai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.openai.open_ai_assistant_execution_options import OpenAIAssistantExecutionOptions
from semantic_kernel.agents.openai.open_ai_service_configuration import OpenAIServiceConfiguration
from semantic_kernel.connectors.telemetry import APP_INFO, prepend_semantic_kernel_to_user_agent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from openai.resources.beta.assistants import Assistant

    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantAgent(OpenAIAssistantBase):
    """OpenAI Assistant Agent class."""

    _options_metadata_key: str = "__run_options"

    # region Agent Initialization

    def __init__(
        self,
        kernel: "Kernel",
        configuration: OpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> None:
        """Initialize an OpenAIAssistant service."""
        args: dict[str, Any] = {
            "kernel": kernel,
            "api_key": configuration.api_key if configuration.api_key else None,
            "org_id": configuration.org_id,
            "ai_model_id": configuration.ai_model_id,
            "service_id": configuration.service_id,
            "client": configuration.openai_client,
            "name": definition.name,
            "description": definition.description,
            "instructions": definition.instructions,
            "configuration": configuration,
            "definition": definition,
            "default_headers": configuration.default_headers,
        }

        if definition.id is not None:
            args["id"] = definition.id
        super().__init__(**args)

    @classmethod
    async def create(
        cls,
        *,
        kernel: "Kernel",
        configuration: OpenAIServiceConfiguration,
        definition: OpenAIAssistantDefinition,
    ) -> "OpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent."""
        agent = cls(
            kernel=kernel,
            configuration=configuration,
            definition=definition,
        )
        agent.assistant = await agent.create_assistant()
        return agent

    async def create_assistant(
        self,
    ) -> "Assistant":
        """Create the assistant."""
        kwargs: dict[str, Any] = {}

        tools = []
        if self.definition.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})
        if self.definition.enable_file_search:
            tools.append({"type": "file_search"})

        kwargs["tools"] = tools if tools else None

        tool_resources = {}
        if self.definition.file_ids:
            tool_resources["code_interpreter"] = {"file_ids": self.definition.file_ids}
        if self.definition.vector_store_ids:
            tool_resources["file_search"] = {"vector_store_ids": self.definition.vector_store_ids}

        kwargs["tool_resources"] = tool_resources if tool_resources else None

        # Filter out None values to avoid passing them as kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        self.assistant = await self.client.beta.assistants.create(
            model=self.ai_model_id,
            instructions=self.instructions,
            name=self.name,
            **kwargs,
        )
        return self.assistant

    @classmethod
    def create_client(
        cls, configuration: OpenAIServiceConfiguration, default_headers: dict[str, str] | None = None
    ) -> AsyncOpenAI:
        """Create the OpenAI client."""
        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not configuration.api_key:
            raise AgentInitializationError("The OpenAI API key is required.")

        return AsyncOpenAI(
            api_key=configuration.api_key,
            organization=configuration.org_id,
            default_headers=merged_headers,
        )

    def _create_open_ai_assistant_definition(self, assistant: "Assistant") -> OpenAIAssistantDefinition:
        """Create an OpenAI Assistant Definition from an OpenAI Assistant."""
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
        super().__init__(**configuration.model_dump())
        assistants = await self.client.beta.assistants.list(order="desc")
        for assistant in assistants.data:
            yield self._create_open_ai_assistant_definition(assistant)

    async def retrieve(
        self, kernel: "Kernel", configuration: OpenAIServiceConfiguration, id: str
    ) -> "OpenAIAssistantAgent":
        """Retrieve an assistant by ID."""
        super().__init__(**configuration.model_dump())
        assistant = await self.client.beta.assistants.retrieve(id)
        definition = self._create_open_ai_assistant_definition(assistant)
        return OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    # endregion
