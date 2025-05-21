# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.agents.models import CodeInterpreterTool, FilePurpose
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a simple, Azure AI agent that
uses the code interpreter tool to answer a coding question.
"""

TASK = "What's the total sum of all sales for all segments using Python?"


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent with a code interpreter on the Azure AI agent service
        csv_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "sales.csv"
        )

        # 2. Upload the CSV file to the Azure AI agent service
        file = await client.agents.files.upload_and_poll(file_path=csv_file_path, purpose=FilePurpose.AGENTS)

        # 3. Create a code interpreter tool referencing the uploaded file
        code_interpreter = CodeInterpreterTool(file_ids=[file.id])
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # 4. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 6. Invoke the agent for the specified thread for response
            async for response in agent.invoke(messages=TASK, thread=thread):
                if response.role != AuthorRole.TOOL:
                    print(f"# Agent: {response}")
                thread = response.thread
        finally:
            # 7. Cleanup: Delete the thread, agent, and file
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
            await client.agents.files.delete(file.id)

        """
        Sample Output:
        # User: 'Give me the code to calculate the total sales for all segments.'

        # AuthorRole.ASSISTANT: Let me first load the uploaded file to understand its contents before providing 
        tailored code.

        ```python
        import pandas as pd

        # Load the uploaded file
        file_path = '/mnt/data/assistant-GBaUAF6AKds3sfdfSpxJZG'
        data = pd.read_excel(file_path) # Attempting to load as an Excel file initially

        # Display the first few rows and understand its structure
        data.head(), data.info()
        ```

        # AuthorRole.ASSISTANT: The file format couldn't be automatically determined. Let me attempt to load it as a 
        CSV or other type.

        ```python
        # Attempt to load the file as a CSV
        data = pd.read_csv(file_path)

        # Display the first few rows of the dataset and its information
        data.head(), data.info()
        ```

        # AuthorRole.ASSISTANT: <class 'pandas.core.frame.DataFrame'>
        RangeIndex: 700 entries, 0 to 699
        Data columns (total 14 columns):
        #   Column        Non-Null Count  Dtype  
        ---  ------        --------------  -----  
        0   Segment       700 non-null    object 
        1   Country       700 non-null    object 
        2   Product       700 non-null    object 
        3   Units Sold    700 non-null    float64
        4   Sale Price    700 non-null    float64
        5   Gross Sales   700 non-null    float64
        6   Discounts     700 non-null    float64
        7   Sales         700 non-null    float64
        8   COGS          700 non-null    float64
        9   Profit        700 non-null    float64
        10  Date          700 non-null    object 
        11  Month Number  700 non-null    int64  
        12  Month Name    700 non-null    object 
        13  Year          700 non-null    int64  
        dtypes: float64(7), int64(2), object(5)
        memory usage: 76.7+ KB
        The dataset has been successfully loaded and contains information regarding sales, profits, and related metrics 
        for various segments. To calculate the total sales across all segments, we can use the "Sales" column.

        Here's the code to calculate the total sales:

        ```python
        # Calculate the total sales for all segments
        total_sales = data['Sales'].sum()

        total_sales
        ```

        # AuthorRole.ASSISTANT: The total sales for all segments amount to approximately **118,726,350.29**. Let me 
        know if you need additional analysis or code for manipulating this data!
        """


if __name__ == "__main__":
    asyncio.run(main())
