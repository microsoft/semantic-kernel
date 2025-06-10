# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import AgentRegistry, OpenAIAssistantAgent

"""
The following sample demonstrates how to create an OpenAI Assistant Agent that answers
user questions using the file search tool.

The agent is used to answer user questions that require file search to help ground 
answers from the model.
"""

# Define the YAML string for the sample
spec = """
type: openai_assistant
name: FileSearchAgent
description: Agent with code interpreter tool.
instructions: >
  Use the code interpreter tool to answer questions that require code to be generated
  and executed.
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
tools:
  - type: file_search
    options:
      vector_store_ids:
        - ${OpenAI:VectorStoreId}
"""


async def main():
    # Setup the OpenAI Assistant client
    client = OpenAIAssistantAgent.create_client()

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
        # Create the Assistant Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `OpenAI:` prefix).
        # The short-format is used here for brevity
        agent: OpenAIAssistantAgent = await AgentRegistry.create_from_yaml(
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
        # FileSearchAgent: If you have a sales question, you can contact either Mariam Jaslyn or Angelino Embla, who 
          are both listed as Sales Representatives. Alternatively, you may also reach out to Hicran Bea,
          the Sales Manager【4:0†employees.pdf】.
        """


if __name__ == "__main__":
    asyncio.run(main())
