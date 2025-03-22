# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
import uuid
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar, cast

from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import Field, model_validator

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@release_candidate
class ChatCompletionAgentThread(AgentThread):
    """Azure AI Agent Thread class."""

    def __init__(self, chat_history: ChatHistory | None = None, thread_id: str | None = None) -> None:
        """Initialize the ChatCompletionAgent Thread.

        Args:
            chat_history: The chat history for the thread. If None, a new ChatHistory instance will be created.
            thread_id: The ID of the thread. If None, a new thread will be created.
        """
        super().__init__()

        self._chat_history = chat_history or ChatHistory()
        self._thread_id = thread_id or f"thread_{uuid.uuid4().hex}"
        self._is_deleted = False

    def __len__(self) -> int:
        """Returns the length of the chat history."""
        return len(self._chat_history)

    @override
    async def _create(self) -> str:
        """Starts the thread and returns its ID."""
        return self._thread_id

    @override
    async def _delete(self) -> None:
        """Ends the current thread."""
        self._chat_history.clear()

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        if isinstance(new_message, str):
            new_message = ChatMessageContent(role=AuthorRole.USER, content=new_message)

        if (
            not new_message.metadata
            or "thread_id" not in new_message.metadata
            or new_message.metadata["thread_id"] != self._id
        ):
            self._chat_history.add_message(new_message)

    async def retrieve_current_chat_history(self) -> ChatHistory:
        """Retrieve the current chat history."""
        if self._id is None:
            raise RuntimeError("Cannot retrieve chat history, since the thread is not currently active.")
        return self._chat_history

    async def reduce(self) -> ChatHistory | None:
        """Reduce the chat history to a smaller size."""
        if self._id is None:
            raise RuntimeError("Cannot reduce chat history, since the thread is not currently active.")
        if not isinstance(self._chat_history, ChatHistoryReducer):
            return None
        return await self._chat_history.reduce()


