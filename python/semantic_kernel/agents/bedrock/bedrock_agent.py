# Copyright (c) Microsoft. All rights reserved.


import asyncio
import logging
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from functools import partial, reduce
from typing import Any, ClassVar

from pydantic import ValidationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
from semantic_kernel.agents.bedrock.action_group_utils import (
    parse_function_result_contents,
    parse_return_control_payload,
)
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.bedrock_agent_settings import BedrockAgentSettings
from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.async_utils import run_in_executor
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)

logger = logging.getLogger(__name__)


@experimental
class BedrockAgentThread(AgentThread):
    """Bedrock Agent Thread class."""

    def __init__(
        self,
        bedrock_runtime_client: Any,
        session_id: str | None = None,
    ) -> None:
        """Initialize the Bedrock Agent Thread.

        The underlying Bedrock session of the thread is created when the thread is started.
        https://docs.aws.amazon.com/bedrock/latest/userguide/sessions.html

        Args:
            bedrock_runtime_client: The Bedrock Runtime Client.
            session_id: The session ID.
        """
        super().__init__()
        self._bedrock_runtime_client = bedrock_runtime_client
        self._id = session_id

    @override
    async def _create(self) -> str:
        """Starts the thread and returns the underlying Bedrock session ID."""
        response = await run_in_executor(
            None,
            partial(
                self._bedrock_runtime_client.create_session,
            ),
        )
        self._id = response["sessionId"]
        return self._id  # type: ignore

    @override
    async def _delete(self) -> None:
        """Ends the current thread.

        This will only end the underlying Bedrock session but not delete it.
        """
        # Must end the session before deleting it.
        await run_in_executor(
            None,
            partial(
                self._bedrock_runtime_client.end_session,
                sessionIdentifier=self._id,
            ),
        )

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        raise NotImplementedError(
            "This method is not implemented for BedrockAgentThread. "
            "Messages and responses are automatically handled by the Bedrock service."
        )


