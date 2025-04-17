# Copyright (c) Microsoft. All rights reserved.

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Awaitable, Callable, Iterable, Sequence
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Generic, TypeVar

from pydantic import Field, model_validator

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.validation import AGENT_NAME_REGEX

if TYPE_CHECKING:
    from mcp.server.lowlevel.server import LifespanResultT, Server

logger: logging.Logger = logging.getLogger(__name__)

TMessage = TypeVar("TMessage", bound=ChatMessageContent)
TThreadType = TypeVar("TThreadType", bound="AgentThread")


class AgentThread(ABC):
    """Base class for agent threads."""

    def __init__(self):
        """Initialize the agent thread."""
        self._is_deleted: bool = False  # type: ignore
        self._id: str | None = None  # type: ignore

    @property
    def id(self) -> str | None:
        """Returns the ID of the current thread (if any)."""
        if self._is_deleted:
            raise RuntimeError("Thread has been deleted; call `create()` to recreate it.")
        return self._id

    async def create(self) -> str | None:
        """Starts the thread and returns the thread ID."""
        # A thread should not be recreated after it has been deleted.
        if self._is_deleted:
            raise RuntimeError("Cannot create thread because it has already been deleted.")

        # If the thread ID is already set, we're done, just return the Id.
        if self.id is not None:
            return self.id

        # Otherwise, create the thread.
        self._id = await self._create()
        return self.id

    async def delete(self) -> None:
        """Ends the current thread."""
        # A thread should not be deleted if it has already been deleted.
        if self._is_deleted:
            return

        # If the thread ID is not set, we're done, just return.
        if self.id is None:
            self._is_deleted = True
            return

        # Otherwise, delete the thread.
        await self._delete()
        self._id = None
        self._is_deleted = True

    async def on_new_message(
        self,
        new_message: ChatMessageContent,
    ) -> None:
        """Invoked when a new message has been contributed to the chat by any participant."""
        # If the thread is not created yet, create it.
        if self.id is None:
            await self.create()

        await self._on_new_message(new_message)

    @abstractmethod
    async def _create(self) -> str:
        """Starts the thread and returns the thread ID."""
        raise NotImplementedError

    @abstractmethod
    async def _delete(self) -> None:
        """Ends the current thread."""
        raise NotImplementedError

    @abstractmethod
    async def _on_new_message(
        self,
        new_message: ChatMessageContent,
    ) -> None:
        """Invoked when a new message has been contributed to the chat by any participant."""
        raise NotImplementedError


