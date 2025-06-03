# Copyright (c) Microsoft. All rights reserved.

import inspect
import json
import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable, Iterable
from copy import deepcopy
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar

from azure.ai.agents.models import Agent as AzureAIAgentModel
from azure.ai.agents.models import (
    AzureAISearchQueryType,
    AzureAISearchTool,
    BingGroundingTool,
    CodeInterpreterTool,
    FileSearchTool,
    OpenApiAnonymousAuthDetails,
    OpenApiTool,
    ResponseFormatJsonSchemaType,
    ThreadMessageOptions,
    ToolDefinition,
    ToolResources,
    TruncationObject,
)
from azure.ai.projects.aio import AIProjectClient
from pydantic import Field

from semantic_kernel.agents import (
    Agent,
    AgentResponseItem,
    AgentSpec,
    AgentThread,
    AzureAIAgentSettings,
    DeclarativeSpecMixin,
    ToolSpec,
    register_agent_type,
)
from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_channel import AzureAIChannel
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInitializationException,
    AgentInvokeException,
    AgentThreadOperationException,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, SEMANTIC_KERNEL_USER_AGENT

if TYPE_CHECKING:
    from azure.ai.agents.models import ToolResources
    from azure.identity.aio import DefaultAzureCredential

    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel_pydantic import KernelBaseSettings

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

AgentsApiResponseFormatOption = str | ResponseFormatJsonSchemaType

_T = TypeVar("_T", bound="AzureAIAgent")


# region Declarative Spec

_TOOL_BUILDERS: dict[str, Callable[[ToolSpec, Kernel | None], ToolDefinition]] = {}


def _register_tool(tool_type: str):
    def decorator(fn: Callable[[ToolSpec, Kernel | None], ToolDefinition]):
        _TOOL_BUILDERS[tool_type.lower()] = fn
        return fn

    return decorator


@_register_tool("azure_ai_search")
def _azure_ai_search(spec: ToolSpec) -> AzureAISearchTool:
    opts = spec.options or {}

    connections = opts.get("tool_connections")
    if not connections or not isinstance(connections, list) or not connections[0]:
        raise AgentInitializationException(f"Missing or malformed 'tool_connections' in: {spec}")
    conn_id = connections[0]

    index_name = opts.get("index_name")
    if not index_name or not isinstance(index_name, str):
        raise AgentInitializationException(f"Missing or malformed 'index_name' in: {spec}")

    raw_query_type = opts.get("query_type", AzureAISearchQueryType.SIMPLE)
    if type(raw_query_type) is str:
        try:
            query_type = AzureAISearchQueryType(raw_query_type.lower())
        except ValueError:
            raise AgentInitializationException(f"Invalid query_type '{raw_query_type}' in: {spec}")
    else:
        query_type = raw_query_type

    filter_expr = opts.get("filter", "")

    top_k = opts.get("top_k", 5)
    if not isinstance(top_k, int):
        raise AgentInitializationException(f"'top_k' must be an integer in: {spec}")

    return AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name,
        query_type=query_type,
        filter=filter_expr,
        top_k=top_k,
    )


@_register_tool("azure_function")
def _azure_function(spec: ToolSpec) -> ToolDefinition:
    # TODO(evmattso): Implement Azure Function tool support
    raise NotImplementedError("Azure Function tools are not yet supported with the Azure AI Agent Declarative Spec.")


@_register_tool("bing_grounding")
def _bing_grounding(spec: ToolSpec) -> BingGroundingTool:
    opts = spec.options or {}

    connections = spec.options.get("tool_connections")
    if not connections or not isinstance(connections, list) or not connections[0]:
        raise AgentInitializationException(f"Missing or malformed 'tool_connections' in: {spec}")
    conn_id = connections[0]

    market = opts.get("market", "")
    set_lang = opts.get("set_lang", "")
    count = opts.get("count", 5)
    if not isinstance(count, int):
        raise AgentInitializationException(f"'count' must be an integer in: {spec}")
    freshness = opts.get("freshness", "")

    return BingGroundingTool(connection_id=conn_id, market=market, set_lang=set_lang, count=count, freshness=freshness)


@_register_tool("code_interpreter")
def _code_interpreter(spec: ToolSpec) -> CodeInterpreterTool:
    file_ids = spec.options.get("file_ids")
    return CodeInterpreterTool(file_ids=file_ids) if file_ids else CodeInterpreterTool()


