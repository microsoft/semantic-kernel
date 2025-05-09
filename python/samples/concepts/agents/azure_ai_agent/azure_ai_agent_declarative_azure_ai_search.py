# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.agent import AgentRegistry
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the Bing Grounding tool.

The agent is created using a YAML declarative spec that configures the
Bing Grounding tool. The agent is then used to answer user questions
that require web search to answer correctly.

Note: the `BingConnectionId` is in the format of:
/subscriptions/<sub_id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<workspace>/connections/<bing_connection_id>

It can either be configured as an env var `AZURE_AI_AGENT_BING_CONNECTION_ID` or passed in as an extra to 
`create_from_yaml`: extras={"BingConnectionId": "<bing_connection_id>"}
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

settings = AzureAIAgentSettings()  # ChatModelId & BingConnectionId come from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=spec,
                client=client,
                settings=settings,
                extras={
                    "AzureAISearchConnectionId": "/subscriptions/5b742c40-bc2b-4a4f-902f-ee9f644d8844/resourceGroups/sk-integration-test-infra/providers/Microsoft.MachineLearningServices/workspaces/ai-proj-sk-integration-test/connections/AzureAISearch",
                    "AzureAISearchIndexName": "skglossary",
                },
            )

            # Define the task for the agent
            TASK = "What is Semantic Kernel?"

            print(f"# User: '{TASK}'")

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
            # Cleanup: Delete the thread and agent
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
