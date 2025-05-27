# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import AgentRegistry, AzureAssistantAgent

"""
The following sample demonstrates how to create an Azure Assistant Agent that answers
user questions using the code interpreter tool.

The agent is then used to answer user questions that require code to be generated and 
executed. The responses are handled in a streaming manner.
"""

# Define the YAML string for the sample
spec = """
type: azure_assistant
name: CodeInterpreterAgent
description: Agent with code interpreter tool.
instructions: >
  Use the code interpreter tool to answer questions that require code to be generated
  and executed.
model:
  id: ${AzureOpenAI:ChatModelId}
  connection:
    api_key: ${AzureOpenAI:ApiKey}
tools:
  - type: code_interpreter
    options:
      file_ids:
        - ${AzureOpenAI:FileId1}
"""


async def main():
    client = AzureAssistantAgent.create_client()

    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "agent_assistant_file_manipulation",
        "sales.csv",
    )

    # Load the employees PDF file as a FileObject
    with open(csv_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    try:
        # Create the Assistant Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `AzureOpenAI:` prefix).
        # The short-format is used here for brevity
        agent: AzureAssistantAgent = await AgentRegistry.create_from_yaml(
            yaml_str=spec,
            client=client,
            extras={"AzureOpenAI:FileId1": file.id},
        )

        # Define the task for the agent
        TASK = "Give me the code to calculate the total sales for all segments."

        print(f"# User: '{TASK}'")

        # Invoke the agent for the specified task
        is_code = False
        last_role = None
        async for response in agent.invoke_stream(
            messages=TASK,
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
        if is_code:
            print("```\n")
        print()
    finally:
        # Cleanup: Delete the thread and agent
        await client.beta.assistants.delete(agent.id)
        await client.files.delete(file.id)

        """
        Sample output:

        # User: 'Give me the code to calculate the total sales for all segments.'

        # AuthorRole.ASSISTANT: Let me first examine the contents of the uploaded file to determine its structure. This 
            will allow me to create the appropriate code for calculating the total sales for all segments. Hang tight!

        ```python
        import pandas as pd

        # Load the uploaded file to examine its contents
        file_path = '/mnt/data/assistant-3nXizu2EX2EwXikUz71uNc'
        data = pd.read_csv(file_path)

        # Display the first few rows and column names to understand the structure of the dataset
        data.head(), data.columns
        ```

        # AuthorRole.ASSISTANT: The dataset contains several columns, including `Segment`, `Sales`, and others such as 
            `Country`, `Product`, and date-related information. To calculate the total sales for all segments, we will:

        1. Group the data by the `Segment` column.
        2. Sum the `Sales` column for each segment.
        3. Calculate the grand total of all sales across all segments.

        Here is the code snippet for this task:

        ```python
        # Group by 'Segment' and sum up 'Sales'
        segment_sales = data.groupby('Segment')['Sales'].sum()

        # Calculate the total sales across all segments
        total_sales = segment_sales.sum()

        print("Total Sales per Segment:")
        print(segment_sales)
        print(f"\nGrand Total Sales: {total_sales}")
        ```

        Would you like me to execute this directly for the uploaded data?
        """


if __name__ == "__main__":
    asyncio.run(main())
