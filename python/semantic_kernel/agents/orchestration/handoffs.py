# Copyright (c) Microsoft. All rights reserved.


import asyncio
import inspect
import logging
import sys
from collections.abc import Awaitable, Callable
from functools import partial

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.orchestration.agent_actor_base import AgentActorBase
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationBase, TIn, TOut
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import message_handler
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.agents.runtime.in_process.type_subscription import TypeSubscription
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover


logger: logging.Logger = logging.getLogger(__name__)

# region Messages and Types


# A type alias for a mapping of agent names to their descriptions
# of the possible handoff connections for an agent.
AgentHandoffs = dict[str, str]


@experimental
class OrchestrationHandoffs(dict[str, AgentHandoffs]):
    """A dictionary mapping agent names to their handoff connections.

    Handoff connections are represented as a dictionary where the key is the target agent name
    and the value is a description of the handoff connection. For example:
    {
        "AgentA": {
            "AgentB": "Transfer to Agent B for further assistance.",
            "AgentC": "Transfer to Agent C for technical support."
        },
        "AgentB": {
            "AgentA": "Transfer to Agent A for general inquiries.",
            "AgentC": "Transfer to Agent C for billing issues."
        }
    }

    This class allows for easy addition of handoff connections between agents.
    """

    def add(self, source_agent: str | Agent, target_agent: str | Agent, description: str | None = None) -> "Self":
        """Add a handoff connection to the source agent.

        Args:
            source_agent (str | Agent): The source agent name or instance.
            target_agent (str | Agent): The target agent name or instance.
            description (str | None): The description of the handoff connection.

        Returns:
            Self: The updated orchestration handoffs, allowing for method chaining.
        """
        return self._add(
            source_agent=source_agent if isinstance(source_agent, str) else source_agent.name,
            target_agent=target_agent if isinstance(target_agent, str) else target_agent.name,
            description=description or target_agent.description or "" if isinstance(target_agent, Agent) else "",
        )

    def add_many(self, source_agent: str | Agent, target_agents: list[str | Agent] | AgentHandoffs) -> "Self":
        """Add multiple handoff connections to the source agent.

        Args:
            source_agent (str | Agent): The source agent name or instance.
            target_agents (list[str | Agent] | AgentHandoffs): A list of target agent names or instances.

        Returns:
            Self: The updated orchestration handoffs, allowing for method chaining.
        """
        if isinstance(target_agents, list):
            for target_agent in target_agents:
                self._add(
                    source_agent=source_agent if isinstance(source_agent, str) else source_agent.name,
                    target_agent=target_agent if isinstance(target_agent, str) else target_agent.name,
                    description=target_agent.description or "" if isinstance(target_agent, Agent) else "",
                )
        elif isinstance(target_agents, dict):
            for target_agent_name, description in target_agents.items():
                self._add(
                    source_agent=source_agent if isinstance(source_agent, str) else source_agent.name,
                    target_agent=target_agent_name,
                    description=description,
                )
        return self

    def _add(self, source_agent: str, target_agent: str, description: str) -> "Self":
        """Helper method to add a handoff connection."""
        self.setdefault(source_agent, AgentHandoffs())[target_agent] = description or ""

        return self


@experimental
class HandoffStartMessage(KernelBaseModel):
    """A start message type to kick off a handoff group chat."""

    body: DefaultTypeAlias


@experimental
class HandoffRequestMessage(KernelBaseModel):
    """A request message type for agents in a handoff group chat."""

    agent_name: str


@experimental
class HandoffResponseMessage(KernelBaseModel):
    """A response message type from agents in a handoff group chat."""

    body: ChatMessageContent


HANDOFF_PLUGIN_NAME = "Handoff"


# endregion Messages and Types

# region HandoffAgentActor


