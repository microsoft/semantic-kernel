# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Iterable
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Agent as AzureAIAgentModel
from azure.ai.projects.models import (
    AgentsApiResponseFormat,
    AgentsApiResponseFormatMode,
    ResponseFormatJsonSchemaType,
    ThreadMessage,
    ThreadMessageOptions,
    ToolDefinition,
    TruncationObject,
)
from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_agent_settings import AzureAIAgentSettings
from semantic_kernel.agents.azure_ai.azure_ai_channel import AzureAIChannel
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
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

logger: logging.Logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from azure.identity.aio import DefaultAzureCredential

    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

AgentsApiResponseFormatOption = (
    str | AgentsApiResponseFormatMode | AgentsApiResponseFormat | ResponseFormatJsonSchemaType
)

_T = TypeVar("_T", bound="AzureAIAgent")


@experimental
class AzureAIAgent(Agent):
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
        conn_str: str | None = None,
        **kwargs: Any,
    ) -> AIProjectClient:
        """Create the Azure AI Project client using the connection string.

        Args:
            credential: The credential
            conn_str: The connection string
            kwargs: Additional keyword arguments

        Returns:
            AIProjectClient: The Azure AI Project client
        """
        if conn_str is None:
            ai_agent_settings = AzureAIAgentSettings.create()
            if not ai_agent_settings.project_connection_string:
                raise AgentInitializationException("Please provide a valid Azure AI connection string.")
            conn_str = ai_agent_settings.project_connection_string.get_secret_value()

        return AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=conn_str,
            **({"user_agent": SEMANTIC_KERNEL_USER_AGENT} if APP_INFO else {}),
            **kwargs,
        )

    async def add_chat_message(self, thread_id: str, message: str | ChatMessageContent) -> "ThreadMessage | None":
        """Add a chat message to the thread.

        Args:
            thread_id: The ID of the thread
            message: The chat message to add

        Returns:
            ThreadMessage | None: The thread message
        """
        return await AgentThreadActions.create_message(client=self.client, thread_id=thread_id, message=message)

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        thread_id: str,
        arguments: KernelArguments | None = None,
        kernel: Kernel | None = None,
        # Run-level parameters:
        *,
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
        **kwargs: Any,
    ) -> ChatMessageContent:
        """Get a response from the agent on a thread."""
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

        messages: list[ChatMessageContent] = []
        async for is_visible, message in AgentThreadActions.invoke(
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
        arguments: KernelArguments | None = None,
        kernel: Kernel | None = None,
        # Run-level parameters:
        *,
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
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent on the specified thread."""
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

        async for is_visible, message in AgentThreadActions.invoke(
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
        messages: list[ChatMessageContent] | None = None,
        kernel: Kernel | None = None,
        arguments: KernelArguments | None = None,
        # Run-level parameters:
        *,
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
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the agent on the specified thread with a stream of messages."""
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

        async for message in AgentThreadActions.invoke_stream(
            agent=self,
            thread_id=thread_id,
            messages=messages,
            kernel=kernel,
            arguments=arguments,
            **run_level_params,  # type: ignore
        ):
            yield message

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

        # Distinguish between different scopes
        yield str(self.client.scope)

    async def create_channel(self) -> AgentChannel:
        """Create a channel."""
        thread_id = await AgentThreadActions.create_thread(self.client)

        return AzureAIChannel(client=self.client, thread_id=thread_id)