class AgentResponseItem(KernelBaseModel, Generic[TMessage]):
    """Class representing a response item from an agent.

    Attributes:
        message: The message content of the response item.
        thread: The conversation thread associated with the response item.
    """

    message: TMessage
    thread: AgentThread

    @property
    def content(self) -> TMessage:
        """Get the content of the response item."""
        return self.message

    @property
    def items(self) -> list[CMC_ITEM_TYPES]:
        """Get the items of the response item."""
        return self.message.items

    @property
    def metadata(self) -> dict[str, Any]:
        """Get the metadata of the response item."""
        return self.message.metadata

    @property
    def name(self) -> str | None:
        """Get the name of the response item."""
        return self.message.name

    @property
    def role(self) -> str | None:
        """Get the role of the response item."""
        return self.message.role

    def __str__(self):
        """Get the string representation of the response item."""
        return str(self.content)

    def __getattr__(self, item):
        """Get an attribute of the response item."""
        return getattr(self.message, item)

    def __hash__(self):
        """Get the hash of the response item."""
        return hash((self.message, self.thread))


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
                kernel.add_plugin(plugin)
            data["kernel"] = kernel
        return data

    def model_post_init(self, __context: Any) -> None:
        """Post initialization: create a kernel_function that calls this agent's get_response()."""

        @kernel_function(name=self.name, description=self.description or self.instructions)
        async def _as_kernel_function(
            messages: Annotated[str | list[str], "The user messages for the agent."],
            instructions_override: Annotated[str | None, "Override agent instructions."] = None,
        ) -> Annotated[Any, "Agent response."]:
            """A Minimal universal function for all agents.

            Exposes 'messages' and 'instructions_override'.
            Internally, we pass them to get_response() for whichever agent is calling it.
            """
            if isinstance(messages, str):
                messages = [messages]

            response_item = await self.get_response(
                messages=messages,  # type: ignore
                instructions_override=instructions_override if instructions_override else None,
            )
            return response_item.content

        # Keep Pydantic happy with the "private" method, otherwise
        # it will fail validating the model.
        setattr(self, "_as_kernel_function", _as_kernel_function)

    @abstractmethod
    def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        **kwargs,
    ) -> Awaitable[AgentResponseItem[ChatMessageContent]]:
        """Get a response from the agent.

        This method returns the final result of the agent's execution
        as a single ChatMessageContent object. The caller is blocked until
        the final result is available.

        Note: For streaming responses, use the invoke_stream method, which returns
        intermediate steps and the final result as a stream of StreamingChatMessageContent
        objects. Streaming only the final result is not feasible because the timing of
        the final result's availability is unknown, and blocking the caller until then
        is undesirable in streaming scenarios.

        Args:
            messages: The message(s) to send to the agent.
            thread: The conversation thread associated with the message(s).
            kwargs: Additional keyword arguments.

        Returns:
            An agent response item.
        """
        pass

    @abstractmethod
    def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke the agent.

        This invocation method will return the final results of the agent's execution as a
        stream of ChatMessageContent objects to the caller. The reason for returning a stream
        is to allow for future extensions to the agent's capabilities, such as multi-modality.

        To get the intermediate steps of the agent's execution, use the on_intermediate_message callback
        to handle those messages.

        Note: A ChatMessageContent object contains an entire message.

        Args:
            messages: The message(s) to send to the agent.
            thread: The conversation thread associated with the message(s).
            on_intermediate_message: A callback function to handle intermediate steps of the agent's execution.
            kwargs: Additional keyword arguments.

        Yields:
            An agent response item.
        """
        pass

    @abstractmethod
    def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Invoke the agent as a stream.

        This invocation method will return the intermediate steps and final results of the
        agent's execution as a stream of StreamingChatMessageContent objects to the caller.

        To get the intermediate steps of the agent's execution as fully formed messages,
        use the on_intermediate_message callback.

        Note: A StreamingChatMessageContent object contains a chunk of a message.

        Args:
            messages: The message(s) to send to the agent.
            thread: The conversation thread associated with the message(s).
            on_intermediate_message: A callback function to handle intermediate steps of the
                                     agent's execution as fully formed messages.
            kwargs: Additional keyword arguments.

        Yields:
            An agent response item.
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

    async def _ensure_thread_exists_with_messages(
        self,
        *,
        messages: str | ChatMessageContent | Sequence[str | ChatMessageContent] | None = None,
        thread: AgentThread | None,
        construct_thread: Callable[[], TThreadType],
        expected_type: type[TThreadType],
    ) -> TThreadType:
        """Ensure the thread exists with the provided message(s)."""
        if messages is None:
            messages = []

        if isinstance(messages, (str, ChatMessageContent)):
            messages = [messages]

        normalized_messages = [
            ChatMessageContent(role=AuthorRole.USER, content=msg) if isinstance(msg, str) else msg for msg in messages
        ]

        if thread is None:
            thread = construct_thread()
            await thread.create()

        if not isinstance(thread, expected_type):
            raise AgentExecutionException(
                f"{self.__class__.__name__} currently only supports agent threads of type {expected_type.__name__}."
            )

        # Notify the thread that new messages are available.
        for msg in normalized_messages:
            await self._notify_thread_of_new_message(thread, msg)

        return thread

    async def _notify_thread_of_new_message(
        self,
        thread: AgentThread,
        new_message: ChatMessageContent,
    ) -> None:
        """Notify the thread of a new message."""
        await thread.on_new_message(new_message)

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

    def as_mcp_server(
        self,
        *,
        prompts: list[PromptTemplateBase] | None = None,
        server_name: str | None = None,
        version: str | None = None,
        instructions: str | None = None,
        lifespan: Callable[["Server[LifespanResultT]"], AbstractAsyncContextManager["LifespanResultT"]] | None = None,
    ) -> "Server[LifespanResultT]":
        """Convert the agent to an MCP server.

        This will create a MCP Server, with a single Tool, which is the agent itself.
        Prompts can be added through the prompts keyword.

        By default, the server name will be the same as the agent name.
        If a server name is provided, it will be used instead.

        Returns:
            The MCP server instance.
        """
        from semantic_kernel.connectors.mcp import create_mcp_server_from_functions

        return create_mcp_server_from_functions(
            functions=self,
            prompts=prompts,
            server_name=server_name or self.name,
            version=version,
            instructions=instructions,
            lifespan=lifespan,
        )
