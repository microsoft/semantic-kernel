# Copyright (c) Microsoft. All rights reserved.


import asyncio
import uuid
from collections.abc import AsyncIterable
from functools import reduce
from typing import Any, ClassVar

from pydantic import ValidationError

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.action_group_utils import (
    parse_function_result_contents,
    parse_return_control_payload,
)
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.bedrock_agent_settings import BedrockAgentSettings
from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
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
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import trace_agent_invocation


@experimental_class
class BedrockAgent(BedrockAgentBase, Agent):
    """Bedrock Agent.

    Manages the interaction with Amazon Bedrock Agent Service.
    """

    channel_type: ClassVar[type[AgentChannel]] = BedrockAgentChannel

    def __init__(
        self,
        name: str,
        *,
        id: str | None = None,
        agent_resource_role_arn: str | None = None,
        foundation_model: str | None = None,
        kernel: Kernel | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        arguments: KernelArguments | None = None,
        instructions: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Bedrock Agent.

        Note that this only creates the agent object and does not create the agent in the service.

        Args:
            name (str): The name of the agent.
            id (str, optional): The unique identifier of the agent.
            agent_resource_role_arn (str, optional): The ARN of the agent resource role.
                Overrides the one in the env file.
            foundation_model (str, optional): The foundation model. Overrides the one in the env file.
            kernel (Kernel, optional): The kernel to use.
            function_choice_behavior (FunctionChoiceBehavior, optional): The function choice behavior for accessing
                the kernel functions and filters.
            arguments (KernelArguments, optional): The kernel arguments.
                Invoke method arguments take precedence over the arguments provided here.
            instructions (str, optional): The instructions for the agent.
            prompt_template_config (PromptTemplateConfig, optional): The prompt template configuration.
                Cannot be set if instructions is set.
            env_file_path (str, optional): The path to the environment file.
            env_file_encoding (str, optional): The encoding of the environment file.
        """
        try:
            bedrock_agent_settings = BedrockAgentSettings.create(
                agent_resource_role_arn=agent_resource_role_arn,
                foundation_model=foundation_model,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise AgentInitializationException("Failed to initialize the Amazon Bedrock Agent settings.") from e

        bedrock_agent_model = BedrockAgentModel(
            agentId=id,
            agentName=name,
            foundationModel=bedrock_agent_settings.foundation_model,
        )

        prompt_template: PromptTemplateBase | None = None
        if instructions and prompt_template_config and prompt_template_config.template:
            raise AgentInitializationException("Cannot set both instructions and prompt_template_config.template.")
        if prompt_template_config:
            prompt_template = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )

        args: dict[str, Any] = {
            "agent_resource_role_arn": bedrock_agent_settings.agent_resource_role_arn,
            "name": name,
            "agent_model": bedrock_agent_model,
        }
        if id:
            args["id"] = id
        if instructions:
            args["instructions"] = instructions
        if kernel:
            args["kernel"] = kernel
        if function_choice_behavior:
            args["function_choice_behavior"] = function_choice_behavior
        if arguments:
            args["arguments"] = arguments
        if prompt_template:
            args["prompt_template"] = prompt_template

        super().__init__(**args)

    # region convenience class methods

    @classmethod
    async def create(
        cls,
        name: str,
        *,
        agent_resource_role_arn: str | None = None,
        foundation_model: str | None = None,
        kernel: Kernel | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        arguments: KernelArguments | None = None,
        instructions: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        enable_code_interpreter: bool | None = None,
        enable_user_input: bool | None = None,
        enable_kernel_function: bool | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "BedrockAgent":
        """Create a new agent asynchronously.

        This is a convenience method that creates an instance of BedrockAgent and then creates the agent on the service.

        Args:
            name (str): The name of the agent.
            agent_resource_role_arn (str, optional): The ARN of the agent resource role.
            foundation_model (str, optional): The foundation model.
            kernel (Kernel, optional): The kernel to use.
            function_choice_behavior (FunctionChoiceBehavior, optional): The function choice behavior for accessing
                the kernel functions and filters.
            arguments (KernelArguments, optional): The kernel arguments.
            instructions (str, optional): The instructions for the agent.
            prompt_template_config (PromptTemplateConfig, optional): The prompt template configuration.
            enable_code_interpreter (bool, optional): Enable code interpretation.
            enable_user_input (bool, optional): Enable user input.
            enable_kernel_function (bool, optional): Enable kernel function.
            env_file_path (str, optional): The path to the environment file.
            env_file_encoding (str, optional): The encoding of the environment file.

        Returns:
            An instance of BedrockAgent with the created agent.
        """
        bedrock_agent = cls(
            name,
            agent_resource_role_arn=agent_resource_role_arn,
            foundation_model=foundation_model,
            kernel=kernel,
            function_choice_behavior=function_choice_behavior,
            arguments=arguments,
            instructions=instructions,
            prompt_template_config=prompt_template_config,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )

        return await bedrock_agent.create_agent(
            enable_code_interpreter=enable_code_interpreter,
            enable_user_input=enable_user_input,
            enable_kernel_function=enable_kernel_function,
        )

    @classmethod
    async def retrieve(
        cls,
        id: str,
        name: str,
        *,
        agent_resource_role_arn: str | None = None,
        kernel: Kernel | None = None,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "BedrockAgent":
        """Retrieve an agent asynchronously.

        This is a convenience method that creates an instance of BedrockAgent and
        then retrieves an existing agent from the service.

        Note that:
        1. If the agent has existing action groups that require control returned to the user,
        a kernel with the required functions must be provided.
        2. If the agent has not been prepared, client code must prepare the agent by calling `prepare_agent()`.

        If client code want to enable the available action groups, it can call the respective methods:
        - `create_code_interpreter_action_group()`
        - `create_user_input_action_group()`
        - `create_kernel_function_action_group()`

        Args:
            id (str): The unique identifier of the agent.
            name (str): The name of the agent.
            agent_resource_role_arn (str, optional): The ARN of the agent resource role.
            kernel (Kernel, optional): The kernel to use.
            function_choice_behavior (FunctionChoiceBehavior, optional): The function choice behavior for accessing
                the kernel functions and filters.
            env_file_path (str, optional): The path to the environment file.
            env_file_encoding (str, optional): The encoding of the environment file.
        """
        bedrock_agent = cls(
            name,
            id=id,
            agent_resource_role_arn=agent_resource_role_arn,
            kernel=kernel,
            function_choice_behavior=function_choice_behavior,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        bedrock_agent.agent_model = await bedrock_agent._get_agent()

        return bedrock_agent

    @classmethod
    def create_session_id(cls) -> str:
        """Create a new session identifier.

        It is the caller's responsibility to maintain the session ID
        to continue the session with the agent.

        Find the requirement for the session identifier here:
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_InvokeAgent.html#API_agent-runtime_InvokeAgent_RequestParameters
        """
        return str(uuid.uuid4())

    # endregion

    async def create_agent(
        self,
        *,
        enable_code_interpreter: bool | None = None,
        enable_user_input: bool | None = None,
        enable_kernel_function: bool | None = None,
        **kwargs,
    ) -> "BedrockAgent":
        """Create an agent on the service asynchronously. This will also prepare the agent so that it ready for use.

        Args:
            enable_code_interpreter (bool, optional): Enable code interpretation.
            enable_user_input (bool, optional): Enable user input.
            enable_kernel_function (bool, optional): Enable kernel function.
            **kwargs: Additional keyword arguments.

        Returns:
            An instance of BedrockAgent with the created agent.
        """
        if not self.agent_model.foundation_model:
            raise AgentInitializationException("Foundation model is required to create an agent.")

        await self._create_agent(
            self.instructions or await self.format_instructions(self.kernel, self.arguments) or "",
            **kwargs,
        )

        if enable_code_interpreter:
            await self.create_code_interpreter_action_group()
        if enable_user_input:
            await self.create_user_input_action_group()
        if enable_kernel_function:
            await self._create_kernel_function_action_group(self.kernel)

        await self.prepare_agent()

        if not self.agent_model.agent_id:
            raise AgentInitializationException("Agent ID is not set.")
        self.id = self.agent_model.agent_id

        return self

    @trace_agent_invocation
    async def invoke(
        self,
        session_id: str,
        input_text: str,
        *,
        agent_alias: str | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke an agent.

        Args:
            session_id (str): The session identifier. This is used to maintain the session state in the service.
            input_text (str): The input text.
            agent_alias (str, optional): The agent alias.
            arguments (KernelArguments, optional): The kernel arguments to override the current arguments.
            kernel (Kernel, optional): The kernel to override the current kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            An async iterable of chat message content.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = False
        kwargs.setdefault("sessionState", {})

        for _ in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
            response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)

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

                yield chat_message_content
                return

    @trace_agent_invocation
    async def invoke_stream(
        self,
        session_id: str,
        input_text: str,
        *,
        agent_alias: str | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke an agent with streaming.

        Args:
            session_id (str): The session identifier. This is used to maintain the session state in the service.
            input_text (str): The input text.
            agent_alias (str, optional): The agent alias.
            arguments (KernelArguments, optional): The kernel arguments to override the current arguments.
            kernel (Kernel, optional): The kernel to override the current kernel.
            **kwargs: Additional keyword arguments.

        Returns:
            An async iterable of streaming chat message content
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = True
        kwargs.setdefault("sessionState", {})

        for request_index in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
            response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)

            all_function_call_messages: list[StreamingChatMessageContent] = []
            for event in response.get("completion", []):
                if BedrockAgentEventType.CHUNK in event:
                    yield self._handle_streaming_chunk_event(event)
                    continue
                if BedrockAgentEventType.FILES in event:
                    yield self._handle_streaming_files_event(event)
                    continue
                if BedrockAgentEventType.TRACE in event:
                    yield self._handle_streaming_trace_event(event)
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
