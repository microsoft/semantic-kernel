# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import AgentRegistry, OpenAIResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent that answers
user questions using the file search tool based on a declarative spec.
"""

# Define the YAML string for the sample
spec = """
type: openai_responses
name: FileSearchAgent
description: Agent with file search tool.
instructions: >
  Find answers to the user's questions in the provided file.
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
tools:
  - type: file_search
    description: File search for document retrieval.
    options:
      vector_store_ids:
        - ${OpenAI:VectorStoreId}
"""


async def main():
    # Setup the OpenAI Responses client
    client = OpenAIResponsesAgent.create_client()

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
        # Create the Responses Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `OpenAI:` prefix).
        # The short-format is used here for brevity
        agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(
            yaml_str=spec,
            client=client,
            extras={"OpenAI:VectorStoreId": vector_store.id},
        )

        # Define the task for the agent
        USER_INPUTS = ["Who can help me if I have a sales question?", "Who works in sales?"]

        thread = None

        for user_input in USER_INPUTS:
            # Print the user input
            print(f"# User: '{user_input}'")

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=user_input,
                thread=thread,
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread
    finally:
        # Cleanup: Delete the vector store, and file
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
