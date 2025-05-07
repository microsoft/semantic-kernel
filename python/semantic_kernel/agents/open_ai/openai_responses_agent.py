# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from copy import copy
from typing import TYPE_CHECKING, Any, Literal

from openai import AsyncOpenAI
from openai.lib._parsing._responses import type_to_text_format_param
from openai.types.responses.computer_tool_param import ComputerToolParam
from openai.types.responses.file_search_tool_param import FileSearchToolParam, RankingOptions
from openai.types.responses.response_format_text_config_param import ResponseFormatText
from openai.types.responses.response_format_text_json_schema_config_param import ResponseFormatTextJSONSchemaConfigParam
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from openai.types.responses.tool_param import ToolParam
from openai.types.responses.web_search_tool_param import UserLocation, WebSearchToolParam
from openai.types.shared_params.comparison_filter import ComparisonFilter
from openai.types.shared_params.compound_filter import CompoundFilter
from openai.types.shared_params.response_format_json_object import ResponseFormatJSONObject
from pydantic import BaseModel, Field, ValidationError

from semantic_kernel.agents import Agent
from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.agents.open_ai.responses_agent_thread_actions import ResponsesAgentThreadActions
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInitializationException,
    AgentInvokeException,
    AgentThreadOperationException,
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

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

if TYPE_CHECKING:
    from openai import AsyncOpenAI

    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

ResponseFormatUnion = ResponseFormatText | ResponseFormatTextJSONSchemaConfigParam | ResponseFormatJSONObject

logger: logging.Logger = logging.getLogger(__name__)

# region Agent Thread


