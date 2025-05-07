# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce

from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent

"""
The following sample demonstrates how to create an Azure AI agent that
uses the code interpreter tool and returns streaming responses to answer a coding question.
Additionally, the `on_intermediate_message` callback is used to handle intermediate messages
from the agent.
"""

TASK = "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101."

intermediate_steps: list[ChatMessageContent] = []


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent with a code interpreter on the Azure AI agent service
        code_interpreter = CodeInterpreterTool()
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 4. Invoke the agent for the specified thread for response
            is_code = False
            last_role = None
            async for response in agent.invoke_stream(
                messages=TASK, thread=thread, on_intermediate_message=handle_streaming_intermediate_steps
            ):
                current_is_code = response.metadata.get("code", False)

                if current_is_code:
                    if not is_code:
                        print("\n\n```python")
                        is_code = True
                    print(response.content, end="", flush=True)
                else:
                    if is_code:
                        print("\n```")
                        is_code = False
                        last_role = None
                    if hasattr(response, "role") and response.role is not None and last_role != response.role:
                        print(f"\n# {response.role}: ", end="", flush=True)
                        last_role = response.role
                    print(response.content, end="", flush=True)
                thread = response.thread
            if is_code:
                print("```\n")
            print()
        finally:
            # 6. Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        print("====================================================")
        print("\nResponse complete:\n")
        # Combine the intermediate `StreamingChatMessageContent` chunks into a single message
        filtered_steps = [step for step in intermediate_steps if isinstance(step, StreamingChatMessageContent)]
        streaming_full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, filtered_steps)
        # Grab the other messages that are not `StreamingChatMessageContent`
        other_steps = [s for s in intermediate_steps if not isinstance(s, StreamingChatMessageContent)]
        final_msgs = [streaming_full_completion] + other_steps
        for msg in final_msgs:
            print(f"{msg.content}")

        r"""
        Sample Output:
        # User: 'Use code to determine the values in the Fibonacci sequence that that are less then the value of 101.'

        ```python
        def fibonacci_sequence(limit):
            fib_sequence = []
            a, b = 0, 1
            while a < limit:
                fib_sequence.append(a)
                a, b = b, a + b
            return fib_sequence

        # Get Fibonacci sequence values less than 101
        fibonacci_values = fibonacci_sequence(101)
        fibonacci_values
        ```

        # AuthorRole.ASSISTANT: The values in the Fibonacci sequence that are less than 101 are:

        \[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89\]
        ====================================================

        Response complete:

        def fibonacci_sequence(limit):
            fib_sequence = []
            a, b = 0, 1
            while a < limit:
                fib_sequence.append(a)
                a, b = b, a + b
            return fib_sequence

        # Get Fibonacci sequence values less than 101
        fibonacci_values = fibonacci_sequence(101)
        fibonacci_values
        The values in the Fibonacci sequence that are less than 101 are:

        \[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89\]
        """


if __name__ == "__main__":
    asyncio.run(main())
