# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys

from opentelemetry import trace

from samples.demos.travel_planning_system.agents import get_agents
from samples.demos.travel_planning_system.observability import enable_observability
from semantic_kernel.agents import (
    BooleanResult,
    ChatCompletionAgent,
    GroupChatManager,
    GroupChatOrchestration,
    MessageResult,
    StringResult,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingChatMessageContent,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


# Flag to indicate if a new message is being received
is_new_message = True


def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """Observer function to print the messages from the agents.

    Args:
        message (StreamingChatMessageContent): The streaming message content from the agent.
        is_final (bool): Indicates if this is the final part of the message.
    """
    global is_new_message
    if is_new_message:
        print(f"# {message.name}")
        is_new_message = False
    print(message.content, end="", flush=True)

    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"Calling '{item.name}' with arguments '{item.arguments}'", end="", flush=True)
        if isinstance(item, FunctionResultContent):
            print(f"Result from '{item.name}' is '{item.result}'", end="", flush=True)

    if is_final:
        print()
        is_new_message = True


def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("human_in_the_loop"):
        user_input = input("User: ")
        return ChatMessageContent(role=AuthorRole.USER, content=user_input)


class AgentBaseGroupChatManager(GroupChatManager):
    """A group chat managers that uses a ChatCompletionAgent."""

    agent: ChatCompletionAgent

    def __init__(self, **kwargs):
        """Initialize the base group chat manager with a ChatCompletionAgent."""
        agent = ChatCompletionAgent(
            name="Manager",
            description="The manager of the group chat, responsible for coordinating the agents.",
            instructions=(
                "You are the manager of the group chat. "
                "Your role is to coordinate the agents and ensure they satisfy the user's request. "
            ),
            service=AzureChatCompletion(),
        )

        super().__init__(agent=agent, **kwargs)

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Determine if the manager should request user input based on the chat history."""
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )

        last_message = chat_history.messages[-1]
        if last_message.role == AuthorRole.USER:
            return BooleanResult(
                result=False,
                reason="User input is not needed if the last message is from the user.",
            )

        messages = chat_history.messages[:]
        messages.append(ChatMessageContent(role=AuthorRole.USER, content="Does the group need further user input?"))

        settings = AzureChatPromptExecutionSettings()
        settings.response_format = BooleanResult

        response = await self.agent.get_response(messages, arguments=KernelArguments(settings=settings))
        return BooleanResult.model_validate_json(response.message.content)

    @override
    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Provide concrete implementation for should_terminate."""
        should_terminate = await super().should_terminate(chat_history)
        if should_terminate.result:
            return should_terminate

        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )

        messages = chat_history.messages[:]
        messages.append(
            ChatMessageContent(
                role=AuthorRole.USER,
                content="Has the user's request been satisfied?",
            )
        )

        settings = AzureChatPromptExecutionSettings()
        settings.response_format = BooleanResult

        response = await self.agent.get_response(messages, arguments=KernelArguments(settings=settings))
        return BooleanResult.model_validate_json(response.message.content)

    @override
    async def select_next_agent(
        self,
        chat_history: ChatHistory,
        participant_descriptions: dict[str, str],
    ) -> StringResult:
        """Provide concrete implementation for selecting the next agent to speak."""
        messages = chat_history.messages[:]
        messages.append(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=(
                    "Who should speak next based on the conversation? Pick one agent from the participants:\n"
                    + "\n".join([f"{k}: {v}" for k, v in participant_descriptions.items()])
                    + "\nPlease provide the agent's name."
                ),
            )
        )

        settings = AzureChatPromptExecutionSettings()
        settings.response_format = StringResult

        response = await self.agent.get_response(messages, arguments=KernelArguments(settings=settings))
        result = StringResult.model_validate_json(response.message.content)

        if result.result not in participant_descriptions:
            raise ValueError(
                f"Selected agent '{result.result}' is not in the list of participants: "
                f"{list(participant_descriptions.keys())}"
            )

        return result

    @override
    async def filter_results(
        self,
        chat_history: ChatHistory,
    ) -> MessageResult:
        """Provide concrete implementation for filtering results."""
        messages = chat_history.messages[:]
        messages.append(ChatMessageContent(role=AuthorRole.USER, content="Please summarize the conversation."))

        settings = AzureChatPromptExecutionSettings()
        settings.response_format = StringResult

        response = await self.agent.get_response(messages, arguments=KernelArguments(settings=settings))
        string_with_reason = StringResult.model_validate_json(response.message.content)

        return MessageResult(
            result=ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=string_with_reason.result,
            ),
            reason=string_with_reason.reason,
        )


@enable_observability
async def main():
    """Main function to run the agents."""
    # 1. Create a Group Chat orchestration with multiple agents
    agents: dict[str, ChatCompletionAgent] = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=[
            agents["planner"],
            agents["flight_agent"],
            agents["hotel_agent"],
        ],
        manager=AgentBaseGroupChatManager(max_rounds=20, human_response_function=human_response_function),
        streaming_agent_response_callback=streaming_agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await group_chat_orchestration.invoke(
        task=(
            "Plan a trip to bali for 5 days including flights, hotels, and "
            "activities for a vegetarian family of 4 members. The family lives in Seattle, WA, USA. "
            "Their vacation starts on July 30th 2025. their have a strict budget of $5000 for the trip. "
            "Please provide a detailed plan and make the necessary hotel and flight bookings."
        ),
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(value)

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
