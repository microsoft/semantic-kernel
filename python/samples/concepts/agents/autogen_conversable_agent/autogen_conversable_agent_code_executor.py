# Copyright (c) Microsoft. All rights reserved.

import asyncio

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

from semantic_kernel.agents import AutoGenConversableAgent, AutoGenConversableAgentThread

"""
The following sample demonstrates how to use the AutoGenConversableAgent to create a reply from an agent
to a message with a code block. The agent executes the code block and replies with the output.

The sample follows the AutoGen flow outlined here:
https://microsoft.github.io/autogen/0.2/docs/tutorial/code-executors#local-execution
"""


async def main():
    thread: AutoGenConversableAgentThread = None

    # Create a temporary directory to store the code files.
    import os

    # Configure the temporary directory to be where the script is located.
    temp_dir = os.path.dirname(os.path.realpath(__file__))

    # Create a local command line code executor.
    executor = LocalCommandLineCodeExecutor(
        timeout=10,  # Timeout for each code execution in seconds.
        work_dir=temp_dir,  # Use the temporary directory to store the code files.
    )

    # Create an agent with code executor configuration.
    code_executor_agent = ConversableAgent(
        "code_executor_agent",
        llm_config=False,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the local command line code executor.
        human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
    )

    autogen_agent = AutoGenConversableAgent(conversable_agent=code_executor_agent)

    message_with_code_block = """This is a message with code block.
The code block is below:
```python
def generate_fibonacci(max_val):
    a, b = 0, 1
    fibonacci_numbers = []
    while a <= max_val:
        fibonacci_numbers.append(a)
        a, b = b, a + b
    return fibonacci_numbers

if __name__ == "__main__":
    fib_numbers = generate_fibonacci(101)
    print(fib_numbers)
```
This is the end of the message.
"""

    async for response in autogen_agent.invoke(messages=message_with_code_block, thread=thread):
        print(f"# {response.role} - {response.name or '*'}: '{response}'")
        thread = response.thread

    # Cleanup: Delete the thread and agent
    await thread.delete() if thread else None


if __name__ == "__main__":
    asyncio.run(main())
