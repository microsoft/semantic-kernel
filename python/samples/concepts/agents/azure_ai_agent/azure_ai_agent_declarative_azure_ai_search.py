# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the Azure AI Search tool.

The agent is created using a YAML declarative spec that configures the
Azure AI Search tool. The agent is then used to answer user questions
that required grounding context from the Azure AI Search index.

Note: the `AzureAISearchConnectionId` is in the format of:
/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<workspace>/connections/AzureAISearch

It can either be configured as an env var `AZURE_AI_AGENT_BING_CONNECTION_ID` or passed in as an extra to 
`create_from_yaml`: extras={
    "AzureAISearchConnectionId": "<azure_ai_search_connection_id>",
    "AzureAISearchIndexName": "<azure_ai_search_index_name>"
}
"""

# Define the YAML string for the sample
spec = """
type: foundry_agent
name: AzureAISearchAgent
instructions: Answer questions using your index to provide grounding context.
description: This agent answers questions using AI Search to provide grounding context.
model:
  id: ${AzureAI:ChatModelId}
  options:
    temperature: 0.4
tools:
  - type: azure_ai_search
    options:
      tool_connections:
        - ${AzureAI:AzureAISearchConnectionId}
      index_name: ${AzureAI:AzureAISearchIndexName}
"""

settings = AzureAIAgentSettings()  # ChatModelId comes from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Create the AzureAI Agent from the YAML spec
            # Note: the extras can be provided in the short-format (shown below) or
            # in the long-format (as shown in the YAML spec, with the `AzureAI:` prefix).
            # The short-format is used here for brevity
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=spec,
                client=client,
                settings=settings,
                extras={
                    "AzureAISearchConnectionId": "<azure-ai-search-connection-id>",
                    "AzureAISearchIndexName": "<azure-ai-search-index-name>",
                },
            )

            # Define the task for the agent
            TASK = "What is Semantic Kernel?"

            print(f"# User: '{TASK}'")

            # Define a callback function to handle intermediate messages
            async def on_intermediate_message(message: ChatMessageContent):
                if message.items:
                    for item in message.items:
                        if isinstance(item, FunctionCallContent):
                            print(f"# FunctionCallContent: arguments={item.arguments}")
                        elif isinstance(item, FunctionResultContent):
                            print(f"# FunctionResultContent: result={item.result}")

            # Invoke the agent for the specified task
            async for response in agent.invoke(messages=TASK, on_intermediate_message=on_intermediate_message):
                print(f"# {response.name}: {response}")
        finally:
            # Cleanup: Delete the  agent
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