@experimental
class BedrockAgent(BedrockAgentBase):
    """Bedrock Agent.

    Manages the interaction with Amazon Bedrock Agent Service.
    """

    channel_type: ClassVar[type[AgentChannel]] = BedrockAgentChannel

    def __init__(
        self,
        agent_model: BedrockAgentModel | dict[str, Any],
        *,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        arguments: KernelArguments | None = None,
        bedrock_runtime_client: Any | None = None,
        bedrock_client: Any | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Bedrock Agent.

        Note that this only creates the agent object and does not create the agent in the service.

        Args:
            agent_model (BedrockAgentModel | dict[str, Any]): The agent model.
            function_choice_behavior (FunctionChoiceBehavior, optional): The function choice behavior for accessing
                the kernel functions and filters.
            kernel (Kernel, optional): The kernel to use.
            plugins (list[KernelPlugin | object] | dict[str, KernelPlugin | object], optional): The plugins to use.
            arguments (KernelArguments, optional): The kernel arguments.
                Invoke method arguments take precedence over the arguments provided here.
            bedrock_runtime_client: The Bedrock Runtime Client.
            bedrock_client: The Bedrock Client.
            **kwargs: Additional keyword arguments.
        """
        args: dict[str, Any] = {
            "agent_model": agent_model,
            **kwargs,
        }

        if function_choice_behavior:
            args["function_choice_behavior"] = function_choice_behavior
        if kernel:
            args["kernel"] = kernel
        if plugins:
            args["plugins"] = plugins
        if arguments:
            args["arguments"] = arguments
        if bedrock_runtime_client:
            args["bedrock_runtime_client"] = bedrock_runtime_client
        if bedrock_client:
            args["bedrock_client"] = bedrock_client

        super().__init__(**args)

    # region convenience class methods

    @classmethod
    async def create_and_prepare_agent(
        cls,
        name: str,
        instructions: str,
        *,
        agent_resource_role_arn: str | None = None,
        foundation_model: str | None = None,
        bedrock_runtime_client: Any | None = None,
        bedrock_client: Any | None = None,
        kernel: Kernel | None = None,
        plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object] | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        arguments: KernelArguments | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "BedrockAgent":
        """Create a new agent asynchronously.

        This is a convenience method that creates an instance of BedrockAgent and then creates the agent on the service.

        Args:
            name (str): The name of the agent.
            instructions (str, optional): The instructions for the agent.
            agent_resource_role_arn (str, optional): The ARN of the agent resource role.
            foundation_model (str, optional): The foundation model.
            bedrock_runtime_client (Any, optional): The Bedrock Runtime Client.
            bedrock_client (Any, optional): The Bedrock Client.
            kernel (Kernel, optional): The kernel to use.
            plugins (list[KernelPlugin | object] | dict[str, KernelPlugin | object], optional): The plugins to use.
            function_choice_behavior (FunctionChoiceBehavior, optional): The function choice behavior for accessing
                the kernel functions and filters. Only FunctionChoiceType.AUTO is supported.
            arguments (KernelArguments, optional): The kernel arguments.
            prompt_template_config (PromptTemplateConfig, optional): The prompt template configuration.
            env_file_path (str, optional): The path to the environment file.
            env_file_encoding (str, optional): The encoding of the environment file.

        Returns:
            An instance of BedrockAgent with the created agent.
        """
        try:
            bedrock_agent_settings = BedrockAgentSettings(
                agent_resource_role_arn=agent_resource_role_arn,
                foundation_model=foundation_model,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise AgentInitializationException("Failed to initialize the Amazon Bedrock Agent settings.") from e

        import boto3
        from botocore.exceptions import ClientError

        bedrock_runtime_client = bedrock_runtime_client or boto3.client("bedrock-agent-runtime")
        bedrock_client = bedrock_client or boto3.client("bedrock-agent")

        try:
            response = await run_in_executor(
                None,
                partial(
                    bedrock_client.create_agent,
                    agentName=name,
                    foundationModel=bedrock_agent_settings.foundation_model,
                    agentResourceRoleArn=bedrock_agent_settings.agent_resource_role_arn,
                    instruction=instructions,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to create agent {name}.")
            raise AgentInitializationException("Failed to create the Amazon Bedrock Agent.") from e

        bedrock_agent = cls(
            response["agent"],
            function_choice_behavior=function_choice_behavior,
            kernel=kernel,
            plugins=plugins,
            arguments=arguments,
            bedrock_runtime_client=bedrock_runtime_client,
            bedrock_client=bedrock_client,
        )

        # The agent will first enter the CREATING status.
        # When the operation finishes, it will enter the NOT_PREPARED status.
        # We need to wait for the agent to reach the NOT_PREPARED status before we can prepare it.
        await bedrock_agent._wait_for_agent_status(BedrockAgentStatus.NOT_PREPARED)
        await bedrock_agent.prepare_agent_and_wait_until_prepared()

        return bedrock_agent

    # endregion

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        agent_alias: str | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent.

        Args:
            messages (str | ChatMessageContent | list[str | ChatMessageContent]): The messages.
            thread (AgentThread, optional): The thread. This is used to maintain the session state in the service.
            agent_alias (str, optional): The agent alias.
            arguments (KernelArguments, optional): The kernel arguments to override the current arguments.
            kernel (Kernel, optional): The kernel to override the current kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            A chat message content with the response.
        """
        if not isinstance(messages, str) and not isinstance(messages, ChatMessageContent):
            raise AgentInvokeException("Messages must be a string or a ChatMessageContent for BedrockAgent.")

        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: BedrockAgentThread(bedrock_runtime_client=self.bedrock_runtime_client),
            expected_type=BedrockAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = False
        kwargs.setdefault("sessionState", {})

        for _ in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
            response = await self._invoke_agent(thread.id, messages, agent_alias, **kwargs)

            events: list[dict[str, Any]] = []
            for event in response.get("completion", []):
                events.append(event)

            if any(BedrockAgentEventType.RETURN_CONTROL in event for event in events):
                # Check if there is function call requests. If there are function calls,
                # parse and invoke them and return the results back to the agent.
                # Not yielding the function call results back to the user.
                kwargs["sessionState"].update(
                    await self._handle_return_control_event(
                        next(event for event in events if BedrockAgentEventType.RETURN_CONTROL in event),
                        kernel,
                        arguments,
                    )
                )
            else:
                # For the rest of the events, the chunk will become the chat message content.
                # If there are files or trace, they will be added to the chat message content.
                file_items: list[BinaryContent] | None = None
                trace_metadata: dict[str, Any] | None = None
                chat_message_content: ChatMessageContent | None = None
                for event in events:
                    if BedrockAgentEventType.CHUNK in event:
                        chat_message_content = self._handle_chunk_event(event)
                    elif BedrockAgentEventType.FILES in event:
                        file_items = self._handle_files_event(event)
                    elif BedrockAgentEventType.TRACE in event:
                        trace_metadata = self._handle_trace_event(event)

                if not chat_message_content or not chat_message_content.content:
                    raise AgentInvokeException("Chat message content is expected but not found in the response.")

                if file_items:
                    chat_message_content.items.extend(file_items)
                if trace_metadata:
                    chat_message_content.metadata.update({"trace": trace_metadata})

                if not chat_message_content:
                    raise AgentInvokeException("No response from the agent.")

                chat_message_content.metadata["thread_id"] = thread.id
                return AgentResponseItem(message=chat_message_content, thread=thread)

        raise AgentInvokeException(
            "Failed to get a response from the agent. Please consider increasing the auto invoke attempts."
        )

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_new_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        agent_alias: str | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke an agent.

        Args:
            messages (str | ChatMessageContent | list[str | ChatMessageContent]): The messages.
            thread (AgentThread, optional): The thread. This is used to maintain the session state in the service.
            on_new_message: A callback function to handle intermediate steps of the agent's execution.
            agent_alias (str, optional): The agent alias.
            arguments (KernelArguments, optional): The kernel arguments to override the current arguments.
            kernel (Kernel, optional): The kernel to override the current kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            An async iterable of chat message content.
        """
        if not isinstance(messages, str) and not isinstance(messages, ChatMessageContent):
            raise AgentInvokeException("Messages must be a string or a ChatMessageContent for BedrockAgent.")

        if on_new_message:
            logger.warning("The on_new_message callback is not supported for BedrockAgent.")

        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: BedrockAgentThread(bedrock_runtime_client=self.bedrock_runtime_client),
            expected_type=BedrockAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = False
        kwargs.setdefault("sessionState", {})

        for _ in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
            response = await self._invoke_agent(thread.id, messages, agent_alias, **kwargs)

            events: list[dict[str, Any]] = []
            for event in response.get("completion", []):
                events.append(event)

            if any(BedrockAgentEventType.RETURN_CONTROL in event for event in events):
                # Check if there is function call requests. If there are function calls,
                # parse and invoke them and return the results back to the agent.
                # Not yielding the function call results back to the user.
                kwargs["sessionState"].update(
                    await self._handle_return_control_event(
                        next(event for event in events if BedrockAgentEventType.RETURN_CONTROL in event),
                        kernel,
                        arguments,
                    )
                )
            else:
                for event in events:
                    if BedrockAgentEventType.CHUNK in event:
                        cmc = self._handle_chunk_event(event)
                        cmc.metadata["thread_id"] = thread.id
                        yield AgentResponseItem(message=cmc, thread=thread)
                    elif BedrockAgentEventType.FILES in event:
                        cmc = ChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            items=self._handle_files_event(event),  # type: ignore
                            name=self.name,
                            inner_content=event,
                            ai_model_id=self.agent_model.foundation_model,
                        )
                        cmc.metadata["thread_id"] = thread.id
                        yield AgentResponseItem(message=cmc, thread=thread)
                    elif BedrockAgentEventType.TRACE in event:
                        cmc = ChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            name=self.name,
                            content="",
                            inner_content=event,
                            ai_model_id=self.agent_model.foundation_model,
                            metadata=self._handle_trace_event(event),
                        )
                        cmc.metadata["thread_id"] = thread.id
                        yield AgentResponseItem(message=cmc, thread=thread)

                return

        raise AgentInvokeException(
            "Failed to get a response from the agent. Please consider increasing the auto invoke attempts."
        )

    @trace_agent_invocation
    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_new_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        agent_alias: str | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Invoke an agent with streaming.

        Args:
            messages (str | ChatMessageContent | list[str | ChatMessageContent]): The messages.
            thread (AgentThread, optional): The thread. This is used to maintain the session state in the service.
            on_new_message: A callback function to handle intermediate steps of the
                            agent's execution as fully formed messages.
            agent_alias (str, optional): The agent alias.
            arguments (KernelArguments, optional): The kernel arguments to override the current arguments.
            kernel (Kernel, optional): The kernel to override the current kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            An async iterable of streaming chat message content
        """
        if not isinstance(messages, str) and not isinstance(messages, ChatMessageContent):
            raise AgentInvokeException("Messages must be a string or a ChatMessageContent for BedrockAgent.")

        if on_new_message:
            logger.warning("The on_new_message callback is not supported for BedrockAgent.")

        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: BedrockAgentThread(bedrock_runtime_client=self.bedrock_runtime_client),
            expected_type=BedrockAgentThread,
        )
        assert thread.id is not None  # nosec

        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self._merge_arguments(arguments)

        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = True
        kwargs.setdefault("sessionState", {})

        for request_index in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
            response = await self._invoke_agent(thread.id, messages, agent_alias, **kwargs)

            all_function_call_messages: list[StreamingChatMessageContent] = []
            for event in response.get("completion", []):
                if BedrockAgentEventType.CHUNK in event:
                    scmc = self._handle_streaming_chunk_event(event)
                    scmc.metadata["thread_id"] = thread.id
                    yield AgentResponseItem(message=scmc, thread=thread)
                    continue
                if BedrockAgentEventType.FILES in event:
                    scmc = self._handle_streaming_files_event(event)
                    scmc.metadata["thread_id"] = thread.id
                    yield AgentResponseItem(message=scmc, thread=thread)
                    continue
                if BedrockAgentEventType.TRACE in event:
                    scmc = self._handle_streaming_trace_event(event)
                    scmc.metadata["thread_id"] = thread.id
                    yield AgentResponseItem(message=scmc, thread=thread)
                    continue
                if BedrockAgentEventType.RETURN_CONTROL in event:
                    all_function_call_messages.append(self._handle_streaming_return_control_event(event))
                    continue

            if not all_function_call_messages:
                return

            full_message: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_function_call_messages)
            function_calls = [item for item in full_message.items if isinstance(item, FunctionCallContent)]
            function_result_contents = await self._handle_function_call_contents(function_calls)
            kwargs["sessionState"].update({
                "invocationId": function_calls[0].id,
                "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
            })

    # region non streaming Event Handlers

    def _handle_chunk_event(self, event: dict[str, Any]) -> ChatMessageContent:
        """Create a chat message content."""
        chunk = event[BedrockAgentEventType.CHUNK]
        completion = chunk["bytes"].decode()

        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=completion,
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
            metadata=chunk,
        )

    async def _handle_return_control_event(
        self,
        event: dict[str, Any],
        kernel: Kernel,
        kernel_arguments: KernelArguments,
    ) -> dict[str, Any]:
        """Handle return control event."""
        return_control_payload = event[BedrockAgentEventType.RETURN_CONTROL]
        function_calls = parse_return_control_payload(return_control_payload)
        if not function_calls:
            raise AgentInvokeException("Function call is expected but not found in the response.")

        function_result_contents = await self._handle_function_call_contents(function_calls)

        return {
            "invocationId": function_calls[0].id,
            "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
        }

    def _handle_files_event(self, event: dict[str, Any]) -> list[BinaryContent]:
        """Handle file event."""
        files_event = event[BedrockAgentEventType.FILES]
        return [
            BinaryContent(
                data=file["bytes"],
                data_format="base64",
                mime_type=file["type"],
                metadata={"name": file["name"]},
            )
            for file in files_event["files"]
        ]

    def _handle_trace_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle trace event."""
        return event[BedrockAgentEventType.TRACE]

    # endregion

    # region streaming Event Handlers

    def _handle_streaming_chunk_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming chunk event."""
        chunk = event[BedrockAgentEventType.CHUNK]
        completion = chunk["bytes"].decode()

        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            content=completion,
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
        )

    def _handle_streaming_return_control_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming return control event."""
        return_control_payload = event[BedrockAgentEventType.RETURN_CONTROL]
        function_calls = parse_return_control_payload(return_control_payload)

        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            items=function_calls,  # type: ignore
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
        )

    def _handle_streaming_files_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming file event."""
        files_event = event[BedrockAgentEventType.FILES]
        items: list[BinaryContent] = [
            BinaryContent(
                data=file["bytes"],
                data_format="base64",
                mime_type=file["type"],
                metadata={"name": file["name"]},
            )
            for file in files_event["files"]
        ]

        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            items=items,  # type: ignore
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
        )

    def _handle_streaming_trace_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming trace event."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            items=[],
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
            metadata=event[BedrockAgentEventType.TRACE],
        )

    # endregion

    async def _handle_function_call_contents(
        self,
        function_call_contents: list[FunctionCallContent],
    ) -> list[FunctionResultContent]:
        """Handle function call contents."""
        chat_history = ChatHistory()
        await asyncio.gather(
            *[
                self.kernel.invoke_function_call(
                    function_call=function_call,
                    chat_history=chat_history,
                    arguments=self.arguments,
                    function_call_count=len(function_call_contents),
                )
                for function_call in function_call_contents
            ],
        )

        return [
            item
            for chat_message in chat_history.messages
            for item in chat_message.items
            if isinstance(item, FunctionResultContent)
        ]

    async def create_channel(self, thread_id: str | None = None) -> AgentChannel:
        """Create a ChatHistoryChannel.

        Args:
            chat_history: The chat history for the channel. If None, a new ChatHistory instance will be created.
            thread_id: The ID of the thread. If None, a new thread will be created.

        Returns:
            An instance of AgentChannel.
        """
        from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgentThread

        BedrockAgentChannel.model_rebuild()

        thread = BedrockAgentThread(bedrock_runtime_client=self.bedrock_runtime_client, session_id=thread_id)

        if thread.id is None:
            await thread.create()

        return BedrockAgentChannel(thread=thread)

    @override
    async def _notify_thread_of_new_message(self, thread, new_message):
        """Bedrock agent doesn't need to notify the thread of new messages.

        The new message is passed to the agent when invoking the agent.
        """
        pass
