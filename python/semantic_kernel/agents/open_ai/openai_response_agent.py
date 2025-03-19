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
from openai.types.beta.file_search_tool_param import FileSearchToolParam
from openai.types.responses.file_search_tool_param import (
    FileSearchToolParam,
)
from openai.types.responses.tool_param import ToolParam
from openai.types.responses.web_search_tool_param import UserLocation, WebSearchToolParam
from pydantic import BaseModel, Field, ValidationError

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.open_ai.assistant_content_generation import create_chat_message, generate_message_content
from semantic_kernel.agents.open_ai.assistant_thread_actions import AssistantThreadActions
from semantic_kernel.agents.open_ai.response_agent_thread_actions import ResponseAgentThreadActions
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.connectors.utils.structured_output_schema import generate_structured_output_response_format_schema
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.exceptions.agent_exceptions import (
    AgentChatException,
    AgentInitializationException,
    AgentInvokeException,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from openai.types.beta.assistant_tool_param import AssistantToolParam
    from openai.types.responses.response_text_config_param import ResponseTextConfigParam

    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class OpenAIResponseChannel(AgentChannel):
    """OpenAI Response Channel."""

    def __init__(self, client: AsyncOpenAI, thread_id: str) -> None:
        """Initialize the OpenAI Response Channel."""
        self.client = client
        self.thread_id = thread_id

    @override
    async def receive(self, history: list["ChatMessageContent"]) -> None:
        """Receive the conversation messages.

        Args:
            history: The conversation messages.
        """
        for message in history:
            if any(isinstance(item, FunctionCallContent) for item in message.items):
                continue
            # TODO, update to correct method
            await create_chat_message(self.client, self.thread_id, message)

    @override
    async def invoke(self, agent: "Agent", **kwargs: Any) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the agent.

        Args:
            agent: The agent to invoke.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, ChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent

        if not isinstance(agent, OpenAIAssistantAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(OpenAIAssistantAgent)}.")

        async for is_visible, message in AssistantThreadActions.invoke(agent=agent, thread_id=self.thread_id, **kwargs):
            yield is_visible, message

    @override
    async def invoke_stream(
        self, agent: "Agent", messages: list[ChatMessageContent], **kwargs: Any
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent stream.

        Args:
            agent: The agent to invoke.
            messages: The conversation messages.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, StreamingChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent

        if not isinstance(agent, OpenAIAssistantAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(OpenAIAssistantAgent)}.")

        async for message in AssistantThreadActions.invoke_stream(
            agent=agent, thread_id=self.thread_id, messages=messages, **kwargs
        ):
            yield message

    @override
    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Get the conversation history.

        Yields:
            ChatMessageContent: The conversation history.
        """
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(
            thread_id=self.thread_id, limit=100, order="desc"
        )
        for message in thread_messages.data:
            assistant_name = None
            if message.assistant_id and message.assistant_id not in agent_names:
                agent = await self.client.beta.assistants.retrieve(message.assistant_id)
                if agent.name:
                    agent_names[message.assistant_id] = agent.name
            assistant_name = agent_names.get(message.assistant_id) if message.assistant_id else message.assistant_id

            content: ChatMessageContent = generate_message_content(str(assistant_name), message)

            if len(content.items) > 0:
                yield content

    @override
    async def reset(self) -> None:
        """Reset the agent's thread."""
        try:
            await self.client.beta.threads.delete(thread_id=self.thread_id)
        except Exception as e:
            raise AgentChatException(f"Failed to delete thread: {e}")


@experimental
class OpenAIResponseAgent(Agent):
    """OpenAI Response Agent class.

    Provides the ability to interact with OpenAI's Responses API.
    """

    # region Agent Initialization

    ai_model_id: str
    client: AsyncOpenAI
    function_choice_behavior: FunctionChoiceBehavior | None = Field(
        default_factory=lambda: FunctionChoiceBehavior.Auto()
    )
    metadata: dict[str, str] | None = Field(default_factory=dict)
    temperature: float | None = Field(default=None)
    top_p: float | None = Field(default=None)
    plugins: list[Any] = Field(default_factory=list)
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)
    tools: list[ToolParam] = Field(default_factory=list)

    channel_type: ClassVar[type[AgentChannel | None]] = OpenAIResponseChannel

    def __init__(
        self,
        ai_model_id: str,
        client: AsyncOpenAI,
        *,
        arguments: KernelArguments | None = None,
        description: str | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        metadata: dict[str, str] | None = None,
        name: str | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        polling_options: RunPollingOptions | None = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        temperature: float | None = None,
        tools: list[ToolParam] | None = None,
        top_p: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAI Response Agent.

        Args:
            client: The OpenAI client.
            arguments: The arguments to pass to the function.
            description: The description of the agent.
            function_choice_behavior: The function choice behavior to determine how and which plugins are
                advertised to the model.
            id: The ID of the agent.
            instructions: The instructions for the agent.
            kernel: The Kernel instance.
            name: The name of the agent.
            plugins: The plugins to add to the kernel. If both the plugins and the kernel are supplied,
                the plugins take precedence and are added to the kernel by default.
            polling_options: The polling options.
            prompt_template_config: The prompt template configuration.
            kwargs: Additional keyword arguments.
        """
        args: dict[str, Any] = {
            "ai_model_id": ai_model_id,
            "client": client,
            "name": name or f"response_agent_{generate_random_ascii_name(length=8)}",
            "description": description,
        }

        if arguments is not None:
            args["arguments"] = arguments
        if function_choice_behavior is not None:
            args["function_choice_behavior"] = function_choice_behavior
        if id is not None:
            args["id"] = id
        if instructions is not None:
            args["instructions"] = instructions
        if kernel is not None:
            args["kernel"] = kernel
        if instructions and prompt_template_config and instructions != prompt_template_config.template:
            logger.info(
                f"Both `instructions` ({instructions}) and `prompt_template_config` "
                f"({prompt_template_config.template}) were provided. Using template in `prompt_template_config` "
                "and ignoring `instructions`."
            )
        if metadata is not None:
            args["metadata"] = metadata
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
        if temperature is not None:
            args["temperature"] = temperature
        if tools:
            args["tools"] = tools
        if top_p is not None:
            args["top_p"] = top_p
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
            An OpenAI client instance and the configured Response model name
        """
        try:
            openai_settings = OpenAISettings.create(
                response_model_id=ai_model_id,
                api_key=api_key,
                org_id=org_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationException("Failed to create OpenAI settings.", ex) from ex

        if not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required.")

        if not openai_settings.response_model_id:
            raise AgentInitializationException("The OpenAI Response model ID is required.")

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

        return client, openai_settings.response_model_id

    # endregion

    # region Tool Handling

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
    def configure_web_search_tool(
        context_size: Literal["low", "medium", "high"] | None = None,
        user_location: UserLocation | None = None,
    ) -> WebSearchToolParam:
        """Generate the tool definition for web search.

        Args:
            context_size: One of 'low', 'medium', or 'high'. If None, the default ('medium')
                is assumed server-side.
            user_location: A UserLocation TypedDict if you want to supply location details
                (city, country, region, timezone).
                - The city and region fields are free text strings, like Seattle and Washington, respectively.
                - The country field is a two-letter ISO country code, like US.
                - The timezone field is an IANA timezone like America/Seattle.

        Returns:
            A WebSearchToolParam dictionary with any passed-in parameters.
        """
        tool: WebSearchToolParam = {
            "type": "web_search_preview",
        }
        if context_size is not None:
            tool["search_context_size"] = context_size
        if user_location is not None:
            tool["user_location"] = user_location
        return tool

    @staticmethod
    def configure_response_format(
        response_format: dict[Literal["type"], Literal["text", "json_object"]]
        | dict[str, Any]
        | type[BaseModel]
        | type
        | None = None,
    ) -> dict | None:
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
            The response format.
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
        yield f"{OpenAIResponseAgent.__name__}"

        # Distinguish between different agent IDs
        yield self.id

        # Distinguish between agent names
        yield self.name

        # Distinguish between different API base URLs
        yield str(self.client.base_url)

    async def create_channel(self) -> AgentChannel:
        """Create a channel."""
        thread = await self.client.beta.threads.create()

        return OpenAIResponseChannel(client=self.client, thread_id=thread.id)

    # endregion

    # region Invocation Methods

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        chat_history: "ChatHistory",
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        instructions_override: str | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        max_completion_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> ChatMessageContent:
        """Get a response from the agent on a thread.

        Args:
            chat_history: The Chat History for the agent.
            arguments: The kernel arguments.
            kernel: The kernel.
            instructions_override: The instructions override.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_completion_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model to override on a per-run basis.
            parallel_tool_calls: Parallel tool calls.
            reasoning_effort: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
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

        response_level_params = {
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning_effort": reasoning,
            "text": text,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation": truncation,
        }
        response_level_params = {k: v for k, v in response_level_params.items() if v is not None}

        function_choice_behavior = function_choice_behavior or self.function_choice_behavior

        messages: list[ChatMessageContent] = []
        async for is_visible, message in ResponseAgentThreadActions.invoke(
            agent=self,
            chat_history=chat_history,
            kernel=kernel,
            arguments=arguments,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
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
        *,
        chat_history: "ChatHistory",
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        instructions_override: str | None = None,
        max_completion_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        temperature: float | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent.

        Args:
            chat_history: The Chat History for the agent.
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
            reasoning: The reasoning effort.
            response_format: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
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

        response_level_params = {
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning": reasoning,
            "text": text,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation": truncation,
        }
        response_level_params = {k: v for k, v in response_level_params.items() if v is not None}

        function_choice_behavior = function_choice_behavior or self.function_choice_behavior

        async for is_visible, message in ResponseAgentThreadActions.invoke(
            agent=self,
            chat_history=chat_history,
            kernel=kernel,
            arguments=arguments,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
        ):
            if is_visible:
                yield message

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        *,
        chat_history: "ChatHistory",
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        # Run-level parameters:
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        instructions_override: str | None = None,
        max_completion_tokens: int | None = None,
        max_prompt_tokens: int | None = None,
        messages: list[ChatMessageContent] | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        temperature: float | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[AssistantToolParam] | None" = None,
        top_p: float | None = None,
        truncation: str | None = None,
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
            reasoning: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
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

        response_level_params = {
            "instructions_override": instructions_override,
            "max_completion_tokens": max_completion_tokens,
            "max_prompt_tokens": max_prompt_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "reasoning": reasoning,
            "temperature": temperature,
            "text": text,
            "tools": tools,
            "top_p": top_p,
            "truncation": truncation,
        }
        response_level_params = {k: v for k, v in response_level_params.items() if v is not None}

        function_choice_behavior = function_choice_behavior or self.function_choice_behavior

        async for message in ResponseAgentThreadActions.invoke_stream(
            agent=self,
            chat_history=chat_history,
            kernel=kernel,
            arguments=arguments,
            messages=messages,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
        ):
            yield message

    # endregion