@release_candidate
class ChatCompletionAgent(Agent):
    """A Chat Completion Agent based on ChatCompletionClientBase."""

    function_choice_behavior: FunctionChoiceBehavior | None = Field(
        default_factory=lambda: FunctionChoiceBehavior.Auto()
    )
    channel_type: ClassVar[type[AgentChannel] | None] = ChatHistoryChannel
    service: ChatCompletionClientBase | None = Field(default=None, exclude=True)

    def __init__(
        self,
        *,
        arguments: KernelArguments | None = None,
        description: str | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        id: str | None = None,
        instructions: str | None = None,
        kernel: "Kernel | None" = None,
        name: str | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        service: ChatCompletionClientBase | None = None,
    ) -> None:
        """Initialize a new instance of ChatCompletionAgent.

        Args:
            arguments: The kernel arguments for the agent. Invoke method arguments take precedence over
                the arguments provided here.
            description: The description of the agent.
            function_choice_behavior: The function choice behavior to determine how and which plugins are
                advertised to the model.
            kernel: The kernel instance. If both a kernel and a service are provided, the service will take precedence
                if they share the same service_id or ai_model_id. Otherwise if separate, the first AI service
                registered on the kernel will be used.
            id: The unique identifier for the agent. If not provided,
                a unique GUID will be generated.
            instructions: The instructions for the agent.
            name: The name of the agent.
            plugins: The plugins for the agent. If plugins are included along with a kernel, any plugins
                that already exist in the kernel will be overwritten.
            prompt_template_config: The prompt template configuration for the agent.
            service: The chat completion service instance. If a kernel is provided with the same service_id or
                `ai_model_id`, the service will take precedence.
        """
        args: dict[str, Any] = {
            "description": description,
        }
        if name is not None:
            args["name"] = name
        if id is not None:
            args["id"] = id
        if kernel is not None:
            args["kernel"] = kernel
        if arguments is not None:
            args["arguments"] = arguments

        if instructions and prompt_template_config and instructions != prompt_template_config.template:
            logger.info(
                f"Both `instructions` ({instructions}) and `prompt_template_config` "
                f"({prompt_template_config.template}) were provided. Using template in `prompt_template_config` "
                "and ignoring `instructions`."
            )

        if plugins is not None:
            args["plugins"] = plugins

        if function_choice_behavior is not None:
            args["function_choice_behavior"] = function_choice_behavior

        if service is not None:
            args["service"] = service

        if instructions is not None:
            args["instructions"] = instructions
        if prompt_template_config is not None:
            args["prompt_template"] = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )
            if prompt_template_config.template is not None:
                # Use the template from the prompt_template_config if it is provided
                args["instructions"] = prompt_template_config.template
        super().__init__(**args)

    @model_validator(mode="after")
    def configure_service(self) -> "ChatCompletionAgent":
        """Configure the service used by the ChatCompletionAgent."""
        if self.service is None:
            return self
        if not isinstance(self.service, ChatCompletionClientBase):
            raise AgentInitializationException(
                f"Service provided for ChatCompletionAgent is not an instance of ChatCompletionClientBase. "
                f"Service: {type(self.service)}"
            )
        self.kernel.add_service(self.service, overwrite=True)
        return self

    async def create_channel(
        self, chat_history: ChatHistory | None = None, thread_id: str | None = None
    ) -> AgentChannel:
        """Create a ChatHistoryChannel.

        Args:
            chat_history: The chat history for the channel. If None, a new ChatHistory instance will be created.
            thread_id: The ID of the thread. If None, a new thread will be created.

        Returns:
            An instance of AgentChannel.
        """
        from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgentThread

        ChatHistoryChannel.model_rebuild()

        thread = ChatCompletionAgentThread(chat_history=chat_history, thread_id=thread_id)

        if thread.id is None:
            await thread.create()

        chat_history = await thread.retrieve_current_chat_history()

        return ChatHistoryChannel(messages=chat_history.messages, thread=thread)

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        message: str | ChatMessageContent,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent.

        Args:
            message: The chat message content either as a string or ChatMessageContent.
            thread: The thread to use for agent invocation.
            arguments: The kernel arguments.
            kernel: The kernel instance.
            kwargs: The keyword arguments.

        Returns:
            An AgentResponseItem of type ChatMessageContent.
        """
        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        thread = await self._configure_thread(message, thread)
        thread = cast(ChatCompletionAgentThread, thread)

        chat_history = await thread.retrieve_current_chat_history()

        responses: list[ChatMessageContent] = []
        async for response in self._inner_invoke(thread, chat_history, arguments, kernel, **kwargs):
            responses.append(response)

        if not responses:
            raise AgentInvokeException("No response from agent.")

        response = responses[-1]
        await thread.on_new_message(response)
        return AgentResponseItem(message=response, thread=thread)

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        message: str | ChatMessageContent,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke the chat history handler.

        Args:
            message: The chat message content either as a string or ChatMessageContent.
            thread: The thread to use for agent invocation.
            arguments: The kernel arguments.
            kernel: The kernel instance.
            kwargs: The keyword arguments.

        Returns:
            An async iterable of AgentResponseItem of type ChatMessageContent.
        """
        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        thread = await self._configure_thread(message, thread)
        thread = cast(ChatCompletionAgentThread, thread)

        chat_history = await thread.retrieve_current_chat_history()

        async for response in self._inner_invoke(thread, chat_history, arguments, kernel, **kwargs):
            await thread.on_new_message(response)
            yield AgentResponseItem(message=response, thread=thread)

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        *,
        message: str | ChatMessageContent,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Invoke the chat history handler in streaming mode.

        Args:
            message: The chat message content either as a string or ChatMessageContent.
            thread: The thread to use for agent invocation.
            arguments: The kernel arguments.
            kernel: The kernel instance.
            kwargs: The keyword arguments.

        Returns:
            An async generator of AgentResponseItem of type StreamingChatMessageContent.
        """
        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        thread = await self._configure_thread(message, thread)
        thread = cast(ChatCompletionAgentThread, thread)

        chat_history = await thread.retrieve_current_chat_history()

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        chat_completion_service, settings = await self._get_chat_completion_service_and_settings(
            kernel=kernel, arguments=arguments
        )

        # If the user hasn't provided a function choice behavior, use the agent's default.
        if settings.function_choice_behavior is None:
            settings.function_choice_behavior = self.function_choice_behavior

        agent_chat_history = await self._prepare_agent_chat_history(
            history=chat_history,
            kernel=kernel,
            arguments=arguments,
        )

        message_count_before_completion = len(agent_chat_history)

        logger.debug(f"[{type(self).__name__}] Invoking {type(chat_completion_service).__name__}.")

        responses: AsyncGenerator[list[StreamingChatMessageContent], Any] = (
            chat_completion_service.get_streaming_chat_message_contents(
                chat_history=agent_chat_history,
                settings=settings,
                kernel=kernel,
                arguments=arguments,
            )
        )

        logger.debug(
            f"[{type(self).__name__}] Invoked {type(chat_completion_service).__name__} "
            f"with message count: {message_count_before_completion}."
        )

        role = None
        response_builder: list[str] = []
        async for response_list in responses:
            for response in response_list:
                role = response.role
                response.name = self.name
                response_builder.append(response.content)
                yield AgentResponseItem(message=response, thread=thread)

        await self._capture_mutated_messages(agent_chat_history, message_count_before_completion, thread)
        if role != AuthorRole.TOOL:
            await thread.on_new_message(
                ChatMessageContent(
                    role=role if role else AuthorRole.ASSISTANT, content="".join(response_builder), name=self.name
                )
            )

    async def _inner_invoke(
        self,
        thread: ChatCompletionAgentThread,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Helper method to invoke the agent with a chat history in non-streaming mode."""
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        chat_completion_service, settings = await self._get_chat_completion_service_and_settings(
            kernel=kernel, arguments=arguments
        )

        # If the user hasn't provided a function choice behavior, use the agent's default.
        if settings.function_choice_behavior is None:
            settings.function_choice_behavior = self.function_choice_behavior

        agent_chat_history = await self._prepare_agent_chat_history(
            history=history,
            kernel=kernel,
            arguments=arguments,
        )

        message_count_before_completion = len(agent_chat_history)

        logger.debug(f"[{type(self).__name__}] Invoking {type(chat_completion_service).__name__}.")

        responses = await chat_completion_service.get_chat_message_contents(
            chat_history=agent_chat_history,
            settings=settings,
            kernel=kernel,
            arguments=arguments,
        )

        logger.debug(
            f"[{type(self).__name__}] Invoked {type(chat_completion_service).__name__} "
            f"with message count: {message_count_before_completion}."
        )

        await self._capture_mutated_messages(agent_chat_history, message_count_before_completion, thread)

        for response in responses:
            response.name = self.name
            yield response

    async def _prepare_agent_chat_history(
        self, history: ChatHistory, kernel: "Kernel", arguments: KernelArguments
    ) -> ChatHistory:
        """Prepare the agent chat history from the input history by adding the formatted instructions."""
        formatted_instructions = await self.format_instructions(kernel, arguments)
        messages = []
        if formatted_instructions:
            messages.append(ChatMessageContent(role=AuthorRole.SYSTEM, content=formatted_instructions, name=self.name))
        if history.messages:
            messages.extend(history.messages)

        return ChatHistory(messages=messages)

    async def _get_chat_completion_service_and_settings(
        self, kernel: "Kernel", arguments: KernelArguments
    ) -> tuple[ChatCompletionClientBase, PromptExecutionSettings]:
        """Get the chat completion service and settings."""
        chat_completion_service, settings = kernel.select_ai_service(arguments=arguments, type=ChatCompletionClientBase)

        if not chat_completion_service:
            raise KernelServiceNotFoundError(
                "Chat completion service not found. Check your service or kernel configuration."
            )

        assert isinstance(chat_completion_service, ChatCompletionClientBase)  # nosec
        assert settings is not None  # nosec

        return chat_completion_service, settings

    async def _capture_mutated_messages(
        self, agent_chat_history: ChatHistory, start: int, thread: ChatCompletionAgentThread
    ) -> None:
        """Capture mutated messages related function calling/tools."""
        for message_index in range(start, len(agent_chat_history)):
            message = agent_chat_history[message_index]  # type: ignore
            message.name = self.name
            await thread.on_new_message(message)

    async def _configure_thread(
        self,
        message: ChatMessageContent,
        thread: AgentThread | None = None,
    ) -> AgentThread:
        """Ensures the thread is properly initialized and active, then posts the new message.

        Args:
            message: The chat message content to post to the thread.
            thread: An optional existing thread to configure. If None, a new AzureAIAgentThread is created.

        Returns:
            The active thread (AzureAIAgentThread) after posting the message.

        Raises:
            AgentInitializationException: If `thread` is not an AzureAIAgentThread.
        """
        thread = thread or ChatCompletionAgentThread()

        if not isinstance(thread, ChatCompletionAgentThread):
            raise AgentInitializationException(
                f"The thread must be an ChatCompletionAgentThread, but got {type(thread).__name__}."
            )

        if thread.id is None:
            await thread.create()

        await thread.on_new_message(message)

        return thread