@experimental
class HandoffAgentActor(AgentActorBase):
    """An agent actor that handles handoff messages in a group chat."""

    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        handoff_connections: AgentHandoffs,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
        streaming_agent_response_callback: Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        | None = None,
        human_response_function: Callable[[], Awaitable[ChatMessageContent] | ChatMessageContent] | None = None,
    ) -> None:
        """Initialize the handoff agent actor."""
        self._handoff_connections = handoff_connections
        self._result_callback = result_callback

        self._kernel = agent.kernel.clone()
        self._add_handoff_functions()

        self._handoff_agent_name: str | None = None
        self._task_completed = False
        self._human_response_function = human_response_function

        super().__init__(
            agent=agent,
            internal_topic_type=internal_topic_type,
            agent_response_callback=agent_response_callback,
            streaming_agent_response_callback=streaming_agent_response_callback,
        )

    def _add_handoff_functions(self) -> None:
        """Add handoff functions to the agent's kernel."""
        functions: list[KernelFunctionFromMethod] = []
        for handoff_agent_name, handoff_description in self._handoff_connections.items():
            function_name = f"transfer_to_{handoff_agent_name}"
            function_description = handoff_description
            return_parameter = KernelParameterMetadata(
                name="return",
                description="",
                default_value=None,
                type_="None",
                type_object=None,
                is_required=False,
            )
            function_metadata = KernelFunctionMetadata(
                name=function_name,
                description=function_description,
                parameters=[],
                return_parameter=return_parameter,
                is_prompt=False,
                is_asynchronous=True,
                plugin_name=HANDOFF_PLUGIN_NAME,
                additional_properties={},
            )
            functions.append(
                KernelFunctionFromMethod.model_construct(
                    metadata=function_metadata,
                    method=partial(self._handoff_to_agent, handoff_agent_name),
                )
            )
        functions.append(KernelFunctionFromMethod(self._complete_task, plugin_name=HANDOFF_PLUGIN_NAME))
        self._kernel.add_plugin(plugin=KernelPlugin(name=HANDOFF_PLUGIN_NAME, functions=functions))
        self._kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, self._handoff_function_filter)

    async def _handoff_to_agent(self, agent_name: str) -> None:
        """Handoff the conversation to another agent."""
        logger.debug(f"{self.id}: Setting handoff agent name to {agent_name}.")
        self._handoff_agent_name = agent_name

    async def _handoff_function_filter(self, context: AutoFunctionInvocationContext, next):
        """A filter to terminate an agent when it decides to handoff the conversation to another agent."""
        await next(context)
        if context.function.plugin_name == HANDOFF_PLUGIN_NAME:
            context.terminate = True

    @kernel_function(
        name="complete_task", description="Complete the task with a summary when no further requests are given."
    )
    async def _complete_task(self, task_summary: str) -> None:
        """End the task with a summary."""
        logger.debug(f"{self.id}: Completing task with summary: {task_summary}")
        if self._result_callback:
            await self._result_callback(
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    name=self._agent.name,
                    content=f"Task is completed with summary: {task_summary}",
                )
            )
        self._task_completed = True

    @message_handler
    async def _handle_start_message(self, message: HandoffStartMessage, cts: MessageContext) -> None:
        logger.debug(f"{self.id}: Received handoff start message.")
        if isinstance(message.body, ChatMessageContent):
            if self._agent_thread:
                await self._agent_thread.on_new_message(message.body)
            else:
                self._chat_history.add_message(message.body)
        elif isinstance(message.body, list) and all(isinstance(m, ChatMessageContent) for m in message.body):
            for m in message.body:
                if self._agent_thread:
                    await self._agent_thread.on_new_message(m)
                else:
                    self._chat_history.add_message(m)
        else:
            raise ValueError(f"Invalid message body type: {type(message.body)}. Expected {DefaultTypeAlias}.")

    @message_handler
    async def _handle_response_message(self, message: HandoffResponseMessage, cts: MessageContext) -> None:
        """Handle a response message from an agent in the handoff group."""
        logger.debug(f"{self.id}: Received handoff response message.")
        if self._agent_thread is not None:
            await self._agent_thread.on_new_message(message.body)
        else:
            self._chat_history.add_message(message.body)

    @message_handler
    async def _handle_request_message(self, message: HandoffRequestMessage, cts: MessageContext) -> None:
        """Handle a request message from an agent in the handoff group."""
        if message.agent_name != self._agent.name:
            return
        logger.debug(f"{self.id}: Received handoff request message.")

        response = await self._invoke_agent_with_potentially_no_response(kernel=self._kernel)

        while not self._task_completed:
            if self._handoff_agent_name:
                await self.publish_message(
                    HandoffRequestMessage(agent_name=self._handoff_agent_name),
                    TopicId(self._internal_topic_type, self.id.key),
                )
                self._handoff_agent_name = None
                break

            if response is None:
                raise RuntimeError(
                    f'Agent "{self._agent.name}" did not return any response nor did not set a handoff agent name.'
                )

            await self.publish_message(
                HandoffResponseMessage(body=response),
                TopicId(self._internal_topic_type, self.id.key),
                cancellation_token=cts.cancellation_token,
            )

            if self._human_response_function:
                human_response = await self._call_human_response_function()
                await self.publish_message(
                    HandoffResponseMessage(body=human_response),
                    TopicId(self._internal_topic_type, self.id.key),
                    cancellation_token=cts.cancellation_token,
                )
                response = await self._invoke_agent_with_potentially_no_response(
                    additional_messages=human_response,
                    kernel=self._kernel,
                )
            else:
                await self._complete_task(
                    task_summary="No handoff agent name provided and no human response function set. Ending task."
                )
                break

    async def _call_human_response_function(self) -> ChatMessageContent:
        """Call the human response function if it is set."""
        assert self._human_response_function  # nosec B101
        if inspect.iscoroutinefunction(self._human_response_function):
            return await self._human_response_function()
        return self._human_response_function()  # type: ignore[return-value]

    async def _invoke_agent_with_potentially_no_response(
        self, additional_messages: DefaultTypeAlias | None = None, **kwargs
    ) -> ChatMessageContent | None:
        """Invoke the agent with the current chat history or thread and optionally additional messages.

        This method differs from `_invoke_agent` in that it handles the case where no response is returned
        from the agent gracefully, returning `None` instead of raising an error.

        The reason for this is that agents in a handoff group chat may not always produce a response when
        a handoff function is invoked, where the `_handoff_function_filter` will terminate the auto function
        invocation loop before a response is produced. In such cases, this method will return `None`
        instead of raising an error.
        """
        streaming_message_buffer: list[StreamingChatMessageContent] = []
        messages = self._create_messages(additional_messages)

        async for response_item in self._agent.invoke_stream(messages=messages, thread=self._agent_thread, **kwargs):  # type: ignore[arg-type]
            # Buffer message chunks and stream them with correct is_final flag.
            streaming_message_buffer.append(response_item.message)
            if len(streaming_message_buffer) > 1:
                await self._call_streaming_agent_response_callback(streaming_message_buffer[-2], is_final=False)
            if self._agent_thread is None:
                self._agent_thread = response_item.thread

        if streaming_message_buffer:
            # Call the callback for the last message chunk with is_final=True.
            await self._call_streaming_agent_response_callback(streaming_message_buffer[-1], is_final=True)

        if not streaming_message_buffer:
            return None

        # Build the full response from the streaming messages
        full_response = sum(streaming_message_buffer[1:], streaming_message_buffer[0])
        await self._call_agent_response_callback(full_response)

        return full_response


