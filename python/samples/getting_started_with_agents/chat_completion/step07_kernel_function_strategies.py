# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import KernelFunctionSelectionStrategy, KernelFunctionTerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelFunctionFromPrompt

"""
The following sample demonstrates how to create a simple, agent group chat that utilizes
An Art Director Chat Completion Agent along with a Copy Writer Chat Completion Agent to
complete a task. The sample also shows how to specify a Kernel Function termination and
selection strategy to determine when to end the chat or how to select the next agent to
take a turn in the conversation.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""

TASK = "a slogan for a new line of electric cars."


async def main():
    # 1. Create the reviewer agent based on the chat completion service
    agent_reviewer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("artdirector"),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    # 2. Create the copywriter agent based on the chat completion service
    agent_writer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("copywriter"),
        name=COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
    )

    # 3. Create a Kernel Function to determine if the copy has been approved
    termination_function = KernelFunctionFromPrompt(
        function_name="termination",
        prompt="""
        Determine if the copy has been approved.  If so, respond with a single word: yes

        History:
        {{$history}}
        """,
    )

    # 4. Create a Kernel Function to determine which agent should take the next turn
    selection_function = KernelFunctionFromPrompt(
        function_name="selection",
        prompt=f"""
        Determine which participant takes the next turn in a conversation based on the the most recent participant.
        State only the name of the participant to take the next turn.
        No participant should take more than one turn in a row.
        
        Choose only from these participants:
        - {REVIEWER_NAME}
        - {COPYWRITER_NAME}
        
        Always follow these rules when selecting the next participant:
        - After user input, it is {COPYWRITER_NAME}'s turn.
        - After {COPYWRITER_NAME} replies, it is {REVIEWER_NAME}'s turn.
        - After {REVIEWER_NAME} provides feedback, it is {COPYWRITER_NAME}'s turn.

        History:
        {{{{$history}}}}
        """,
    )

    # 5. Place the agents in a group chat with the custom termination and selection strategies
    chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=KernelFunctionTerminationStrategy(
            agents=[agent_reviewer],
            function=termination_function,
            kernel=_create_kernel_with_chat_completion("termination"),
            result_parser=lambda result: str(result.value[0]).lower() == "yes",
            history_variable_name="history",
            maximum_iterations=10,
        ),
        selection_strategy=KernelFunctionSelectionStrategy(
            function=selection_function,
            kernel=_create_kernel_with_chat_completion("selection"),
            result_parser=lambda result: str(result.value[0]) if result.value is not None else COPYWRITER_NAME,
            agent_variable_name="agents",
            history_variable_name="history",
        ),
    )

    # 6. Add the task as a message to the group chat
    await chat.add_chat_message(message=TASK)
    print(f"# User: {TASK}")

    # 7. Invoke the chat
    async for content in chat.invoke():
        print(f"# {content.name}: {content.content}")

    """
    Sample Output:
    # User: a slogan for a new line of electric cars.
    # CopyWriter: "Electrify your drive. Spare the gas, not the thrill."
    # ArtDirector: This slogan captures the essence of electric cars but could use refinement to ...
    # CopyWriter: "Go electric. Enjoy the thrill. Skip the gas."
    # ArtDirector: Approved. This slogan is clear, concise, and effectively communicates the ...
    """


if __name__ == "__main__":
    asyncio.run(main())
