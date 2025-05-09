# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.projects.models import OpenAIFile, VectorStore
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.agent import AgentRegistry

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the code interpreter tool.

The agent is created using a YAML declarative spec that configures the
code interpreter tool. The agent is then used to answer user questions
that require code to be generated and executed. The responses are handled
in a streaming manner.
"""

# Define the YAML string for the sample
spec = """
type: foundry_agent
name: FileSearchAgent
description: Agent with code interpreter tool.
instructions: >
  Use the code interpreter tool to answer questions that require code to be generated
  and executed.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
tools:
  - type: file_search
    options:
      vector_store_ids:
        - ${AzureAI:VectorStoreId}
"""

settings = AzureAIAgentSettings()  # ChatModelId & ConnectionString come from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # Read and upload the file to the Azure AI agent service
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
            "resources",
            "file_search",
            "employees.pdf",
        )
        # Upload the pdf file to the agent service
        file: OpenAIFile = await client.agents.upload_file_and_poll(file_path=pdf_file_path, purpose="assistants")
        vector_store: VectorStore = await client.agents.create_vector_store_and_poll(
            file_ids=[file.id], name="my_vectorstore"
        )

        try:
            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=spec,
                client=client,
                settings=settings,
                extras={"VectorStoreId": vector_store.id},
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
            await client.agents.delete_agent(agent.id)
            await client.agents.delete_vector_store(vector_store.id)
            await client.agents.delete_file(file.id)

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
