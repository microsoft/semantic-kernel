# Copyright (c) Microsoft. All rights reserved.

import importlib
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Awaitable, Callable, Iterable, Sequence
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Generic, Protocol, TypeVar, runtime_checkable

import yaml
from pydantic import Field, model_validator

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException, AgentInitializationException
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

    from semantic_kernel.kernel_pydantic import KernelBaseSettings

logger: logging.Logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="Agent")
TMessage = TypeVar("TMessage", bound=ChatMessageContent)
TThreadType = TypeVar("TThreadType", bound="AgentThread")


# region Declarative Spec Definitions


class InputSpec(KernelBaseModel):
    """Class representing an input specification."""

    description: str | None = None
    required: bool = False
    default: Any = None


class OutputSpec(KernelBaseModel):
    """Class representing an output specification."""

    description: str | None = None
    type: str | None = None


class ModelConnection(KernelBaseModel):
    """Class representing a model connection."""

    type: str | None = None
    service_id: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)


class ModelSpec(KernelBaseModel):
    """Class representing a model specification."""

    id: str | None = None
    api: str = "chat"
    options: dict[str, Any] = Field(default_factory=dict)
    connection: ModelConnection | None = None


class ToolSpec(KernelBaseModel):
    """Class representing a tool specification."""

    id: str | None = None
    type: str | None = None
    description: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)


class AgentSpec(KernelBaseModel):
    """Class representing an agent specification."""

    type: str
    id: str | None = None
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    model: ModelSpec | None = None
    tools: list[ToolSpec] = Field(default_factory=list)
    template: dict[str, Any] | None = None
    extras: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, InputSpec] = Field(default_factory=dict)
    outputs: dict[str, OutputSpec] = Field(default_factory=dict)


# endregion


# region AgentThread


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


# endregion

# region AgentResponseItem


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


# endregion