@_register_tool("file_search")
def _file_search(spec: ToolSpec) -> FileSearchTool:
    vector_store_ids = spec.options.get("vector_store_ids")
    if not vector_store_ids or not isinstance(vector_store_ids, list) or not vector_store_ids[0]:
        raise AgentInitializationException(f"Missing or malformed 'vector_store_ids' in: {spec}")
    return FileSearchTool(vector_store_ids=vector_store_ids)


@_register_tool("function")
def _function(spec: ToolSpec, kernel: "Kernel") -> ToolDefinition:
    def parse_fqn(fqn: str) -> tuple[str, str]:
        parts = fqn.split(".")
        if len(parts) != 2:
            raise AgentInitializationException(f"Function `{fqn}` must be in the form `pluginName.functionName`.")
        return parts[0], parts[1]

    if not spec.id:
        raise AgentInitializationException("Function ID is required for function tools.")
    plugin_name, function_name = parse_fqn(spec.id)
    funcs = kernel.get_list_of_function_metadata_filters({"included_functions": f"{plugin_name}-{function_name}"})

    match len(funcs):
        case 0:
            raise AgentInitializationException(f"Function `{spec.id}` not found in kernel.")
        case 1:
            return kernel_function_metadata_to_function_call_format(funcs[0])  # type: ignore[return-value]
        case _:
            raise AgentInitializationException(f"Multiple definitions found for `{spec.id}`. Please remove duplicates.")


@_register_tool("openapi")
def _openapi(spec: ToolSpec) -> OpenApiTool:
    opts = spec.options or {}

    if not spec.id:
        raise AgentInitializationException("OpenAPI tool requires a non-empty 'id' (used as name).")
    if not spec.description:
        raise AgentInitializationException(f"OpenAPI tool '{spec.id}' requires a 'description'.")

    raw_spec = opts.get("specification")
    if not raw_spec:
        raise AgentInitializationException(f"OpenAPI tool '{spec.id}' is missing required 'specification' field.")

    try:
        parsed_spec = json.loads(raw_spec) if isinstance(raw_spec, str) else raw_spec
    except json.JSONDecodeError as e:
        raise AgentInitializationException(f"Invalid JSON in OpenAPI 'specification' field: {e}") from e

    auth = opts.get("auth", OpenApiAnonymousAuthDetails())

    return OpenApiTool(
        name=spec.id,
        description=spec.description,
        spec=parsed_spec,
        auth=auth,
        default_parameters=opts.get("default_parameters"),
    )


def _build_tool(spec: ToolSpec, kernel: "Kernel") -> ToolDefinition:
    if not spec.type:
        raise AgentInitializationException("Tool spec must include a 'type' field.")

    try:
        builder = _TOOL_BUILDERS[spec.type.lower()]
    except KeyError as exc:
        raise AgentInitializationException(f"Unsupported tool type: {spec.type}") from exc

    sig = inspect.signature(builder)
    return builder(spec) if len(sig.parameters) == 1 else builder(spec, kernel)  # type: ignore[call-arg]


def _build_tool_resources(tool_defs: list[ToolDefinition]) -> ToolResources | None:
    """Collects tool resources from known tool types with resource needs."""
    resources: dict[str, Any] = {}

    for tool in tool_defs:
        if isinstance(tool, CodeInterpreterTool):
            resources["code_interpreter"] = tool.resources.code_interpreter
        elif isinstance(tool, AzureAISearchTool):
            resources["azure_ai_search"] = tool.resources.azure_ai_search
        elif isinstance(tool, FileSearchTool):
            resources["file_search"] = tool.resources.file_search

    return ToolResources(**resources) if resources else None


# endregion

# region Thread


