# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from copy import copy
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIAssistantAgent(OpenAIAssistantBase):
    """OpenAI Assistant Agent class.

    Provides the ability to interact with OpenAI Assistants.
    """

    # region Agent Initialization

    def __init__(
        self,
        *,
        kernel: "Kernel | None" = None,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        client: AsyncOpenAI | None = None,
        default_headers: dict[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        name: str | None = None,
        enable_code_interpreter: bool | None = None,
        enable_file_search: bool | None = None,
        enable_json_response: bool | None = None,
        code_interpreter_file_ids: list[str] | None = [],
        temperature: float | None = None,
        top_p: float | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, Any] | None = {},
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant service.

        Args:
            kernel: The Kernel instance. (optional)
            service_id: The service ID. (optional) If not provided the default service name (default) is used.
            ai_model_id: The AI model ID. (optional)
            api_key: The OpenAI API key. (optional)
            org_id: The OpenAI organization ID. (optional)
            client: The OpenAI client. (optional)
            default_headers: The default headers. (optional)
            env_file_path: The environment file path. (optional)
            env_file_encoding: The environment file encoding. (optional)
            description: The assistant description. (optional)
            id: The assistant ID. (optional)
            instructions: The assistant instructions. (optional)
            name: The assistant name. (optional)
            enable_code_interpreter: Enable code interpreter. (optional)
            enable_file_search: Enable file search. (optional)
            enable_json_response: Enable JSON response. (optional)
            code_interpreter_file_ids: The file IDs. (optional)
            temperature: The temperature. (optional)
            top_p: The top p. (optional)
            vector_store_id: The vector store ID. (optional)
            metadata: The assistant metadata. (optional)
            max_completion_tokens: The max completion tokens. (optional)
            max_prompt_tokens: The max prompt tokens. (optional)
            parallel_tool_calls_enabled: Enable parallel tool calls. (optional)
            truncation_message_count: The truncation message count. (optional)
            kwargs: Additional keyword arguments.

        Raises:
            AgentInitializationError: If the api_key is not provided in the configuration.
        """
        openai_settings = OpenAIAssistantAgent._create_open_ai_settings(
            api_key=api_key,
            org_id=org_id,
            ai_model_id=ai_model_id,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )

        if not client and not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required, if a client is not provided.")
        if not openai_settings.chat_model_id:
            raise AgentInitializationException("The OpenAI chat model ID is required.")

        if not client:
            client = self._create_client(
                api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
                org_id=openai_settings.org_id,
                default_headers=default_headers,
            )

        service_id = service_id if service_id else DEFAULT_SERVICE_NAME

        args: dict[str, Any] = {
            "ai_model_id": openai_settings.chat_model_id,
            "service_id": service_id,
            "client": client,
            "description": description,
            "instructions": instructions,
            "enable_code_interpreter": enable_code_interpreter,
            "enable_file_search": enable_file_search,
            "enable_json_response": enable_json_response,
            "code_interpreter_file_ids": code_interpreter_file_ids,
            "temperature": temperature,
            "top_p": top_p,
            "vector_store_id": vector_store_id,
            "metadata": metadata,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "parallel_tool_calls_enabled": parallel_tool_calls_enabled,
            "truncation_message_count": truncation_message_count,
        }

        if name is not None:
            args["name"] = name
        if id is not None:
            args["id"] = id
        if kernel is not None:
            args["kernel"] = kernel
        if kwargs:
            args.update(kwargs)
        super().__init__(**args)

    @classmethod
    async def create(
        cls,
        *,
        kernel: "Kernel | None" = None,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        client: AsyncOpenAI | None = None,
        default_headers: dict[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        description: str | None = None,
        id: str | None = None,
        instructions: str | None = None,
        name: str | None = None,
        enable_code_interpreter: bool | None = None,
        code_interpreter_filenames: list[str] | None = None,
        enable_file_search: bool | None = None,
        vector_store_filenames: list[str] | None = None,
        enable_json_response: bool | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        vector_store_id: str | None = None,
        metadata: dict[str, Any] | None = {},
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        parallel_tool_calls_enabled: bool | None = True,
        truncation_message_count: int | None = None,
        **kwargs: Any,
    ) -> "OpenAIAssistantAgent":
        """Asynchronous class method used to create the OpenAI Assistant Agent.

        Args:
            kernel: The Kernel instance. (optional)
            service_id: The service ID. (optional) If not provided the default service name (default) is used.
            ai_model_id: The AI model ID. (optional)
            api_key: The OpenAI API key. (optional)
            org_id: The OpenAI organization ID. (optional)
            client: The OpenAI client. (optional)
            default_headers: The default headers. (optional)
            env_file_path: The environment file path. (optional)
            env_file_encoding: The environment file encoding. (optional)
            description: The assistant description. (optional)
            id: The assistant ID. (optional)
            instructions: The assistant instructions. (optional)
            name: The assistant name. (optional)
            enable_code_interpreter: Enable code interpreter. (optional)
            code_interpreter_filenames: The filenames/paths for files to use with file search. (optional)
            enable_file_search: Enable file search. (optional)
            vector_store_filenames: The list of file paths to upload and attach to the file search. (optional)
            enable_json_response: Enable JSON response. (optional)
            temperature: The temperature. (optional)
            top_p: The top p. (optional)
            vector_store_id: The vector store ID. (optional)
            metadata: The assistant metadata. (optional)
            max_completion_tokens: The max completion tokens. (optional)
            max_prompt_tokens: The max prompt tokens. (optional)
            parallel_tool_calls_enabled: Enable parallel tool calls. (optional)
            truncation_message_count: The truncation message count. (optional)
            kwargs: Additional keyword arguments.

        Returns:
            An OpenAIAssistantAgent instance.
        """
        agent = cls(
            kernel=kernel,
            service_id=service_id,
            ai_model_id=ai_model_id,
            api_key=api_key,
            org_id=org_id,
            client=client,
            default_headers=default_headers,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            description=description,
            id=id,
            instructions=instructions,
            name=name,
            enable_code_interpreter=enable_code_interpreter,
            enable_file_search=enable_file_search,
            enable_json_response=enable_json_response,
            temperature=temperature,
            top_p=top_p,
            vector_store_id=vector_store_id,
            metadata=metadata,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            parallel_tool_calls_enabled=parallel_tool_calls_enabled,
            truncation_message_count=truncation_message_count,
            **kwargs,
        )

        assistant_create_kwargs: dict[str, Any] = {}

        if code_interpreter_filenames is not None:
            code_interpreter_file_ids: list[str] = []
            for file_path in code_interpreter_filenames:
                try:
                    file_id = await agent.add_file(file_path=file_path, purpose="assistants")
                    code_interpreter_file_ids.append(file_id)
                except FileNotFoundError as ex:
                    logger.error(
                        f"Failed to upload code interpreter file with path: `{file_path}` with exception: {ex}"
                    )
                    raise AgentInitializationException("Failed to upload code interpreter files.", ex) from ex
            agent.code_interpreter_file_ids = code_interpreter_file_ids
            assistant_create_kwargs["code_interpreter_file_ids"] = code_interpreter_file_ids

        if vector_store_filenames is not None:
            file_search_file_ids: list[str] = []
            for file_path in vector_store_filenames:
                try:
                    file_id = await agent.add_file(file_path=file_path, purpose="assistants")
                    file_search_file_ids.append(file_id)
                except FileNotFoundError as ex:
                    logger.error(f"Failed to upload file search file with path: `{file_path}` with exception: {ex}")
                    raise AgentInitializationException("Failed to upload file search files.", ex) from ex

            if enable_file_search or agent.enable_file_search:
                vector_store_id = await agent.create_vector_store(file_ids=file_search_file_ids)
                agent.file_search_file_ids = file_search_file_ids
                agent.vector_store_id = vector_store_id
                assistant_create_kwargs["vector_store_id"] = vector_store_id

        agent.assistant = await agent.create_assistant(**assistant_create_kwargs)
        return agent

    @staticmethod
    def _create_client(
        api_key: str | None = None, org_id: str | None = None, default_headers: dict[str, str] | None = None
    ) -> AsyncOpenAI:
        """An internal method to create the OpenAI client from the provided arguments.

        Args:
            api_key: The OpenAI API key.
            org_id: The OpenAI organization ID. (optional)
            default_headers: The default headers. (optional)

        Returns:
            An OpenAI client instance.
        """
        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not api_key:
            raise AgentInitializationException("Please provide an OpenAI api_key")

        return AsyncOpenAI(
            api_key=api_key,
            organization=org_id,
            default_headers=merged_headers,
        )

    @staticmethod
    def _create_open_ai_settings(
        api_key: str | None = None,
        org_id: str | None = None,
        ai_model_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> OpenAISettings:
        """An internal method to create the OpenAI settings from the provided arguments.

        Args:
            api_key: The OpenAI API key.
            org_id: The OpenAI organization ID. (optional)
            ai_model_id: The AI model ID. (optional)
            env_file_path: The environment file path. (optional)
            env_file_encoding: The environment file encoding. (optional)

        Returns:
            An OpenAI settings instance.
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationException("Failed to create OpenAI settings.", ex) from ex

        return openai_settings

    async def list_definitions(self) -> AsyncIterable[dict[str, Any]]:
        """List the assistant definitions.

        Yields:
            An AsyncIterable of dictionaries representing the OpenAIAssistantDefinition.
        """
        assistants = await self.client.beta.assistants.list(order="desc")
        for assistant in assistants.data:
            yield OpenAIAssistantBase._create_open_ai_assistant_definition(assistant)

    @classmethod
    async def retrieve(
        cls,
        *,
        id: str,
        kernel: "Kernel | None" = None,
        api_key: str | None = None,
        org_id: str | None = None,
        ai_model_id: str | None = None,
        client: AsyncOpenAI | None = None,
        default_headers: dict[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "OpenAIAssistantAgent":
        """Retrieve an assistant by ID.

        Args:
            id: The assistant ID.
            kernel: The Kernel instance. (optional)
            api_key: The OpenAI API key. (optional)
            org_id: The OpenAI organization ID. (optional)
            ai_model_id: The AI model ID. (optional)
            client: The OpenAI client. (optional)
            default_headers: The default headers. (optional)
            env_file_path: The environment file path. (optional)
            env_file_encoding: The environment file encoding. (optional

        Returns:
            An OpenAIAssistantAgent instance.
        """
        openai_settings = OpenAIAssistantAgent._create_open_ai_settings(
            api_key=api_key,
            org_id=org_id,
            ai_model_id=ai_model_id,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        if not client and not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required, if a client is not provided.")
        if not openai_settings.chat_model_id:
            raise AgentInitializationException("The OpenAI chat model ID is required.")
        if not client:
            client = OpenAIAssistantAgent._create_client(
                api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
                org_id=openai_settings.org_id,
                default_headers=default_headers,
            )
        assistant = await client.beta.assistants.retrieve(id)
        assistant_definition = OpenAIAssistantBase._create_open_ai_assistant_definition(assistant)
        return OpenAIAssistantAgent(kernel=kernel, assistant=assistant, **assistant_definition)

    # endregion
