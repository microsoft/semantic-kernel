# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from typing import ClassVar

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import BooleanResult, MessageResult, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

"""
The following sample demonstrates how to create a group chat orchestration with human
in the loop. Human in the loop is achieved by overriding the default round robin manager
to allow user input after the reviewer agent's message.

Think of the group chat manager as a state machine, with the following possible states:
- Request for user message
- Termination, after which the manager will try to filter a result from the conversation
- Continuation, at which the manager will select the next agent to speak

This sample demonstrates the basic steps of customizing the group chat manager to enter
the user input state, creating a human response function to get user input, and providing
it to the group chat manager.

There are two agents in this orchestration: a writer and a reviewer. They work iteratively
to refine a slogan for a new electric SUV.
"""


def get_agents() -> list[Agent]:
    """Return a list of agents that will participate in the group style discussion.

    Feel free to add or remove agents.
    """
    writer = ChatCompletionAgent(
        name="Writer",
        description="A content writer.",
        instructions=(
            "You are an excellent content writer. "
            "You create new content and edit contents based on the feedback from the reviewer and user."
        ),
        service=AzureChatCompletion(),
    )
    reviewer = ChatCompletionAgent(
        name="Reviewer",
        description="A content reviewer.",
        instructions=(
            "You are an excellent content reviewer. "
            "You review the content and provide feedback. "
            "Do not respond to the user directly, but provide feedback to the writer."
        ),
        service=AzureChatCompletion(),
    )

    # The order of the agents in the list will be the order in which they will be picked by the round robin manager
    return [writer, reviewer]


class HumanInTheLoopGroupChatManager(RoundRobinGroupChatManager):
    """Custom round robin group chat manager to enable user input."""

    APPROVE_MESSAGE: ClassVar[str] = "approve"

    @override
    async def filter_results(self, chat_history) -> MessageResult:
        """Override the default behavior to return the result of the group chat.

        The result of the group chat in this case is the last message from the writer agent.
        """
        if not chat_history.messages:
            raise RuntimeError("Chat history is empty, cannot filter results.")

        # Find the last message that is from the writer agent
        for message in reversed(chat_history.messages):
            if message.name == "Writer":
                return MessageResult(
                    result=message,
                    reason="Returning the last message from the writer agent.",
                )

        raise RuntimeError("No message from the writer agent found in chat history.")

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the writer's message.

        The manager will check if input from human is needed after each agent message.
        """
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )
        last_message = chat_history.messages[-1]
        if last_message.name == "Writer":
            return BooleanResult(
                result=True,
                reason="User input is needed after the writer's message.",
            )

        return BooleanResult(
            result=False,
            reason="User input is not needed if the last message is not from the Writer.",
        )

    @override
    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to terminate the chat.

        The manager will check if the chat should be terminated after each agent message.
        """
        result = await super().should_terminate(chat_history)
        if result.result:
            return result

        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet, cannot terminate.",
            )

        last_message = chat_history.messages[-1]
        if last_message.role == AuthorRole.USER and last_message.content.lower() == self.APPROVE_MESSAGE:
            return BooleanResult(
                result=True,
                reason="User has approved the content.",
            )

        return BooleanResult(
            result=False,
            reason="Chat should not be terminated yet since user has not approved the content.",
        )


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Function to get user input."""
    user_input = input(f"User (Enter '{HumanInTheLoopGroupChatManager.APPROVE_MESSAGE}' to approve the content): ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """Main function to run the agents."""
    # 1. Create a group chat orchestration with a round robin manager
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=HumanInTheLoopGroupChatManager(
            max_rounds=5,
            human_response_function=human_response_function,
        ),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await group_chat_orchestration.invoke(
        task="Create a slogan for a new electric SUV that is affordable and fun to drive.",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(f"***** Result *****\n{value}")

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

    """
    **Writer**
    "Electrify Your Adventure: Affordable Fun Awaits!"
    User (Enter 'approve' to approve the content): I'd like to make it rhyme
    **Reviewer**
    Consider revising the slogan to incorporate rhyme while maintaining clarity and impact.
    Here’s a suggestion: "Drive with a Smile, Save for a While!" This emphasizes the affordability
    and enjoyment of the electric SUV. Additionally, ensure that the slogan aligns with the brand’s
    voice and resonates with your target audience for maximum engagement.
    **Writer**
    "Charge Up the Fun, Drive On the Run!"
    User (Enter 'approve' to approve the content): approve
    ***** Result *****
    "Charge Up the Fun, Drive On the Run!"
    """


if __name__ == "__main__":
    asyncio.run(main())
