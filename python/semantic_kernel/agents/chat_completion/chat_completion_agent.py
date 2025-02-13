# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TYPE_CHECKING, Any, ClassVar

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import trace_agent_invocation

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class ChatCompletionAgent(Agent):
    """A KernelAgent specialization based on ChatCompletionClientBase.

    Note: enable `function_choice_behavior` on the PromptExecutionSettings to enable function
    choice behavior which allows the kernel to utilize plugins and functions registered in
    the kernel.
    """

    service_id: str
    channel_type: ClassVar[type[AgentChannel]] = ChatHistoryChannel

    def __init__(
        self,
        service_id: str | None = None,
        kernel: "Kernel | None" = None,
        name: str | None = None,
        id: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        arguments: KernelArguments | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
    ) -> None:
        """Initialize a new instance of ChatCompletionAgent.

        Args:
            service_id: The service id for the chat completion service. (optional) If not provided,
                the default service name `default` will be used.
            kernel: The kernel instance. (optional)
            name: The name of the agent. (optional)
            id: The unique identifier for the agent. (optional) If not provided,
                a unique GUID will be generated.
            description: The description of the agent. (optional)
            instructions: The instructions for the agent. (optional)
            arguments: The kernel arguments for the agent. (optional) Invoke method arguments take precedence over
                the arguments provided here.
            prompt_template_config: The prompt template configuration for the agent. (optional)
        """
        if not service_id:
            service_id = DEFAULT_SERVICE_NAME

        args: dict[str, Any] = {
            "service_id": service_id,
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

    @trace_agent_invocation
    async def invoke(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat history handler.

        Args:
            history: The chat history.
            arguments: The kernel arguments. (optional)
            kernel: The kernel instance. (optional)
            kwargs: The keyword arguments. (optional)

        Returns:
            An async iterable of ChatMessageContent.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        # Add the chat history to the args in the event that it is needed for prompt template configuration
        arguments["chat_history"] = history

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        chat_completion_service, settings = await self._get_chat_completion_service_and_settings(
            kernel=kernel, arguments=arguments
        )

        assert isinstance(chat_completion_service, ChatCompletionClientBase)  # nosec

        chat = await self._setup_agent_chat_history(
            history=history,
            kernel=kernel,
            arguments=arguments,
        )

        message_count = len(chat)

        logger.debug(f"[{type(self).__name__}] Invoking {type(chat_completion_service).__name__}.")

        messages = await chat_completion_service.get_chat_message_contents(
            chat_history=chat,
            settings=settings,
            kernel=kernel,
            arguments=arguments,
        )

        logger.info(
            f"[{type(self).__name__}] Invoked {type(chat_completion_service).__name__} "
            f"with message count: {message_count}."
        )

        # Capture mutated messages related function calling / tools
        for message_index in range(message_count, len(chat)):
            message = chat[message_index]
            message.name = self.name
            history.add_message(message)

        for message in messages:
            message.name = self.name
            yield message

    @trace_agent_invocation
    async def invoke_stream(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke the chat history handler in streaming mode.

        Args:
            history: The chat history.
            arguments: The kernel arguments. (optional)
            kernel: The kernel instance. (optional)
            kwargs: The keyword arguments. (optional)

        Returns:
            An async generator of StreamingChatMessageContent.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        # Add the chat history to the args in the event that it is needed for prompt template configuration
        arguments["chat_history"] = history

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        chat_completion_service, settings = await self._get_chat_completion_service_and_settings(
            kernel=kernel, arguments=arguments
        )

        chat = await self._setup_agent_chat_history(
            history=history,
            kernel=kernel,
            arguments=arguments,
        )

        message_count = len(chat)

        logger.debug(f"[{type(self).__name__}] Invoking {type(chat_completion_service).__name__}.")

        messages: AsyncGenerator[list[StreamingChatMessageContent], Any] = (
            chat_completion_service.get_streaming_chat_message_contents(
                chat_history=chat,
                settings=settings,
                kernel=kernel,
                arguments=arguments,
            )
        )

        logger.info(
            f"[{type(self).__name__}] Invoked {type(chat_completion_service).__name__} "
            f"with message count: {message_count}."
        )

        role = None
        message_builder: list[str] = []
        async for message_list in messages:
            for message in message_list:
                role = message.role
                message.name = self.name
                message_builder.append(message.content)
                yield message

        # Capture mutated messages related function calling / tools
        for message_index in range(message_count, len(chat)):
            message = chat[message_index]  # type: ignore
            message.name = self.name
            history.add_message(message)

        if role != AuthorRole.TOOL:
            history.add_message(
                ChatMessageContent(
                    role=role if role else AuthorRole.ASSISTANT, content="".join(message_builder), name=self.name
                )
            )

    async def _setup_agent_chat_history(
        self, history: ChatHistory, kernel: "Kernel", arguments: KernelArguments
    ) -> ChatHistory:
        """Setup the agent chat history."""
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
            raise KernelServiceNotFoundError(f"Chat completion service not found with service_id: {self.service_id}")

        assert isinstance(chat_completion_service, ChatCompletionClientBase)  # nosec
        assert settings is not None  # nosec

        return chat_completion_service, settings
