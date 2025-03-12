# Copyright (c) Microsoft. All rights reserved.

import asyncio

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

from semantic_kernel.agents.autogen.autogen_conversable_agent import AutoGenConversableAgent

"""
The following sample demonstrates how to use the AutoGenConversableAgent to create a reply from an agent
to a message with a code block. The agent executes the code block and replies with the output.

The sample follows the AutoGen flow outlined here:
https://microsoft.github.io/autogen/0.2/docs/tutorial/code-executors#local-execution
"""


async def main():
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
import numpy as np
import matplotlib.pyplot as plt
x = np.random.randint(0, 100, 100)
y = np.random.randint(0, 100, 100)
plt.scatter(x, y)
plt.savefig('scatter.png')
print('Scatter plot saved to scatter.png')
```
This is the end of the message.
"""

    async for content in autogen_agent.invoke(message=message_with_code_block):
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")


if __name__ == "__main__":
    asyncio.run(main())
