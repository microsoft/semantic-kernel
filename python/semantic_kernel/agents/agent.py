# Copyright (c) Microsoft. All rights reserved.

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Iterable
from typing import Any, ClassVar

from pydantic import Field, model_validator

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.validation import AGENT_NAME_REGEX

logger: logging.Logger = logging.getLogger(__name__)


class Agent(KernelBaseModel, ABC):
    """Base abstraction for all Semantic Kernel agents.

    An agent instance may participate in one or more conversations.
    A conversation may include one or more agents.
    In addition to identity and descriptive meta-data, an Agent
    must define its communication protocol, or AgentChannel.

    Attributes:
        arguments: The arguments for the agent
        channel_type: The type of the agent channel
        description: The description of the agent
        id: The unique identifier of the agent  If no id is provided,
            a new UUID will be generated.
        instructions: The instructions for the agent (optional)
        kernel: The kernel instance for the agent
        name: The name of the agent
        prompt_template: The prompt template for the agent
    """

    arguments: KernelArguments | None = None
    channel_type: ClassVar[type[AgentChannel] | None] = None
    description: str | None = None
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instructions: str | None = None
    kernel: Kernel = Field(default_factory=Kernel)
    name: str = Field(default_factory=lambda: f"agent_{generate_random_ascii_name()}", pattern=AGENT_NAME_REGEX)
    prompt_template: PromptTemplateBase | None = None

    @staticmethod
    def _get_plugin_name(plugin: KernelPlugin | object) -> str:
        """Helper method to get the plugin name."""
        if isinstance(plugin, KernelPlugin):
            return plugin.name
        return plugin.__class__.__name__

    @model_validator(mode="before")
    @classmethod
    def _configure_plugins(cls, data: Any) -> Any:
        """Configure any plugins passed in."""
        if isinstance(data, dict) and (plugins := data.pop("plugins", None)):
            kernel = data.get("kernel", None)
            if not kernel:
                kernel = Kernel()
            for plugin in plugins:
                name = Agent._get_plugin_name(plugin)
                kernel.add_plugin(plugin, plugin_name=name)
            data["kernel"] = kernel
        return data

    @abstractmethod
    async def get_response(self, *args, **kwargs) -> ChatMessageContent:
        """Get a response from the agent.

        This method returns the final result of the agent's execution
        as a single ChatMessageContent object. The caller is blocked until
        the final result is available.

        Note: For streaming responses, use the invoke_stream method, which returns
        intermediate steps and the final result as a stream of StreamingChatMessageContent
        objects. Streaming only the final result is not feasible because the timing of
        the final result's availability is unknown, and blocking the caller until then
        is undesirable in streaming scenarios.
        """
        pass

    @abstractmethod
    def invoke(self, *args, **kwargs) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent.

        This invocation method will return the intermediate steps and the final results
        of the agent's execution as a stream of ChatMessageContent objects to the caller.

        Note: A ChatMessageContent object contains an entire message.
        """
        pass

    @abstractmethod
    def invoke_stream(self, *args, **kwargs) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke the agent as a stream.

        This invocation method will return the intermediate steps and final results of the
        agent's execution as a stream of StreamingChatMessageContent objects to the caller.

        Note: A StreamingChatMessageContent object contains a chunk of a message.
        """
        pass

    def get_channel_keys(self) -> Iterable[str]:
        """Get the channel keys.

        Returns:
            A list of channel keys.
        """
        if not self.channel_type:
            raise NotImplementedError("Unable to get channel keys. Channel type not configured.")
        yield self.channel_type.__name__

    async def create_channel(self) -> AgentChannel:
        """Create a channel.

        Returns:
            An instance of AgentChannel.
        """
        if not self.channel_type:
            raise NotImplementedError("Unable to create channel. Channel type not configured.")
        return self.channel_type()

    async def format_instructions(self, kernel: Kernel, arguments: KernelArguments | None = None) -> str | None:
        """Format the instructions.

        Args:
            kernel: The kernel instance.
            arguments: The kernel arguments.

        Returns:
            The formatted instructions.
        """
        if self.prompt_template is None:
            if self.instructions is None:
                return None
            self.prompt_template = KernelPromptTemplate(
                prompt_template_config=PromptTemplateConfig(template=self.instructions)
            )
        return await self.prompt_template.render(kernel, arguments)

    def _merge_arguments(self, override_args: KernelArguments | None) -> KernelArguments:
        """Merge the arguments with the override arguments.

        Args:
            override_args: The arguments to override.

        Returns:
            The merged arguments. If both are None, return None.
        """
        if not self.arguments:
            if not override_args:
                return KernelArguments()
            return override_args

        if not override_args:
            return self.arguments

        # Both are not None, so merge with precedence for override_args.
        merged_execution_settings = self.arguments.execution_settings or {}
        if override_args.execution_settings:
            merged_execution_settings.update(override_args.execution_settings)

        merged_params = dict(self.arguments)
        merged_params.update(override_args)

        return KernelArguments(settings=merged_execution_settings, **merged_params)

    def __eq__(self, other):
        """Check if two agents are equal."""
        if isinstance(other, Agent):
            return (
                self.id == other.id
                and self.name == other.name
                and self.description == other.description
                and self.instructions == other.instructions
                and self.channel_type == other.channel_type
            )
        return False

    def __hash__(self):
        """Get the hash of the agent."""
        return hash((self.id, self.name, self.description, self.instructions, self.channel_type))
