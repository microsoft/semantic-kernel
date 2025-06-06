# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    AnnotationContent,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)

"""
The following sample demonstrates how to create an Azure AI agent that
uses the Bing grounding tool to answer a user's question.

Note: Please visit the following link to learn more about the Bing grounding tool:

https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding?tabs=python&pivots=overview
"""

TASK = "Which team won the 2025 NCAA basketball championship?"


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Enter your Bing Grounding Connection Name
        bing_connection = await client.connections.get(name="<your-bing-grounding-connection-name>")
        conn_id = bing_connection.id

        # 2. Initialize agent bing tool and add the connection id
        bing_grounding = BingGroundingTool(connection_id=conn_id)

        # 3. Create an agent with Bing grounding on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            name="BingGroundingAgent",
            instructions="Use the Bing grounding tool to answer the user's question.",
            model=AzureAIAgentSettings().model_deployment_name,
            tools=bing_grounding.definitions,
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
            async for response in agent.invoke(
                messages=TASK, thread=thread, on_intermediate_message=handle_intermediate_steps
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread

                # 7. Show annotations
                if any(isinstance(item, AnnotationContent) for item in response.items):
                    for annotation in response.items:
                        if isinstance(annotation, AnnotationContent):
                            print(
                                f"Annotation :> {annotation.url}, source={annotation.quote}, with "
                                f"start_index={annotation.start_index} and end_index={annotation.end_index}"
                            )
        finally:
            # 8. Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        
        # User: 'Which team won the 2025 NCAA basketball championship?'
        Function Call:> bing_grounding with arguments: 
            {
                'requesturl': 'https://api.bing.microsoft.com/v7.0/search?q=search(query:2025 NCAA basketball championship winner)', 
                'response_metadata': "{'market': 'en-US', 'num_docs_retrieved': 5, 'num_docs_actually_used': 5}"
            }
        # BingGroundingAgent: The team that won the 2025 NCAA men's basketball championship was the Florida Gators. They defeated the Houston Cougars with a final score of 65-63. 
            The championship game took place in San Antonio, Texas, and the Florida team was coached by Todd Golden. This victory made Florida the national champion for the 2024-25 
            NCAA Division I men's basketball season【3:0†source】【3:1†source】【3:2†source】.
        Annotation :> https://en.wikipedia.org/wiki/2025_NCAA_Division_I_men%27s_basketball_championship_game, source=【3:0†source】, with start_index=357 and end_index=369
        Annotation :> https://www.ncaa.com/history/basketball-men/d1, source=【3:1†source】, with start_index=369 and end_index=381
        Annotation :> https://sports.yahoo.com/article/won-march-madness-2025-ncaa-100551421.html, source=【3:2†source】, with start_index=381 and end_index=393
        """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