@experimental
class ResponsesAgentThread(AgentThread):
    """Azure OpenAI and OpenAI Responses Agent Thread class."""

    def __init__(
        self,
        client: AsyncOpenAI,
        chat_history: ChatHistory | None = None,
        previous_response_id: str | None = None,
        enable_store: bool | None = True,
    ) -> None:
        """Initialize the Responses Agent Thread.

        Args:
            client: The OpenAI client.
            chat_history: The chat history for the thread. If None, a new ChatHistory instance will be created.
            previous_response_id: The previous response ID of the thread. This is used when creating a new thread
                to continue the conversation.
            enable_store: Whether to enable storing the thread. If None, it will be set to True.
        """
        self._client = client
        self._chat_history = ChatHistory() if chat_history is None else chat_history
        self._is_deleted = False
        self._enable_store = enable_store or True
        self._response_id: str | None = previous_response_id

    def __len__(self) -> int:
        """Returns the length of the chat history."""
        return len(self._chat_history)

    @property
    def response_id(self) -> str | None:
        """Get the response ID."""
        return self._response_id

    @response_id.setter
    def response_id(self, value: str | None) -> None:
        """Set the response ID."""
        self._response_id = value

    @property
    def store_enabled(self) -> bool:
        """Check if the store is enabled."""
        return self._enable_store

    @override
    @property
    def id(self) -> str | None:
        """Get the thread ID."""
        return self.response_id

    @override
    async def _create(self) -> str:
        """Starts the thread and returns its ID."""
        if self._is_deleted:
            raise AgentThreadOperationException(
                "Cannot create a new thread, since the current thread has been deleted."
            )
        self._enable_store = True

        # The ID isn't available until after a message is sent
        return ""

    @override
    async def _delete(self) -> None:
        """Ends the current thread."""
        if self._is_deleted:
            return
        if self.response_id is None:
            raise AgentThreadOperationException("Cannot delete the thread, since it has not been created.")
        self._chat_history.clear()
        self._is_deleted = True

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        if isinstance(new_message, str):
            new_message = ChatMessageContent(role=AuthorRole.USER, content=new_message)

        if not self.response_id:
            self._chat_history.add_message(new_message)

    async def get_messages(
        self, limit: int | None = None, sort_order: Literal["asc", "desc"] | None = "desc"
    ) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the current chat history."""
        if self._is_deleted:
            raise AgentThreadOperationException("Cannot retrieve chat history, since the thread has been deleted.")
        if self.store_enabled and self.response_id is not None:
            async for message in ResponsesAgentThreadActions.get_messages(
                self._client,
                self.response_id,
                limit=limit,
                sort_order=sort_order,
            ):
                yield message
        else:
            for message in self._chat_history.messages:
                yield message

    async def reduce(self) -> ChatHistory | None:
        """Reduce the chat history to a smaller size."""
        if self._id is None:
            raise AgentThreadOperationException("Cannot reduce chat history, since the thread is not currently active.")
        if not isinstance(self._chat_history, ChatHistoryReducer):
            return None
        return await self._chat_history.reduce()


# endregion


@experimental
class OpenAIResponsesAgent(Agent):
    """OpenAI Responses Agent class.

    Provides the ability to interact with OpenAI's Responses API.

    NOTE: The Responses Agent does not currently support AgentGroupChat.
    """

    # region Agent Initialization

    ai_model_id: str
    client: AsyncOpenAI
    function_choice_behavior: FunctionChoiceBehavior = Field(default_factory=lambda: FunctionChoiceBehavior.Auto())
    instruction_role: str = Field(default="developer")
    metadata: dict[str, Any] = Field(default_factory=dict)
    temperature: float | None = Field(default=None)
    top_p: float | None = Field(default=None)
    plugins: list[Any] = Field(default_factory=list)
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)
    store_enabled: bool = Field(default=True, description="Whether to store responses.")
    text: dict[str, Any] = Field(default_factory=dict)
    tools: list[ToolParam] = Field(default_factory=list)

    def __init__(
        self,
        *,
        ai_model_id: str,
        client: AsyncOpenAI,
        arguments: KernelArguments | None = None,
        description: str | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        id: str | None = None,
        instruction_role: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        metadata: dict[str, str] | None = None,
        name: str | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        polling_options: RunPollingOptions | None = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        store_enabled: bool | None = None,
        temperature: float | None = None,
        text: ResponseTextConfigParam | None = None,
        tools: list[ToolParam] | None = None,
        top_p: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAI Responses Agent.

        Args:
            ai_model_id: The AI model ID.
            client: The OpenAI client.
            arguments: The arguments to pass to the function.
            description: The description of the agent.
            function_choice_behavior: The function choice behavior to determine how and which plugins are
                advertised to the model.
            id: The ID of the agent.
            instruction_role: The role of the agent, either developer or system.
            instructions: The instructions for the agent.
            kernel: The Kernel instance.
            metadata: The metadata for the agent.
            name: The name of the agent.
            plugins: The plugins to add to the kernel. If both the plugins and the kernel are supplied,
                the plugins take precedence and are added to the kernel by default.
            polling_options: The polling options.
            prompt_template_config: The prompt template configuration.
            store_enabled: Whether to enable storing the responses from the agent.
            temperature: The temperature for the agent.
            text: The text/response format configuration for the agent.
            tools: The tools to use with the agent.
            top_p: The top p value for the agent.
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
        if instruction_role is not None:
            args["instruction_role"] = instruction_role
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
        if store_enabled is not None:
            args["store_enabled"] = store_enabled
        if temperature is not None:
            args["temperature"] = temperature
        if text is not None:
            args["text"] = text
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
            openai_settings = OpenAISettings(
                responses_model_id=ai_model_id,
                api_key=api_key,
                org_id=org_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationException("Failed to create OpenAI settings.", ex) from ex

        if not openai_settings.api_key:
            raise AgentInitializationException("The OpenAI API key is required.")

        if not openai_settings.responses_model_id:
            raise AgentInitializationException("The OpenAI Responses model ID is required.")

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

        return client, openai_settings.responses_model_id

    # endregion

    # region Tool Handling

    @staticmethod
    def configure_file_search_tool(
        vector_store_ids: str | list[str],
        filters: ComparisonFilter | CompoundFilter | None = None,
        max_num_results: int | None = None,
        score_threshold: float | None = None,
        ranker: Literal["auto", "default-2024-11-15"] | None = None,
    ) -> FileSearchToolParam:
        """Generate the file search tool param.

        Args:
            vector_store_ids: Single or list of vector store IDs.
            filters: A filter to apply based on file attributes.
                - ComparisonFilter: A single filter.
                - CompoundFilter: A compound filter.
            max_num_results: Optional override for maximum results (1 to 50).
            score_threshold: Floating point threshold between 0 and 1.
            ranker: The ranker to use ('auto' or 'default_2024_08_21').
            kwargs: Any extra arguments needed by ToolResourcesFileSearch.

        Returns:
            A FileSearchToolParam dictionary with any passed-in parameters.
        """
        if isinstance(vector_store_ids, str):
            vector_store_ids = [vector_store_ids]

        tool: FileSearchToolParam = {
            "type": "file_search",
            "vector_store_ids": vector_store_ids,
        }

        if filters is not None:
            tool["filters"] = filters

        if max_num_results is not None:
            tool["max_num_results"] = max_num_results

        ranking_options: RankingOptions = {}
        if score_threshold is not None:
            ranking_options["score_threshold"] = score_threshold
        if ranker is not None:
            ranking_options["ranker"] = ranker

        if ranking_options:
            tool["ranking_options"] = ranking_options

        return tool

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
    def configure_computer_use_tool() -> ComputerToolParam:
        """Generate the tool definition for computer use."""
        raise NotImplementedError("Computer use tool is not implemented yet.")

    @staticmethod
    def _generate_structured_output_response_format_schema(name: str, schema: dict) -> dict:
        """Mock function to simulate formatting the final schema with 'strict' = True."""
        return {"type": "json_schema", "name": name, "schema": schema, "strict": True}

    @staticmethod
    def configure_response_format(
        response_format: ResponseFormatUnion
        | dict[Literal["type"], Literal["text", "json_object"]]
        | dict[str, Any]
        | type[BaseModel]
        | type
        | None = None,
    ) -> dict[str, Any] | None:
        """Form the response format.

            {
              "text": {
                "format": {
                  "name": "<some_name>",
                  "type": "json_schema",
                  "schema": { ... },
                  "strict": true
                }
              }
            }

        "auto" is the default value. Not configuring the response format will result in the model
        outputting text.

        Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
        Outputs which ensures the model will match your supplied JSON schema.

        Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
        message the model generates is valid JSON, as long as the prompt contains "JSON."

        Args:
            response_format: The response format.

        Returns:
            The final dict containing `text.format` if JSON-based, or None if "auto".
        """
        if response_format is None or response_format == "auto":
            return None

        # TODO(evmattso): improve typing in this method
        if isinstance(response_format, dict):
            resp_type = response_format.get("type", None)

            if resp_type == "json_object":
                return {"type": "json_object"}
            if resp_type == "json_schema":
                json_schema = response_format.get("json_schema")  # type: ignore
                if not isinstance(json_schema, dict):
                    raise AgentInitializationException(
                        "If response_format has type 'json_schema', 'json_schema' must be a valid dictionary."
                    )
                # We're assuming the response_format has already been provided in the correct format
                return response_format  # type: ignore

            raise AgentInitializationException(
                f"Encountered unexpected response_format type: {resp_type}. Allowed types are `json_object` "
                " and `json_schema`."
            )
        if isinstance(response_format, type):
            if issubclass(response_format, BaseModel):
                interim_format = type_to_text_format_param(response_format)
                if interim_format["type"] != "json_schema":
                    raise AgentInitializationException("Only 'json_schema' is allowed from that helper.")
                configured_format = {
                    "type": "json_schema",
                    "name": interim_format.get("name", response_format.__name__),
                    "schema": interim_format.get("schema"),
                    "strict": interim_format.get("strict", True),
                }
            else:
                # Build a schema from a plain Python class
                generated_schema = KernelJsonSchemaBuilder.build(parameter_type=response_format, structured_output=True)
                if generated_schema is None:
                    raise AgentInitializationException(f"Could not generate schema for the type {response_format}.")
                configured_format = {
                    "type": "json_schema",
                    "name": response_format.__name__,
                    "schema": generated_schema,
                    "strict": True,
                }
        else:
            raise AgentInitializationException(
                "response_format must be a dictionary, a subclass of BaseModel, a Python class/type, or None"
            )

        return {"format": configured_format}

    # endregion

    # region Invocation Methods

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instruction_role: str | None = None,
        instructions_override: str | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        polling_options: RunPollingOptions | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[ToolParam] | None" = None,
        temperature: float | None = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent on a thread.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            arguments: The kernel arguments.
            kernel: The kernel.
            include: Additional output data to include in the response.
            instruction_role: The instruction role, either developer or system.
            instructions_override: The instructions override.
            function_choice_behavior: The function choice behavior.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_output_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model to override on a per-run basis.
            parallel_tool_calls: Parallel tool calls.
            polling_options: The polling options at the run-level.
            reasoning: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
            kwargs: Additional keyword arguments.

        Returns:
            ResponseMessageContent: The response from the agent.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: ResponsesAgentThread(client=self.client, enable_store=self.store_enabled),
            expected_type=ResponsesAgentThread,
        )

        chat_history = self._prepare_input_message(messages)

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        response_level_params = {
            "include": include,
            "instruction_role": instruction_role,
            "instructions_override": instructions_override,
            "max_output_tokens": max_output_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "polling_options": polling_options,
            "reasoning_effort": reasoning,
            "text": text,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation": truncation,
        }
        response_level_params = {k: v for k, v in response_level_params.items() if v is not None}

        function_choice_behavior = function_choice_behavior or self.function_choice_behavior
        assert function_choice_behavior is not None  # nosec

        response_messages: list[ChatMessageContent] = []
        async for is_visible, response in ResponsesAgentThreadActions.invoke(
            agent=self,
            chat_history=chat_history,
            thread=thread,
            store_enabled=self.store_enabled,
            kernel=kernel,
            arguments=arguments,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
        ):
            if is_visible and response.metadata.get("code") is not True:
                response.metadata["thread_id"] = thread.id
                response_messages.append(response)

        if not response_messages:
            raise AgentInvokeException("No response messages were returned from the agent.")
        final_message = response_messages[-1]
        await thread.on_new_message(final_message)
        return AgentResponseItem(message=final_message, thread=thread)

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instructions_override: str | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        polling_options: RunPollingOptions | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        temperature: float | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[ToolParam] | None" = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke the agent.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to handle intermediate steps of the agent's execution.
            arguments: The kernel arguments.
            kernel: The kernel.
            include: Additional output data to include in the response.
            instructions_override: The instructions override.
            function_choice_behavior: The function choice behavior.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_output_tokens: The maximum completion tokens.
            max_prompt_tokens: The maximum prompt tokens.
            metadata: The metadata.
            model: The model to override on a per-run basis.
            parallel_tool_calls: Parallel tool calls.
            polling_options: The polling options at the run-level.
            reasoning: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: ResponsesAgentThread(client=self.client, enable_store=self.store_enabled),
            expected_type=ResponsesAgentThread,
        )

        chat_history = self._prepare_input_message(messages)

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        response_level_params = {
            "include": include,
            "instructions_override": instructions_override,
            "max_output_tokens": max_output_tokens,
            "metadata": metadata,
            "model": model,
            "parallel_tool_calls": parallel_tool_calls,
            "polling_options": polling_options,
            "reasoning": reasoning,
            "text": text,
            "temperature": temperature,
            "tools": tools,
            "top_p": top_p,
            "truncation": truncation,
        }
        response_level_params = {k: v for k, v in response_level_params.items() if v is not None}

        function_choice_behavior = function_choice_behavior or self.function_choice_behavior
        assert function_choice_behavior is not None  # nosec

        async for is_visible, response in ResponsesAgentThreadActions.invoke(
            agent=self,
            chat_history=chat_history,
            thread=thread,
            store_enabled=self.store_enabled,
            kernel=kernel,
            arguments=arguments,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
        ):
            response.metadata["thread_id"] = thread.id
            await thread.on_new_message(response)
            if on_intermediate_message:
                await on_intermediate_message(response)

            if is_visible:
                yield AgentResponseItem(message=response, thread=thread)

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        include: list[
            Literal[
                "file_search_call.results", "message.input_image.image_url", "computer_call_output.output.image_url"
            ]
        ]
        | None = None,
        instructions_override: str | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        model: str | None = None,
        parallel_tool_calls: bool | None = None,
        reasoning: Literal["low", "medium", "high"] | None = None,
        temperature: float | None = None,
        text: "ResponseTextConfigParam | None" = None,
        tools: "list[ToolParam] | None" = None,
        top_p: float | None = None,
        truncation: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Invoke the agent.

        Args:
            messages: The messages to send to the agent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to handle intermediate steps of the
                                     agent's execution as fully formed messages.
            arguments: The kernel arguments.
            kernel: The kernel.
            include: Additional output data to include in the response.
            instructions_override: The instructions override.
            function_choice_behavior: The function choice behavior.
            include: Additional output data to include in the model response.
            additional_instructions: Additional instructions.
            additional_messages: Additional messages.
            max_output_tokens: The maximum completion tokens.
            metadata: The metadata.
            model: The model to override on a per-run basis.
            parallel_tool_calls: Parallel tool calls.
            reasoning: The reasoning effort.
            text: The response format.
            tools: The tools.
            temperature: The temperature.
            top_p: The top p.
            truncation: The truncation strategy.
            kwargs: Additional keyword arguments.

        Yields:
            The chat message content.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,  # type: ignore
            thread=thread,
            construct_thread=lambda: ResponsesAgentThread(client=self.client, enable_store=self.store_enabled),
            expected_type=ResponsesAgentThread,
        )

        chat_history = self._prepare_input_message(messages)

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        response_level_params = {
            "include": include,
            "instructions_override": instructions_override,
            "max_output_tokens": max_output_tokens,
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
        assert function_choice_behavior is not None  # nosec

        collected_messages: list[ChatMessageContent] | None = [] if on_intermediate_message else None

        async for response in ResponsesAgentThreadActions.invoke_stream(
            agent=self,
            chat_history=chat_history,
            thread=thread,
            store_enabled=self.store_enabled,
            kernel=kernel,
            arguments=arguments,
            output_messages=collected_messages,
            function_choice_behavior=function_choice_behavior,
            **response_level_params,  # type: ignore
        ):
            response.metadata["thread_id"] = thread.id
            yield AgentResponseItem(message=response, thread=thread)

        for message in collected_messages or []:
            message.metadata["thread_id"] = thread.id
            await thread.on_new_message(message)
            if on_intermediate_message:
                await on_intermediate_message(message)

    def _prepare_input_message(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
    ) -> ChatHistory:
        """Prepare the input message for the agent.

        Args:
            messages: The messages to send to the agent.

        Returns:
            The chat history with the input messages.
        """
        if messages is None:
            messages = []

        if isinstance(messages, (str, ChatMessageContent)):
            messages = [messages]

        normalized_messages = [
            ChatMessageContent(role=AuthorRole.USER, content=msg) if isinstance(msg, str) else msg for msg in messages
        ]

        return ChatHistory(messages=normalized_messages)

    # endregion
