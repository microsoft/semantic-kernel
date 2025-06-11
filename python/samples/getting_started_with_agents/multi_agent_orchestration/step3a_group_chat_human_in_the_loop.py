# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import BooleanResult, RoundRobinGroupChatManager
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
            "You are an excellent content writer. You create new content and edit contents based on the feedback."
        ),
        service=AzureChatCompletion(),
    )
    reviewer = ChatCompletionAgent(
        name="Reviewer",
        description="A content reviewer.",
        instructions=(
            "You are an excellent content reviewer. You review the content and provide feedback to the writer."
        ),
        service=AzureChatCompletion(),
    )

    # The order of the agents in the list will be the order in which they will be picked by the round robin manager
    return [writer, reviewer]


class CustomRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    """Custom round robin group chat manager to enable user input."""

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the reviewer's message.

        The manager will check if input from human is needed after each agent message.
        """
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )
        last_message = chat_history.messages[-1]
        if last_message.name == "Reviewer":
            return BooleanResult(
                result=True,
                reason="User input is needed after the reviewer's message.",
            )

        return BooleanResult(
            result=False,
            reason="User input is not needed if the last message is not from the reviewer.",
        )


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Function to get user input."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """Main function to run the agents."""
    # 1. Create a group chat orchestration with a round robin manager
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=CustomRoundRobinGroupChatManager(
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
    "Electrify Your Journey: Affordable Adventure Awaits!"
    **Reviewer**
    Your slogan captures the essence of being both affordable and fun, which is great! However, you might want to ...
    User: I'd like to also make it rhyme
    **Writer**
    Sure! Here are a few rhyming slogan options for your electric SUV:

    1. "Zoom Through the Streets, Feel the Beats!"
    2. "Charge and Drive, Feel the Jive!"
    3. "Electrify Your Ride, Let Fun Be Your Guide!"
    4. "Zoom in Style, Drive with a Smile!"

    Let me know if you'd like more options or variations!
    **Reviewer**
    These rhyming slogans are creative and energetic! They effectively capture the fun aspect while promoting ...
    User: Please continue with the reviewer's suggestions
    **Writer**
    Absolutely! Let's refine and expand on the reviewer's suggestions for a more polished and appealing set of rhym...
    ***** Result *****
    Absolutely! Let's refine and expand on the reviewer's suggestions for a more polished and appealing set of rhym...
    """


if __name__ == "__main__":
    asyncio.run(main())
