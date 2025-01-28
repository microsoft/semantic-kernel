# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import AsyncIterable
from functools import reduce
from typing import Any, ClassVar

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.action_group_utils import (
    parse_function_result_contents,
    parse_return_control_payload,
)
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BedrockAgent(BedrockAgentBase, Agent):
    """Bedrock Agent.

    Manages the interaction with Amazon Bedrock Agent Service.
    """

    channel_type: ClassVar[type[BedrockAgentChannel]] = BedrockAgentChannel

    @classmethod
    async def create_new_agent(
        cls,
        agent_name: str,
        foundation_model: str,
        role_arn: str,
        instruction: str,
        enable_code_interpreter: bool | None = None,
        enable_user_input: bool | None = None,
        enable_kernel_function: bool | None = None,
        **kwargs,
    ) -> "BedrockAgent":
        """Create a new agent asynchronously."""
        agent_base_class_kwargs = {}
        if "kernel" in kwargs:
            agent_base_class_kwargs["kernel"] = kwargs.pop("kernel")
        if "function_choice_behavior" in kwargs:
            agent_base_class_kwargs["function_choice_behavior"] = kwargs.pop("function_choice_behavior")

        bedrock_agent = cls(name=agent_name, instructions=instruction, **agent_base_class_kwargs)

        await bedrock_agent.create_agent(
            foundation_model,
            role_arn,
            enable_code_interpreter,
            enable_user_input,
            enable_kernel_function,
            **kwargs,
        )

        return bedrock_agent

    @classmethod
    async def use_existing_agent(cls, agent_arn: str, agent_id: str, agent_name: str, **kwargs) -> "BedrockAgent":
        """Use an existing agent asynchronously."""
        bedrock_agent_model = BedrockAgentModel(
            agent_arn=agent_arn,
            agent_id=agent_id,
            agent_name=agent_name,
        )

        agent_base_class_kwargs = {}
        if "kernel" in kwargs:
            agent_base_class_kwargs["kernel"] = kwargs.pop("kernel")
        if "function_choice_behavior" in kwargs:
            agent_base_class_kwargs["function_choice_behavior"] = kwargs.pop("function_choice_behavior")

        bedrock_agent = cls(agent_model=bedrock_agent_model, **agent_base_class_kwargs)
        bedrock_agent.agent_model = await bedrock_agent._get_agent()

        bedrock_agent.id = bedrock_agent.agent_model.agent_id
        bedrock_agent.name = bedrock_agent.agent_model.agent_name

        return bedrock_agent

    async def create_agent(
        self,
        foundation_model: str,
        role_arn: str,
        enable_code_interpreter: bool | None = None,
        enable_user_input: bool | None = None,
        enable_kernel_function: bool | None = None,
        **kwargs,
    ) -> None:
        """Create an agent asynchronously."""
        await self._create_agent(
            self.name,
            foundation_model,
            role_arn,
            self.instructions,
            **kwargs,
        )

        if enable_code_interpreter:
            await self._create_code_interpreter_action_group()
        if enable_user_input:
            await self._create_user_input_action_group()
        if enable_kernel_function:
            await self._create_kernel_function_action_group()

        await self._prepare_agent()
        self.id = self.agent_model.agent_id

    async def update_agent(
        self,
        agent_id,
        agent_name,
        role_arn,
        foundation_model,
        **kwargs,
    ) -> BedrockAgentModel:
        """Update an agent asynchronously."""
        return await self._update_agent(
            agent_id,
            agent_name,
            role_arn,
            foundation_model,
            **kwargs,
        )

    async def delete_agent(self, **kwargs) -> None:
        """Delete an agent asynchronously."""
        await self._delete_agent(**kwargs)

    async def create_code_interpreter_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable code interpretation."""
        return await self._create_code_interpreter_action_group(**kwargs)

    async def create_user_input_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable user input."""
        return await self._create_user_input_action_group(**kwargs)

    async def create_kernel_function_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable kernel function."""
        return await self._create_kernel_function_action_group(self.kernel, **kwargs)

    async def associate_agent_knowledge_base(self, knowledge_base_id, **kwargs) -> dict[str, Any]:
        """Associate an agent with a knowledge base."""
        return await self._associate_agent_knowledge_base(knowledge_base_id, **kwargs)

    async def disassociate_agent_knowledge_base(self, knowledge_base_id, **kwargs) -> None:
        """Disassociate an agent with a knowledge base."""
        return await self._disassociate_agent_knowledge_base(knowledge_base_id, **kwargs)

    async def list_associated_agent_knowledge_bases(self, **kwargs) -> dict[str, Any]:
        """List associated agent knowledge bases."""
        return await self._list_associated_agent_knowledge_bases(**kwargs)

    async def invoke(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke an agent."""
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
                        next(event for event in events if BedrockAgentEventType.RETURN_CONTROL in event)
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

    async def invoke_stream(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke an agent."""
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

            chat_history = ChatHistory()
            await asyncio.gather(
                *[
                    self.kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        function_call_count=len(function_calls),
                        request_index=request_index,
                    )
                    for function_call in function_calls
                ],
            )
            function_result_contents = [
                item
                for chat_message in chat_history.messages
                for item in chat_message.items
                if isinstance(item, FunctionResultContent)
            ]

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

    async def _handle_return_control_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle return control event."""
        return_control_payload = event[BedrockAgentEventType.RETURN_CONTROL]
        function_calls = parse_return_control_payload(return_control_payload)
        if not function_calls:
            raise AgentInvokeException("Function call is expected but not found in the response.")

        chat_history = ChatHistory()
        await asyncio.gather(
            *[
                self.kernel.invoke_function_call(
                    function_call=function_call,
                    chat_history=chat_history,
                    function_call_count=len(function_calls),
                )
                for function_call in function_calls
            ],
        )
        function_result_contents = [
            item
            for chat_message in chat_history.messages
            for item in chat_message.items
            if isinstance(item, FunctionResultContent)
        ]

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
            items=function_calls,
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
        )

    def _handle_streaming_files_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming file event."""
        files_event = event[BedrockAgentEventType.FILES]
        items = [
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
            items=items,
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
        )

    def _handle_streaming_trace_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Handle streaming trace event."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            name=self.name,
            inner_content=event,
            ai_model_id=self.agent_model.foundation_model,
            metadata=event[BedrockAgentEventType.TRACE],
        )

    # endregion