# endregion HandoffAgentActor

# region HandoffOrchestration


@experimental
class HandoffOrchestration(OrchestrationBase[TIn, TOut]):
    """An orchestration class for managing handoff agents in a group chat."""

    def __init__(
        self,
        members: list[Agent],
        handoffs: OrchestrationHandoffs,
        name: str | None = None,
        description: str | None = None,
        input_transform: Callable[[TIn], Awaitable[DefaultTypeAlias] | DefaultTypeAlias] | None = None,
        output_transform: Callable[[DefaultTypeAlias], Awaitable[TOut] | TOut] | None = None,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
        streaming_agent_response_callback: Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        | None = None,
        human_response_function: Callable[[], Awaitable[ChatMessageContent] | ChatMessageContent] | None = None,
    ) -> None:
        """Initialize the handoff orchestration.

        Args:
            members (list[Agent]): A list of agents or orchestrations that are part of the
                handoff group. This first agent in the list will be the one that receives the first message.
            handoffs (OrchestrationHandoffs): Defines the handoff connections between agents.
            name (str | None): The name of the orchestration.
            description (str | None): The description of the orchestration.
            input_transform (Callable | None): A function that transforms the external input message.
            output_transform (Callable | None): A function that transforms the internal output message.
            agent_response_callback (Callable | None): A function that is called when a full response is produced
                by the agents.
            streaming_agent_response_callback (Callable | None): A function that is called when a streaming response
                is produced by the agents.
            human_response_function (Callable | None): A function that is called when a human response is
                needed.
        """
        self._handoffs = handoffs
        self._human_response_function = human_response_function

        super().__init__(
            members=members,
            name=name,
            description=description,
            input_transform=input_transform,
            output_transform=output_transform,
            agent_response_callback=agent_response_callback,
            streaming_agent_response_callback=streaming_agent_response_callback,
        )

        self._validate_handoffs()

    @override
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the handoff pattern.

        This ensures that all initial messages are sent to the individual actors
        and processed before the group chat begins. It's important because if the
        manager actor processes its start message too quickly (or other actors are
        too slow), it might send a request to the next agent before the other actors
        have the necessary context.
        """

        async def send_start_message(agent: Agent) -> None:
            target_actor_id = await runtime.get(self._get_agent_actor_type(agent, internal_topic_type))
            await runtime.send_message(
                HandoffStartMessage(body=task),
                target_actor_id,
                cancellation_token=cancellation_token,
            )

        await asyncio.gather(*[send_start_message(agent) for agent in self._members])

        # Send the handoff request message to the first agent in the list
        target_actor_id = await runtime.get(self._get_agent_actor_type(self._members[0], internal_topic_type))
        await runtime.send_message(
            HandoffRequestMessage(agent_name=self._members[0].name),
            target_actor_id,
            cancellation_token=cancellation_token,
        )

    @override
    async def _prepare(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Register the actors and orchestrations with the runtime and add the required subscriptions."""
        await self._register_members(runtime, internal_topic_type, result_callback)
        await self._add_subscriptions(runtime, internal_topic_type)

    async def _register_members(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Register the members with the runtime."""

        async def _register_helper(agent: Agent) -> None:
            handoff_connections = self._handoffs.get(agent.name, AgentHandoffs())
            await HandoffAgentActor.register(
                runtime,
                self._get_agent_actor_type(agent, internal_topic_type),
                lambda agent=agent, handoff_connections=handoff_connections: HandoffAgentActor(  # type: ignore[misc]
                    agent,
                    internal_topic_type,
                    handoff_connections,
                    result_callback=result_callback,
                    agent_response_callback=self._agent_response_callback,
                    streaming_agent_response_callback=self._streaming_agent_response_callback,
                    human_response_function=self._human_response_function,
                ),
            )

        await asyncio.gather(*[_register_helper(member) for member in self._members])

    async def _add_subscriptions(self, runtime: CoreRuntime, internal_topic_type: str) -> None:
        """Add subscriptions to the runtime."""
        subscriptions: list[TypeSubscription] = [
            TypeSubscription(
                internal_topic_type,
                self._get_agent_actor_type(member, internal_topic_type),
            )
            for member in self._members
        ]

        await asyncio.gather(*[runtime.add_subscription(subscription) for subscription in subscriptions])

    def _get_agent_actor_type(self, agent: Agent, internal_topic_type: str) -> str:
        """Get the actor type for an agent.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{agent.name}_{internal_topic_type}"

    def _validate_handoffs(self) -> None:
        """Validate the handoffs to ensure all connections are valid."""
        if not self._handoffs:
            raise ValueError("Handoffs cannot be empty. Please provide at least one handoff connection.")

        member_names = {m.name for m in self._members}
        for agent_name, connections in self._handoffs.items():
            if agent_name not in member_names:
                raise ValueError(f"Agent {agent_name} is not a member of the handoff group.")
            for handoff_agent_name in connections:
                if handoff_agent_name not in member_names:
                    raise ValueError(f"Agent {handoff_agent_name} is not a member of the handoff group.")
                if handoff_agent_name == agent_name:
                    raise ValueError(f"Agent {agent_name} cannot handoff to itself.")


# endregion HandoffOrchestration
