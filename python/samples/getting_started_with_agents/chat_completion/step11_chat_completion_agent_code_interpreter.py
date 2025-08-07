# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.core_plugins import SessionsPythonTool

"""
The following sample demonstrates how to create a chat completion agent with
code interpreter capabilities using the Azure Container Apps session pool service.
"""


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"# Function Result:> {item.result}")
        elif isinstance(item, FunctionCallContent):
            print(f"# Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"# {message.name}: {message} ")


async def main():
    # 1. Create the python code interpreter tool using the SessionsPythonTool
    python_code_interpreter = SessionsPythonTool()

    # 2. Create the agent
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Host",
        instructions="Answer questions about the menu.",
        plugins=[python_code_interpreter],
    )

    # 3. Upload a CSV file to the session
    csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "sales.csv")
    file_metadata = await python_code_interpreter.upload_file(local_file_path=csv_file_path)

    # 4. Invoke the agent for a response to a task
    TASK = (
        "What's the total sum of all sales for all segments using Python? "
        f"Use the uploaded file {file_metadata.full_path} for reference."
    )
    print(f"# User: '{TASK}'")
    async for response in agent.invoke(
        messages=TASK,
        on_intermediate_message=handle_intermediate_steps,
    ):
        print(f"# {response.name}: {response} ")

    """
    Sample output:
    # User: 'What's the total sum of all sales for all segments using Python?
        Use the uploaded file /mnt/data/sales.csv for reference.'
    # Function Call:> SessionsPythonTool-execute_code with arguments: {
        "code": "
            import pandas as pd

            # Load the sales data
            file_path = '/mnt/data/sales.csv'
            sales_data = pd.read_csv(file_path)
             
            # Calculate the total sum of sales
            # Assuming there's a column named 'Sales' which contains the sales amounts
            total_sales = sales_data['Sales'].sum()
            total_sales"
        }
    # Function Result:> Status:
    Success
    Result:
    118726350.28999999
    Stdout:

    Stderr:
    # Host: The total sum of all sales for all segments is approximately $118,726,350.29.
    """


if __name__ == "__main__":
    asyncio.run(main())
