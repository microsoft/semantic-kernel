# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Iterable
from copy import copy
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncOpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from openai.types.beta.assistant import Assistant
from openai.types.beta.assistant_create_params import (
    ToolResources,
    ToolResourcesCodeInterpreter,
    ToolResourcesFileSearch,
)
from openai.types.beta.assistant_response_format_option_param import AssistantResponseFormatOptionParam
from openai.types.beta.file_search_tool_param import FileSearchToolParam
from pydantic import BaseModel, Field, ValidationError

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel
from semantic_kernel.agents.open_ai.assistant_content_generation import generate_message_content
from semantic_kernel.agents.open_ai.assistant_thread_actions import AssistantThreadActions
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.connectors.utils.structured_output_schema import generate_structured_output_response_format_schema
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from openai.types.beta.assistant_tool_param import AssistantToolParam
    from openai.types.beta.code_interpreter_tool_param import CodeInterpreterToolParam
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run_create_params import TruncationStrategy

    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger: logging.Logger = logging.getLogger(__name__)


@release_candidate
class OpenAIAssistantAgent(Agent):
    """OpenAI Assistant Agent class.

    Provides the ability to interact with OpenAI Assistants.
    """

    # region Agent Initialization

    client: AsyncOpenAI
    definition: Assistant
    plugins: list[Any] = Field(default_factory=list)
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)

    channel_type: ClassVar[type[AgentChannel]] = OpenAIAssistantChannel  # type: ignore

    def __init__(
        self,
        *,
        arguments: KernelArguments | None = None,
        client: AsyncOpenAI,
        definition: Assistant,
        kernel: "Kernel | None" = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        polling_options: RunPollingOptions | None = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIAssistant service.

        Args:
            arguments: The arguments to pass to the function.
            client: The OpenAI client.
            definition: The assistant definition.
            kernel: The Kernel instance.
            plugins: The plugins to add to the kernel. If both the plugins and the kernel are supplied,
                the plugins take precedence and are added to the kernel by default.
            polling_options: The polling options.
            prompt_template_config: The prompt template configuration.
            kwargs: Additional keyword arguments.
        """
        args: dict[str, Any] = {
            "client": client,
            "definition": definition,
            "name": definition.name or f"assistant_agent_{generate_random_ascii_name(length=8)}",
            "description": definition.description,
        }

        if arguments is not None:
            args["arguments"] = arguments
        if definition.id is not None:
            args["id"] = definition.id
        if definition.instructions is not None:
            args["instructions"] = definition.instructions
        if kernel is not None:
            args["kernel"] = kernel

        if (
            definition.instructions
            and prompt_template_config
            and definition.instructions != prompt_template_config.template
        ):
            logger.info(
                f"Both `instructions` ({definition.instructions}) and `prompt_template_config` "
                f"({prompt_template_config.template}) were provided. Using template in `prompt_template_config` "
                "and ignoring `instructions`."
            )

        if plugins is not None:
            args["plugins"] = plugins

        if prompt_template_config is not None:
            args["prompt_template"] = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )
            if prompt_template_config.template is not None:
                # Use the template from the prompt_template_config if it is provided
                args["instructions"] = prompt_template_config.template
        if polling_options is not None:
            args["polling_options"] = polling_options
        if kwargs:
            args.update(kwargs)
        super().__init__(**args)

    @staticmethod
    def setup_resources(
        *,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        default_headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> tuple[AsyncOpenAI, str]:
        """A method to create the OpenAI client and the model from the provided arguments.

        Any arguments provided will override the values in the environment variables/environment file.

        Args:
            ai_model_id: The AI model ID
            api_key: The API key
            org_id: The organization ID
            env_file_path: The environment file path
            env_file_encoding: The environment file encoding, defaults to utf-8
            default_headers: The default headers to add to the client
            kwargs: Additional keyword arguments

        Returns:
            An OpenAI client instance and the configured model name
        """
        try:
            openai_settings = OpenAISettings.create(
                chat_model_id=ai_model_id,
                api_key=api_key,
                org_id=org_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationException("Failed to create OpenAI settings.", ex) from ex

        if not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required.")

        if not openai_settings.chat_model_id:
            raise AgentInitializationException("The OpenAI model ID is required.")

        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        client = AsyncOpenAI(
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            organization=openai_settings.org_id,
            default_headers=merged_headers,
            **kwargs,
        )

        return client, openai_settings.chat_model_id

    # endregion

    # region Tool Handling

    @staticmethod
    def configure_code_interpreter_tool(
        file_ids: str | list[str] | None = None, **kwargs: Any
    ) -> tuple[list["CodeInterpreterToolParam"], ToolResources]:
        """Generate tool + tool_resources for the code_interpreter."""
        if isinstance(file_ids, str):
            file_ids = [file_ids]
        tool: "CodeInterpreterToolParam" = {"type": "code_interpreter"}
        resources: ToolResources = {}
        if file_ids:
            resources["code_interpreter"] = ToolResourcesCodeInterpreter(file_ids=file_ids)
        return [tool], resources

    @staticmethod
    def configure_file_search_tool(
        vector_store_ids: str | list[str], **kwargs: Any
    ) -> tuple[list[FileSearchToolParam], ToolResources]:
        """Generate tool + tool_resources for the file_search."""
        if isinstance(vector_store_ids, str):
            vector_store_ids = [vector_store_ids]

        tool: FileSearchToolParam = {
            "type": "file_search",
        }
        resources: ToolResources = {"file_search": ToolResourcesFileSearch(vector_store_ids=vector_store_ids, **kwargs)}  # type: ignore
        return [tool], resources

    @staticmethod
    def configure_response_format(
        response_format: dict[Literal["type"], Literal["text", "json_object"]]
        | dict[str, Any]
        | type[BaseModel]
        | type
        | AssistantResponseFormatOptionParam
        | None = None,
    ) -> AssistantResponseFormatOptionParam | None:
        """Form the response format.

        "auto" is the default value. Not configuring the response format will result in the model
        outputting text.

        Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
        Outputs which ensures the model will match your supplied JSON schema. Learn more
        in the [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).

        Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
        message the model generates is valid JSON, as long as the prompt contains "JSON."

        Args:
            response_format: The response format.

        Returns:
            AssistantResponseFormatOptionParam: The response format.
        """
        if response_format is None or response_format == "auto":
            return None

        configured_response_format = None
        if isinstance(response_format, dict):
            resp_type = response_format.get("type")
            if resp_type == "json_object":
                configured_response_format = {"type": "json_object"}
            elif resp_type == "json_schema":
                json_schema = response_format.get("json_schema")  # type: ignore
                if not isinstance(json_schema, dict):
                    raise AgentInitializationException(
                        "If response_format has type 'json_schema', 'json_schema' must be a valid dictionary."
                    )
                # We're assuming the response_format has already been provided in the correct format
                configured_response_format = response_format  # type: ignore
            else:
                raise AgentInitializationException(
                    f"Encountered unexpected response_format type: {resp_type}. Allowed types are `json_object` "
                    " and `json_schema`."
                )
        elif isinstance(response_format, type):
            # If it's a type, differentiate based on whether it's a BaseModel subclass
            if issubclass(response_format, BaseModel):
                configured_response_format = type_to_response_format_param(response_format)  # type: ignore
            else:
                generated_schema = KernelJsonSchemaBuilder.build(parameter_type=response_format, structured_output=True)
                assert generated_schema is not None  # nosec
                configured_response_format = generate_structured_output_response_format_schema(
                    name=response_format.__name__, schema=generated_schema
                )
        else:
            # If it's not a dict or a type, throw an exception
            raise AgentInitializationException(
                "response_format must be a dictionary, a subclass of BaseModel, a Python class/type, or None"
            )

        return configured_response_format  # type: ignore

    # endregion

    # region Agent Channel Methods

    def get_channel_keys(self) -> Iterable[str]:
        """Get the channel keys.

        Returns:
            Iterable[str]: The channel keys.
        """
        # Distinguish from other channel types.
        yield f"{OpenAIAssistantAgent.__name__}"

        # Distinguish between different agent IDs
        yield self.id

        # Distinguish between agent names
        yield self.name

        # Distinguish between different API base URLs
        yield str(self.client.base_url)

    async def create_channel(self) -> AgentChannel:
        """Create a channel."""
        thread = await self.client.beta.threads.create()

        return OpenAIAssistantChannel(client=self.client, thread_id=thread.id)

    # endregion

    # region Message Handling

    async def add_chat_message(
        self, thread_id: str, message: "str | ChatMessageContent", **kwargs: Any
    ) -> "Message | None":
        """Add a chat message to the thread.

        Args:
            thread_id: The ID of the thread
            message: The chat message to add
            kwargs: Additional keyword arguments

        Returns:
            The thread message or None
        """
        return await AssistantThreadActions.create_message(
            client=self.client, thread_id=thread_id, message=message, **kwargs
        )

    async def get_thread_messages(self, thread_id: str) -> AsyncIterable["ChatMessageContent"]:
        """Get the messages for the specified thread.

        Args:
            thread_id: The thread id.

        Yields:
            ChatMessageContent: The chat message.
        """
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(thread_id=thread_id, limit=100, order="desc")
        for message in thread_messages.data:
            assistant_name = None
            if message.assistant_id and message.assistant_id not in agent_names:
                agent = await self.client.beta.assistants.retrieve(message.assistant_id)
                if agent.name:
                    agent_names[message.assistant_id] = agent.name
            assistant_name = agent_names.get(message.assistant_id) if message.assistant_id else message.assistant_id
            assistant_name = assistant_name or message.assistant_id

            content: "ChatMessageContent" = generate_message_content(str(assistant_name), message)

            if len(content.items) > 0:
                yield content

    # endregion

    # region Invocation Methods

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        thread_id: str,
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        additional_instructions: str | None = None,
        additional_messages: list[ChatMessageContent] | None = None,
        instructions_override: str | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> ChatMessageContent:
        """Get a response from the agent on a thread.

        Args:
            thread_id: The ID of the thread.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Returns:
            ChatMessageContent: The response from the agent.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation_strategy": truncation_strategy,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        messages: list[ChatMessageContent] = []
        async for is_visible, message in AssistantThreadActions.invoke(
            agent=self,
            thread_id=thread_id,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
        ):
            if is_visible and message.metadata.get("code") is not True:
                messages.append(message)

        if not messages:
            raise AgentInvokeException("No response messages were returned from the agent.")
        return messages[-1]

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        thread_id: str,
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        additional_instructions: str | None = None,
        additional_messages: list[ChatMessageContent] | None = None,
        instructions_override: str | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent.

        Args:
            thread_id: The ID of the thread.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation_strategy": truncation_strategy,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        async for is_visible, message in AssistantThreadActions.invoke(
            agent=self,
            thread_id=thread_id,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
        ):
            if is_visible:
                yield message

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        thread_id: str,
        *,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        additional_instructions: str | None = None,
        additional_messages: list[ChatMessageContent] | None = None,
        instructions_override: str | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        messages: list[ChatMessageContent] | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        response_format: "AssistantResponseFormatOptionParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation_strategy: "TruncationStrategy | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the agent.

        Args:
            thread_id: The ID of the thread.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            messages: The messages that act as a receiver for completed messages.
            metadata: The metadata.
            model: The model.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation_strategy: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning_effort,
            "response_format": response_format,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation_strategy": truncation_strategy,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        async for message in AssistantThreadActions.invoke_stream(
            agent=self,
            thread_id=thread_id,
            kernel=kernel,
            arguments=arguments,
            messages=messages,
            **run_level_params,  # type: ignore
        ):
            yield message

    # endregion
