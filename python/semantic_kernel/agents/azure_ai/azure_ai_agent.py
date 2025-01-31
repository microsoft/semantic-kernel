# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar, Iterable

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Agent as AzureAIAgentModel
from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_channel import AzureAIChannel
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import trace_agent_invocation

logger: logging.Logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class AzureAIAgent(Agent):
    """Azure AI Agent class."""

    client: AIProjectClient
    definition: AzureAIAgentModel
    polling_options: RunPollingOptions = Field(default_factory=RunPollingOptions)

    channel_type: ClassVar[type[AgentChannel]] = AzureAIChannel

    def __init__(
        self,
        *,
        client: AIProjectClient,
        definition: AzureAIAgentModel,
        kernel: "Kernel | None" = None,
        arguments: "KernelArguments | None" = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Azure AI Agent.

        Args:
            client: The AzureAI Project client
            definition: The AzureAI Agent model
            kernel: The Kernel instance (Optional)
            arguments: The KernelArguments instance (Optional)
            description: The description of the agent (Optional)
            id: The ID of the agent (Optional)
            instructions: The instructions for the agent (Optional)
            name: The name of the agent (Optional)
            prompt_template_config: The prompt template configuration (Optional). If this is provided along with
                instructions, the prompt template will be used in place of the instructions.
            **kwargs: Additional keyword arguments
        """
        args: dict[str, Any] = {
            "client": client,
            "definition": definition,
            "name": definition.name,
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

        if definition.instructions is not None:
            args["instructions"] = definition.instructions
        if prompt_template_config is not None:
            args["prompt_template"] = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )
            if prompt_template_config.template is not None:
                # Use the template from the prompt_template_config if it is provided
                args["instructions"] = prompt_template_config.template
        if kwargs:
            args.update(kwargs)

        super().__init__(**args)

    async def add_chat_message(self, thread_id: str, message: "ChatMessageContent") -> None:
        """Add a chat message to the thread.

        Args:
            thread_id: The ID of the thread
            message: The chat message to add
        """
        await AgentThreadActions.create_message(client=self.client, thread_id=thread_id, message=message)

    @trace_agent_invocation
    async def invoke(
        self, thread_id: str, *, arguments: KernelArguments | None = None, kernel: Kernel | None = None, **kwargs
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent on the specified thread."""
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        async for is_visible, message in AgentThreadActions.invoke(
            agent=self, thread_id=thread_id, kernel=kernel, arguments=arguments, **kwargs
        ):
            if is_visible:
                yield message

    @trace_agent_invocation
    async def invoke_stream(
        self,
        thread_id: str,
        *,
        messages: list["ChatMessageContent"] | None = None,
        arguments: KernelArguments | None = None,
        **kwargs,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent on the specified thread with a stream of messages."""
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = self.kernel
        arguments = self.merge_arguments(arguments)

        async for message in AgentThreadActions.invoke_stream(
            agent=self, thread_id=thread_id, messages=messages, kernel=kernel, arguments=arguments, **kwargs
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
