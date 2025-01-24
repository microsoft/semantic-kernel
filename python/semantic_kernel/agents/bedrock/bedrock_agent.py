# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import AsyncIterable
from functools import reduce
from typing import Any

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.action_group_utils import (
    parse_function_result_contents,
    parse_return_control_payload,
)
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BedrockAgent(BedrockAgentBase, Agent):
    """Bedrock Agent.

    Manages the interaction with Amazon Bedrock Agent Service.
    """

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
        await self._prepare_agent()

        if enable_code_interpreter:
            await self._create_code_interpreter_action_group()
        if enable_user_input:
            await self._create_user_input_action_group()
        if enable_kernel_function:
            await self._create_kernel_function_action_group()

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

    async def delete_agent(self, agent_id, **kwargs) -> None:
        """Delete an agent asynchronously."""
        await self._delete_agent(agent_id, **kwargs)

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

        if not self.function_choice_behavior.auto_invoke_kernel_functions:
            response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)
            # When streaming is disabled, the response will be a single event.
            for event in response.get("completion", []):
                yield self._create_chat_message_content(event)
        else:
            session_state: dict[str, Any] | None = None
            for request_index in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
                if session_state:
                    # Session state is used to send function call results back to the agent.
                    kwargs["sessionState"] = session_state
                response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)

                # When streaming is disabled, the response will be a single event.
                for event in response.get("completion", []):
                    chat_message_content = self._create_chat_message_content(event)
                    function_calls = [
                        item for item in chat_message_content.items if isinstance(item, FunctionCallContent)
                    ]

                    if not function_calls:
                        yield chat_message_content
                        return

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

                    session_state = {
                        "invocationId": function_calls[0].id,
                        "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
                    }

    async def invoke_stream(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke an agent."""
        kwargs.setdefault("streamingConfigurations", {})["streamFinalResponse"] = True

        if not self.function_choice_behavior.auto_invoke_kernel_functions:
            response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)
            # When streaming is disabled, the response will be a single event.
            for event in response.get("completion", []):
                yield self._create_streaming_chat_message_content(event)
        else:
            session_state: dict[str, Any] | None = None
            for request_index in range(self.function_choice_behavior.maximum_auto_invoke_attempts):
                if session_state:
                    # Session state is used to send function call results back to the agent.
                    kwargs["sessionState"] = session_state
                response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)

                all_messages: list[StreamingChatMessageContent] = []
                for event in response.get("completion", []):
                    message = self._create_streaming_chat_message_content(event)
                    all_messages.append(message)
                    if not any(isinstance(item, FunctionCallContent) for item in message.items):
                        # Only streaming back the messages that contain text content
                        yield message

                full_message: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
                function_calls = [item for item in full_message.items if isinstance(item, FunctionCallContent)]

                if not function_calls:
                    return

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

                session_state = {
                    "invocationId": function_calls[0].id,
                    "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
                }

    def _create_chat_message_content(self, event: dict[str, Any]) -> ChatMessageContent:
        """Create a chat message content."""
        if "chunk" in event:
            # Text response
            chunk = event["chunk"]
            completion = chunk["bytes"].decode()

            return ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=completion,
                name=self.name,
                inner_content=event,
                ai_model_id=self.agent_model.foundation_model,
            )
        if "returnControl" in event:
            # Tool call response
            return_control_payload = event["returnControl"]
            function_calls = parse_return_control_payload(return_control_payload)

            return ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                items=function_calls,
                name=self.name,
                inner_content=event,
                ai_model_id=self.agent_model.foundation_model,
            )
        raise ValueError(f"Unknown event type: {event}")

    def _create_streaming_chat_message_content(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Create a streaming chat message content."""
        if "chunk" in event:
            # Text response
            chunk = event["chunk"]
            completion = chunk["bytes"].decode()

            return StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                content=completion,
                name=self.name,
                inner_content=event,
                ai_model_id=self.agent_model.foundation_model,
            )
        if "returnControl" in event:
            # Tool call response
            return_control_payload = event["returnControl"]
            function_calls = parse_return_control_payload(return_control_payload)

            return StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=function_calls,
                name=self.name,
                inner_content=event,
                ai_model_id=self.agent_model.foundation_model,
            )
        raise ValueError(f"Unknown event type: {event}")
