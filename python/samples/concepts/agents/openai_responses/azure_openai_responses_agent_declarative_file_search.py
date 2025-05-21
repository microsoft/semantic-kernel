# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import AzureAssistantAgent
from semantic_kernel.agents.agent import AgentRegistry

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the file search tool.

The agent is used to answer user questions that require file search to help ground 
answers from the model.
"""

# Define the YAML string for the sample
spec = """
type: azure_openai_responses_agent
name: FileSearchAgent
description: Agent with code interpreter tool.
instructions: >
  Use the code interpreter tool to answer questions that require code to be generated
  and executed.
model:
  id: ${AzureOpenAI:ChatModelId}
  connection:
    endpoint: ${AzureOpenAI:Endpoint}
tools:
  - type: file_search
    options:
      vector_store_ids:
        - ${AzureOpenAI:VectorStoreId}
"""


async def main():
    # Setup the OpenAI Assistant client
    client = AzureAssistantAgent.create_client()

    # Read and upload the file to the OpenAI AI service
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "file_search",
        "employees.pdf",
    )
    # Upload the pdf file to the assistant service
    with open(pdf_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    vector_store = await client.vector_stores.create(
        name="assistant_file_search",
        file_ids=[file.id],
    )

    try:
        # Create the AzureAI Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `AzureAI:` prefix).
        # The short-format is used here for brevity
        agent: AzureAssistantAgent = await AgentRegistry.create_from_yaml(
            yaml_str=spec,
            client=client,
            extras={"OpenAI:VectorStoreId": vector_store.id},
        )

        # Define the task for the agent
        TASK = "Who can help me if I have a sales question?"

        print(f"# User: '{TASK}'")

        # Invoke the agent for the specified task
        async for response in agent.invoke(
            messages=TASK,
        ):
            print(f"# {response.name}: {response}")
    finally:
        # Cleanup: Delete the agent, vector store, and file
        await client.beta.assistants.delete(agent.id)
        await client.vector_stores.delete(vector_store.id)
        await client.files.delete(file.id)

        """
        Sample output:

        # User: 'Who can help me if I have a sales question?'
        # FileSearchAgent: If you have a sales question, you may contact the following individuals:

        1. **Hicran Bea** - Sales Manager
        2. **Mariam Jaslyn** - Sales Representative
        3. **Angelino Embla** - Sales Representative

        This information comes from the employee records【4:0†source】.
        """


if __name__ == "__main__":
    asyncio.run(main())