@experimental
class AzureAIAgentThread(AgentThread):
    """Azure AI Agent Thread class."""

    def __init__(
        self,
        *,
        client: AIProjectClient,
        messages: list[ThreadMessageOptions] | None = None,
        metadata: dict[str, str] | None = None,
        thread_id: str | None = None,
        tool_resources: "ToolResources | None" = None,
    ) -> None:
        """Initialize the Azure AI Agent Thread.

        Args:
            client: The Azure AI Project client.
            messages: The messages to initialize the thread with.
            metadata: The metadata for the thread.
            thread_id: The ID of the thread
            tool_resources: The tool resources for the thread.
        """
        super().__init__()

        if client is None:
            raise ValueError("Client cannot be None")

        self._client = client
        self._id = thread_id
        self._messages = messages or []
        self._metadata = metadata
        self._tool_resources = tool_resources

    @override
    async def _create(self) -> str:
        """Starts the thread and returns its ID."""
        try:
            response = await self._client.agents.threads.create(
                messages=self._messages,
                metadata=self._metadata,
                tool_resources=self._tool_resources,
            )
        except Exception as ex:
            raise AgentThreadOperationException(
                "The thread could not be created due to an error response from the service."
            ) from ex
        return response.id

    @override
    async def _delete(self) -> None:
        """Ends the current thread."""
        if self._id is None:
            raise AgentThreadOperationException("The thread cannot be deleted because it has not been created yet.")
        try:
            await self._client.agents.threads.delete(self._id)
        except Exception as ex:
            raise AgentThreadOperationException(
                "The thread could not be deleted due to an error response from the service."
            ) from ex

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        if isinstance(new_message, str):
            new_message = ChatMessageContent(role=AuthorRole.USER, content=new_message)

        if (
            not new_message.metadata
            or "thread_id" not in new_message.metadata
            or new_message.metadata["thread_id"] != self.id
        ):
            assert self.id is not None  # nosec
            await AgentThreadActions.create_message(self._client, self.id, new_message)

    async def get_messages(self, sort_order: Literal["asc", "desc"] = "desc") -> AsyncIterable[ChatMessageContent]:
        """Get the messages in the thread.

        Args:
            sort_order: The order to sort the messages in. Either "asc" or "desc".

        Yields:
            An AsyncIterable of ChatMessageContent of the messages in the thread.
        """
        if self._is_deleted:
            raise ValueError("The thread has been deleted.")
        if self._id is None:
            await self.create()
        assert self.id is not None  # nosec
        async for message in AgentThreadActions.get_messages(self._client, self.id, sort_order=sort_order):
            yield message


