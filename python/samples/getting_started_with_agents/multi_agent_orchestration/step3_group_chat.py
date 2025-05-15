# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent

"""
The following sample demonstrates how to create a group chat orchestration with a default
round robin manager for controlling the flow of conversation in a round robin fashion.

Think of the group chat manager as a state machine, with the following possible states:
- Request for user message
- Termination, after which the manager will try to filter a result from the conversation
- Continuation, at which the manager will select the next agent to speak

This sample demonstrates the basic steps of creating and starting a runtime, creating
a group chat orchestration with a group chat manager, invoking the orchestration,
and finally waiting for the results.

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


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """Main function to run the agents."""
    # 1. Create a group chat orchestration with a round robin manager
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=RoundRobinGroupChatManager(max_rounds=5),
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
    Sample output:
    **Writer**
    "Drive Tomorrow: Affordable Adventure Starts Today!"
    **Reviewer**
    This slogan, "Drive Tomorrow: Affordable Adventure Starts Today!", effectively communicates the core attributes of
    the new electric SUV being promoted: affordability, fun, and forward-thinking. Here's some feedback:

    ...

    Overall, the slogan captures the essence of an innovative, enjoyable, and accessible vehicle. Great job!
    **Writer**
    "Embrace the Future: Your Affordable Electric Adventure Awaits!"
    **Reviewer**
    This revised slogan, "Embrace the Future: Your Affordable Electric Adventure Awaits!", further enhances the message
    of the electric SUV. Here's an evaluation:

    ...

    Overall, this version of the slogan effectively communicates the vehicle's benefits while maintaining a positive
        and engaging tone. Keep up the good work!
    **Writer**
    "Feel the Charge: Adventure Meets Affordability in Your New Electric SUV!"
    ***** Result *****
    "Feel the Charge: Adventure Meets Affordability in Your New Electric SUV!"
    """


if __name__ == "__main__":
    asyncio.run(main())