# region Agent Base Class


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

    # region Invocation Methods

    @abstractmethod
    def get_response(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
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
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
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
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        *,
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

    # endregion

    # region Channel Management

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

    # endregion

    # region Instructions Management

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

    # endregion

    # region Thread Management

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

    # endregion

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


# region Declarative Spec Handling


@runtime_checkable
class DeclarativeSpecProtocol(Protocol):
    """Protocol for declarative spec mixin."""

    @classmethod
    def resolve_placeholders(
        cls: type,
        yaml_str: str,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """Resolve placeholders in the YAML string."""
        ...

    @classmethod
    async def from_yaml(
        cls: type,
        yaml_str: str,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
        **kwargs,
    ) -> "Agent":
        """Create an agent instance from a YAML string."""
        ...

    @classmethod
    async def from_dict(
        cls: type,
        data: dict,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        settings: "KernelBaseSettings | None" = None,
        **kwargs,
    ) -> "Agent":
        """Create an agent from a dictionary."""
        ...


# region Agent Type Registry


_TAgent = TypeVar("_TAgent", bound=Agent)

# Global agent type registry
AGENT_TYPE_REGISTRY: dict[str, type[Agent]] = {}


def register_agent_type(agent_type: str):
    """Decorator to register an agent type with the registry.

    Example usage:
        @register_agent_type("my_custom_agent")
        class MyCustomAgent(Agent):
            ...
    """

    def decorator(cls: type[_TAgent]) -> type[_TAgent]:
        AGENT_TYPE_REGISTRY[agent_type.lower()] = cls
        return cls

    return decorator


_BUILTIN_AGENTS_LOADED = False
_BUILTIN_AGENTS_LOCK = threading.Lock()

# List of import paths for all built-in agent modules
# These modules must contain `@register_agent_type(...)` decorators.
_BUILTIN_AGENT_MODULES = [
    "semantic_kernel.agents.chat_completion.chat_completion_agent",
    "semantic_kernel.agents.azure_ai.azure_ai_agent",
    "semantic_kernel.agents.open_ai.openai_assistant_agent",
    "semantic_kernel.agents.open_ai.azure_assistant_agent",
    "semantic_kernel.agents.open_ai.openai_responses_agent",
    "semantic_kernel.agents.open_ai.azure_responses_agent",
]


def _preload_builtin_agents() -> None:
    """Make sure all built-in agent modules are imported at least once, so their decorators register agent types."""
    global _BUILTIN_AGENTS_LOADED

    if _BUILTIN_AGENTS_LOADED:
        return

    with _BUILTIN_AGENTS_LOCK:
        if _BUILTIN_AGENTS_LOADED:
            return  # Double-checked locking

        failed = []

        for module_name in _BUILTIN_AGENT_MODULES:
            try:
                importlib.import_module(module_name)
            except Exception as ex:
                failed.append((module_name, ex))

        if failed:
            error_msgs = "\n".join(f"- {mod}: {err}" for mod, err in failed)
            raise RuntimeError(f"Failed to preload the following built-in agent modules:\n{error_msgs}")

        _BUILTIN_AGENTS_LOADED = True


class AgentRegistry:
    """Responsible for creating agents from YAML, dicts, or files."""

    @staticmethod
    def register_type(agent_type: str, agent_cls: type[Agent]) -> None:
        """Register a new agent type at runtime.

        Args:
            agent_type: The string identifier representing the agent type (e.g., 'chat_completion_agent').
            agent_cls: The class implementing the agent, inheriting from `Agent`.

        Example:
            AgentRegistry.register_type("my_custom_agent", MyCustomAgent)
        """
        AGENT_TYPE_REGISTRY[agent_type.lower()] = agent_cls

    @staticmethod
    async def create_from_yaml(
        yaml_str: str,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
        **kwargs,
    ) -> _TAgent:
        """Create a single agent instance from a YAML string.

        Args:
            yaml_str: The YAML string defining the agent.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            plugins: The plugins to use for the agent.
            settings: The settings to use for the agent.
            extras: Additional parameters to resolve placeholders in the YAML.
            **kwargs: Additional parameters passed to the agent constructor if required.

        Returns:
            An instance of the requested agent.

        Raises:
            AgentInitializationException: If the YAML is invalid or the agent type is not supported.

        Example:
            agent = await AgentRegistry.create_agent_from_yaml(
                yaml_str, kernel=kernel, service=AzureChatCompletion(),
            )
        """
        _preload_builtin_agents()

        data = yaml.safe_load(yaml_str)

        agent_type = data.get("type", "").lower()
        if not agent_type:
            raise AgentInitializationException("Missing 'type' field in agent definition.")

        if agent_type not in AGENT_TYPE_REGISTRY:
            raise AgentInitializationException(f"Agent type '{agent_type}' not registered.")

        agent_cls = AGENT_TYPE_REGISTRY[agent_type]

        if not isinstance(agent_cls, DeclarativeSpecProtocol):
            raise AgentInitializationException(
                f"Agent class '{agent_cls.__name__}' does not support declarative spec loading."
            )

        yaml_str = agent_cls.resolve_placeholders(yaml_str, settings, extras)
        data = yaml.safe_load(yaml_str)

        return await agent_cls.from_dict(
            data,
            kernel=kernel,
            plugins=plugins,
            settings=settings,
            **kwargs,
        )

    @staticmethod
    async def create_from_dict(
        data: dict,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
        **kwargs,
    ) -> _TAgent:
        """Create a single agent instance from a dictionary.

        Args:
            data: The dictionary defining the agent fields.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            plugins: The plugins to use for the agent.
            settings: The settings to use for the agent.
            extras: Additional parameters to resolve placeholders in the YAML.
            **kwargs: Additional parameters passed to the agent constructor if required.

        Returns:
            An instance of the requested agent.

        Raises:
            AgentInitializationException: If the dictionary is missing a 'type' field or the agent type is unsupported.

        Example:
            agent = await AgentRegistry.create_agent_from_dict(agent_data, kernel=kernel)
        """
        _preload_builtin_agents()

        agent_type = data.get("type", "").lower()

        if not agent_type:
            raise AgentInitializationException("Missing 'type' field in agent definition.")

        if agent_type not in AGENT_TYPE_REGISTRY:
            raise AgentInitializationException(f"Agent type '{agent_type}' is not supported.")

        agent_cls = AGENT_TYPE_REGISTRY[agent_type]

        if not isinstance(agent_cls, DeclarativeSpecProtocol):
            raise AgentInitializationException(
                f"Agent class '{agent_cls.__name__}' does not support declarative spec loading."
            )

        return await agent_cls.from_dict(
            data,
            kernel=kernel,
            plugins=plugins,
            settings=settings,
            extras=extras,
            **kwargs,
        )

    @staticmethod
    async def create_from_file(
        file_path: str,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
        encoding: str | None = None,
        **kwargs,
    ) -> _TAgent:
        """Create a single agent instance from a YAML file.

        Args:
            file_path: Path to the YAML file defining the agent.
            kernel: The Kernel instance to use for tool resolution and agent initialization.
            plugins: The plugins to use for the agent.
            settings: The settings to use for the agent.
            extras: Additional parameters to resolve placeholders in the YAML.
            encoding: The encoding of the file (default is 'utf-8').
            **kwargs: Additional parameters passed to the agent constructor if required.

        Returns:
            An instance of the requested agent.

        Raises:
            AgentInitializationException: If the file is unreadable or the agent type is unsupported.
        """
        _preload_builtin_agents()

        try:
            if encoding is None:
                encoding = "utf-8"
            with open(file_path, encoding=encoding) as f:
                yaml_str = f.read()
        except Exception as e:
            raise AgentInitializationException(f"Failed to read agent spec file: {e}") from e

        return await AgentRegistry.create_from_yaml(
            yaml_str,
            kernel=kernel,
            plugins=plugins,
            settings=settings,
            extras=extras,
            **kwargs,
        )


# endregion


# region DeclarativeSpecMixin

_D = TypeVar("_D", bound="DeclarativeSpecMixin")


class DeclarativeSpecMixin(ABC):
    """Mixin class for declarative agent methods."""

    @classmethod
    async def from_yaml(
        cls: type[_D],
        yaml_str: str,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
        **kwargs,
    ) -> _D:
        """Create an agent instance from a YAML string."""
        if settings:
            yaml_str = cls.resolve_placeholders(yaml_str, settings, extras=extras)

        data = yaml.safe_load(yaml_str)
        return await cls.from_dict(
            data,
            kernel=kernel,
            plugins=plugins,
            prompt_template_config=prompt_template_config,
            settings=settings,
            **kwargs,
        )

    @classmethod
    async def from_dict(
        cls: type[_D],
        data: dict,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        settings: "KernelBaseSettings | None" = None,
        **kwargs,
    ) -> _D:
        """Default implementation: call the protected _from_dict."""
        extracted, kernel = cls._normalize_spec_fields(data, kernel=kernel, plugins=plugins, **kwargs)
        return await cls._from_dict(
            {**data, **extracted},
            kernel=kernel,
            prompt_template_config=extracted.get("prompt_template"),
            settings=settings,
            **kwargs,
        )

    @classmethod
    @abstractmethod
    async def _from_dict(
        cls: type[_D],
        data: dict,
        *,
        kernel: Kernel,
        prompt_template_config: PromptTemplateConfig | None = None,
        **kwargs,
    ) -> _D:
        """Create an agent instance from a dictionary."""
        pass

    @classmethod
    def resolve_placeholders(
        cls: type[_D],
        yaml_str: str,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """Resolve placeholders inside the YAML string using agent-specific settings.

        Override in subclasses if necessary.
        """
        return yaml_str

    @classmethod
    def _normalize_spec_fields(
        cls: type[_D],
        data: dict,
        *,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        **kwargs,
    ) -> tuple[dict[str, Any], Kernel]:
        """Normalize the fields in the spec dictionary.

        Returns:
            A tuple of:
                - Normalized constructor field dict
                - The effective Kernel instance (created or reused)
        """
        if not kernel:
            kernel = Kernel()

        # Plugins provided explicitly
        if plugins:
            for plugin in plugins:
                kernel.add_plugin(plugin)

        # Validate tools declared in the spec exist in the kernel
        if "tools" in data:
            cls._validate_tools(data["tools"], kernel)

        model_options = data.get("model", {}).get("options", {}) if data.get("model") else {}

        inputs = data.get("inputs", {})
        input_defaults = {
            k: v.get("default")
            for k, v in (inputs.items() if isinstance(inputs, dict) else [])
            if v.get("default") is not None
        }

        # Start with model options
        arguments = KernelArguments(**model_options)
        # Update with input defaults (only if not already provided by model options)
        for k, v in input_defaults.items():
            if k not in arguments:
                arguments[k] = v

        fields = {
            "name": data.get("name"),
            "description": data.get("description"),
            "instructions": data.get("instructions"),
            "arguments": arguments,
        }

        # Handle prompt_template if available
        if "template" in data or "prompt_template" in data:
            template_data = data.get("prompt_template") or data.get("template")
            if isinstance(template_data, dict):
                prompt_template_config = PromptTemplateConfig(**template_data)
                # If 'instructions' is set in YAML, override the template field in config
                instructions = data.get("instructions")
                if instructions is not None:
                    prompt_template_config.template = instructions
                fields["prompt_template"] = prompt_template_config
                # Always set fields["instructions"] to the template being used
                fields["instructions"] = prompt_template_config.template

        return fields, kernel

    @classmethod
    def _validate_tools(cls: type[_D], tools_list: list[dict], kernel: Kernel) -> None:
        """Validate tool references in the declarative spec against kernel's registered plugins.

        This validates the declared tools in the YAML spec, and only checks whether those references resolve
        properly in the current kernel.
        """
        if not kernel:
            raise AgentInitializationException("Kernel instance is required for tool resolution.")

        for tool in tools_list:
            tool_id = tool.get("id")
            if not tool_id or tool.get("type") != "function":
                continue

            if "." not in tool_id:
                raise AgentInitializationException(f"Tool id '{tool_id}' must be in format PluginName.FunctionName")

            plugin_name, function_name = tool_id.split(".", 1)

            plugin = kernel.plugins.get(plugin_name)
            if not plugin:
                raise AgentInitializationException(f"Plugin '{plugin_name}' not found in kernel.")

            if function_name not in plugin.functions:
                raise AgentInitializationException(f"Function '{function_name}' not found in plugin '{plugin_name}'.")


# endregion