@experimental
@register_agent_type("foundry_agent")
class AzureAIAgent(DeclarativeSpecMixin, Agent):
    """Azure AI Agent class."""

    client: AIProjectClient
    definition: AzureAIAgentModel
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)

    channel_type: ClassVar[type[AgentChannel]] = AzureAIChannel

    def __init__(
        self,
        *,
        arguments: "KernelArguments | None" = None,
        client: AIProjectClient,
        definition: AzureAIAgentModel,
        kernel: "Kernel | None" = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        polling_options: RunPollingOptions | None = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Azure AI Agent.

        Args:
            arguments: The KernelArguments instance
            client: The AzureAI Project client. See "Quickstart: Create a new agent" guide
                https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure
                for details on how to create a new agent.
            definition: The AzureAI Agent model created via the AzureAI Project client.
            kernel: The Kernel instance used if invoking plugins
            plugins: The plugins for the agent. If plugins are included along with a kernel, any plugins
                that already exist in the kernel will be overwritten.
            polling_options: The polling options for the agent.
            prompt_template_config: The prompt template configuration. If this is provided along with
                instructions, the prompt template will be used in place of the instructions.
            **kwargs: Additional keyword arguments
        """
        args: dict[str, Any] = {
            "client": client,
            "definition": definition,
            "name": definition.name or f"azure_agent_{generate_random_ascii_name(length=8)}",
            "description": definition.description,
        }

        if definition.id is not None:
            args["id"] = definition.id
        if kernel is not None:
            args["kernel"] = kernel
        if arguments is not None:
            args["arguments"] = arguments
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
        if definition.instructions is not None:
            args["instructions"] = definition.instructions
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
    def create_client(
        credential: "DefaultAzureCredential",
        endpoint: str | None = None,
        api_version: str | None = None,
        **kwargs: Any,
    ) -> AIProjectClient:
        """Create the Azure AI Project client using the connection string.

        Args:
            credential: The credential
            endpoint: The Azure AI Foundry endpoint
            api_version: Optional API version to use
            kwargs: Additional keyword arguments

        Returns:
            AIProjectClient: The Azure AI Project client
        """
        if endpoint is None:
            ai_agent_settings = AzureAIAgentSettings()
            if not ai_agent_settings.endpoint:
                raise AgentInitializationException("Please provide a valid Azure AI endpoint.")
            endpoint = ai_agent_settings.endpoint

        client_kwargs: dict[str, Any] = {
            **kwargs,
            **({"user_agent": SEMANTIC_KERNEL_USER_AGENT} if APP_INFO else {}),
        }

        if api_version:
            client_kwargs["api_version"] = api_version

        return AIProjectClient(
            credential=credential,
            endpoint=endpoint,
            **client_kwargs,
        )

    # region Declarative Spec

    @override
    @classmethod
    async def _from_dict(
        cls: type[_T],
        data: dict,
        *,
        kernel: Kernel,
        prompt_template_config: PromptTemplateConfig | None = None,
        **kwargs,
    ) -> _T:
        """Create an Azure AI Agent from the provided dictionary.

        Args:
            data: The dictionary containing the agent data.
            kernel: The kernel to use for the agent.
            prompt_template_config: The prompt template configuration.
            kwargs: Additional keyword arguments. Note: unsupported keys may raise validation errors.

        Returns:
            AzureAIAgent: The Azure AI Agent instance.
        """
        client: AIProjectClient = kwargs.pop("client", None)
        if client is None:
            raise AgentInitializationException("Missing required 'client' in AzureAIAgent._from_dict()")

        spec = AgentSpec.model_validate(data)

        if "settings" in kwargs:
            kwargs.pop("settings")

        args = data.pop("arguments", None)
        arguments = None
        if args:
            arguments = KernelArguments(**args)

        if spec.id:
            existing_definition = await client.agents.get_agent(spec.id)

            # Create a mutable clone
            definition = deepcopy(existing_definition)

            # Selectively override attributes from spec
            if spec.name is not None:
                setattr(definition, "name", spec.name)
            if spec.description is not None:
                setattr(definition, "description", spec.description)
            if spec.instructions is not None:
                setattr(definition, "instructions", spec.instructions)
            if spec.extras:
                merged_metadata = dict(getattr(definition, "metadata", {}) or {})
                merged_metadata.update(spec.extras)
                setattr(definition, "metadata", merged_metadata)

            return cls(
                definition=definition,
                client=client,
                kernel=kernel,
                prompt_template_config=prompt_template_config,
                arguments=arguments,
                **kwargs,
            )

        if not (spec.model and spec.model.id):
            raise ValueError("model.id required when creating a new Azure AI agent")

        # Build tool definitions & resources
        tool_objs = [_build_tool(t, kernel) for t in spec.tools if t.type != "function"]
        tool_defs = [d for tool in tool_objs for d in (tool.definitions if hasattr(tool, "definitions") else [tool])]
        tool_resources = _build_tool_resources(tool_objs)

        try:
            agent_definition = await client.agents.create_agent(
                model=spec.model.id,
                name=spec.name,
                description=spec.description,
                instructions=spec.instructions,
                tools=tool_defs,
                tool_resources=tool_resources,
                metadata=spec.extras,
                **kwargs,
            )
        except Exception as ex:
            print(f"Error creating agent: {ex}")

        return cls(
            definition=agent_definition,
            client=client,
            kernel=kernel,
            arguments=arguments,
            prompt_template_config=prompt_template_config,
            **kwargs,
        )

    @override
    @classmethod
    def resolve_placeholders(
        cls: type[_T],
        yaml_str: str,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """Substitute ${AzureAI:Key} placeholders with fields from AzureAIAgentSettings and extras."""
        import re

        pattern = re.compile(r"\$\{([^}]+)\}")

        # Build the mapping only if settings is provided and valid
        field_mapping: dict[str, Any] = {}

        if settings is None:
            settings = AzureAIAgentSettings()

        if not isinstance(settings, AzureAIAgentSettings):
            raise AgentInitializationException(f"Expected AzureAIAgentSettings, got {type(settings).__name__}")

        field_mapping.update({
            "ChatModelId": getattr(settings, "model_deployment_name", None),
            "Endpoint": getattr(settings, "endpoint", None),
            "AgentId": getattr(settings, "agent_id", None),
            "BingConnectionId": getattr(settings, "bing_connection_id", None),
            "AzureAISearchConnectionId": getattr(settings, "azure_ai_search_connection_id", None),
            "AzureAISearchIndexName": getattr(settings, "azure_ai_search_index_name", None),
        })

        if extras:
            field_mapping.update(extras)

        def replacer(match: re.Match[str]) -> str:
            """Replace the matched placeholder with the corresponding value from field_mapping."""
            full_key = match.group(1)  # for example, AzureAI:AzureAISearchConnectionId
            section, _, key = full_key.partition(":")
            if section != "AzureAI":
                return match.group(0)

            # Try short key first (AzureAISearchConnectionId), then full (AzureAI:AzureAISearchConnectionId)
            return str(field_mapping.get(key) or field_mapping.get(full_key) or match.group(0))

        result = pattern.sub(replacer, yaml_str)

        # Safety check for unresolved placeholders
        unresolved = pattern.findall(result)
        if unresolved:
            raise AgentInitializationException(
                f"Unresolved placeholders in spec: {', '.join(f'${{{key}}}' for key in unresolved)}"
            )

        return result

    # endregion

    # region Invocation Methods

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: Kernel | None = None,
        model: str | None = None,
        instructions_override: str | None = None,
        additional_instructions: str | None = None,
        additional_messages: list[ThreadMessageOptions] | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        truncation_strategy: TruncationObject | None = None,
        response_format: AgentsApiResponseFormatOption | None = None,
        parallel_tool_calls: bool | None = None,
        metadata: dict[str, str] | None = None,
        polling_options: RunPollingOptions | None = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent on a thread.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the agent.
            arguments: The arguments for the agent.
            kernel: The kernel to use for the agent.
            model: The model to use for the agent.
            instructions_override: Instructions to override the default instructions.
            additional_instructions: Additional instructions for the agent.
            additional_messages: Additional messages for the agent.
            tools: Tools for the agent.
            temperature: Temperature for the agent.
            top_p: Top p for the agent.
            max_prompt_tokens: Maximum prompt tokens for the agent.
            max_completion_tokens: Maximum completion tokens for the agent.
            truncation_strategy: Truncation strategy for the agent.
            response_format: Response format for the agent.
            parallel_tool_calls: Whether to allow parallel tool calls.
            metadata: Metadata for the agent.
            polling_options: The polling options for the agent.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResponseItem[ChatMessageContent]: The response from the agent.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: AzureAIAgentThread(client=self.client),
            expected_type=AzureAIAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "model": model,
            "instructions_override": instructions_override,
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "tools": tools,
            "temperature": temperature,
            "top_p": top_p,
            "max_prompt_tokens": max_prompt_tokens,
            "max_completion_tokens": max_completion_tokens,
            "truncation_strategy": truncation_strategy,
            "response_format": response_format,
            "parallel_tool_calls": parallel_tool_calls,
            "polling_options": polling_options,
            "metadata": metadata,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        response_messages: list[ChatMessageContent] = []
        async for is_visible, response in AgentThreadActions.invoke(
            agent=self,
            thread_id=thread.id,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
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
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: Kernel | None = None,
        model: str | None = None,
        instructions_override: str | None = None,
        additional_instructions: str | None = None,
        additional_messages: list[ThreadMessageOptions] | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        truncation_strategy: TruncationObject | None = None,
        response_format: AgentsApiResponseFormatOption | None = None,
        parallel_tool_calls: bool | None = None,
        metadata: dict[str, str] | None = None,
        polling_options: RunPollingOptions | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke the agent on the specified thread.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to handle intermediate steps of the agent's execution.
            arguments: The arguments for the agent.
            kernel: The kernel to use for the agent.
            model: The model to use for the agent.
            instructions_override: Instructions to override the default instructions.
            additional_instructions: Additional instructions for the agent.
            additional_messages: Additional messages for the agent.
            tools: Tools for the agent.
            temperature: Temperature for the agent.
            top_p: Top p for the agent.
            max_prompt_tokens: Maximum prompt tokens for the agent.
            max_completion_tokens: Maximum completion tokens for the agent.
            truncation_strategy: Truncation strategy for the agent.
            response_format: Response format for the agent.
            parallel_tool_calls: Whether to allow parallel tool calls.
            polling_options: The polling options for the agent.
            metadata: Metadata for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            AgentResponseItem[ChatMessageContent]: The response from the agent.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: AzureAIAgentThread(client=self.client),
            expected_type=AzureAIAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "model": model,
            "instructions_override": instructions_override,
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "tools": tools,
            "temperature": temperature,
            "top_p": top_p,
            "max_prompt_tokens": max_prompt_tokens,
            "max_completion_tokens": max_completion_tokens,
            "truncation_strategy": truncation_strategy,
            "response_format": response_format,
            "parallel_tool_calls": parallel_tool_calls,
            "metadata": metadata,
            "polling_options": polling_options,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        async for is_visible, message in AgentThreadActions.invoke(
            agent=self,
            thread_id=thread.id,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
        ):
            message.metadata["thread_id"] = thread.id
            await thread.on_new_message(message)

            if is_visible:
                # Only yield visible messages
                yield AgentResponseItem(message=message, thread=thread)
            elif on_intermediate_message:
                # Emit tool-related messages only via callback
                await on_intermediate_message(message)

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        additional_instructions: str | None = None,
        additional_messages: list[ThreadMessageOptions] | None = None,
        instructions_override: str | None = None,
        kernel: Kernel | None = None,
        model: str | None = None,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_prompt_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        truncation_strategy: TruncationObject | None = None,
        response_format: AgentsApiResponseFormatOption | None = None,
        parallel_tool_calls: bool | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem["StreamingChatMessageContent"]]:
        """Invoke the agent on the specified thread with a stream of messages.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the agent.
            on_intermediate_message: A callback function to handle intermediate steps of the
                                     agent's execution as fully formed messages.
            arguments: The arguments for the agent.
            additional_instructions: Additional instructions for the agent.
            additional_messages: Additional messages for the agent.
            instructions_override: Instructions to override the default instructions.
            kernel: The kernel to use for the agent.
            model: The model to use for the agent.
            tools: Tools for the agent.
            temperature: Temperature for the agent.
            top_p: Top p for the agent.
            max_prompt_tokens: Maximum prompt tokens for the agent.
            max_completion_tokens: Maximum completion tokens for the agent.
            truncation_strategy: Truncation strategy for the agent.
            response_format: Response format for the agent.
            parallel_tool_calls: Whether to allow parallel tool calls.
            metadata: Metadata for the agent.
            **kwargs: Additional keyword arguments.

        Yields:
            AgentResponseItem[StreamingChatMessageContent]: The response from the agent.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: AzureAIAgentThread(client=self.client),
            expected_type=AzureAIAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        run_level_params = {
            "model": model,
            "instructions_override": instructions_override,
            "additional_instructions": additional_instructions,
            "additional_messages": additional_messages,
            "tools": tools,
            "temperature": temperature,
            "top_p": top_p,
            "max_prompt_tokens": max_prompt_tokens,
            "max_completion_tokens": max_completion_tokens,
            "truncation_strategy": truncation_strategy,
            "response_format": response_format,
            "parallel_tool_calls": parallel_tool_calls,
            "metadata": metadata,
        }
        run_level_params = {k: v for k, v in run_level_params.items() if v is not None}

        collected_messages: list[ChatMessageContent] | None = [] if on_intermediate_message else None

        start_idx = 0
        async for message in AgentThreadActions.invoke_stream(
            agent=self,
            thread_id=thread.id,
            output_messages=collected_messages,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
        ):
            # Before yielding the current streamed message, emit any new full messages first
            if collected_messages is not None:
                new_messages = collected_messages[start_idx:]
                start_idx = len(collected_messages)

                for new_msg in new_messages:
                    new_msg.metadata["thread_id"] = thread.id
                    await thread.on_new_message(new_msg)
                    if on_intermediate_message:
                        await on_intermediate_message(new_msg)

            # Now yield the current streamed content (StreamingTextContent)
            message.metadata["thread_id"] = thread.id
            yield AgentResponseItem(message=message, thread=thread)

    def get_channel_keys(self) -> Iterable[str]:
        """Get the channel keys.

        Returns:
            Iterable[str]: The channel keys.
        """
        # Distinguish from other channel types.
        yield f"{AzureAIAgent.__name__}"

        # Distinguish between different agent IDs
        yield self.id

        # Distinguish between agent names
        yield self.name

    async def create_channel(self, thread_id: str | None = None) -> AgentChannel:
        """Create a channel.

        Args:
            thread_id: The ID of the thread to create the channel for. If not provided
                a new thread will be created.
        """
        thread = AzureAIAgentThread(client=self.client, thread_id=thread_id)

        if thread.id is None:
            await thread.create()

        assert thread.id is not None  # nosec

        return AzureAIChannel(client=self.client, thread_id=thread.id)
