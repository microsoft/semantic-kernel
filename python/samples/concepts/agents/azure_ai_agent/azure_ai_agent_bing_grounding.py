# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import AnnotationContent

"""
The following sample demonstrates how to create an Azure AI agent that
uses the Bing grounding tool to answer a user's question.

Note: Please visit the following link to learn more about the Bing grounding tool:

https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding?tabs=python&pivots=overview
"""

TASK = "Which team won the 2025 NCAA basketball championship?"


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Enter your Bing Grounding Connection Name
        bing_connection = await client.connections.get(connection_name="<your-bing-grounding-connection-name>")
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
            async for response in agent.invoke(messages=TASK, thread=thread):
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
        # BingGroundingAgent: The Florida Gators won the 2025 NCAA basketball championship, defeating the Houston Cougars 65-63 in the final to secure their third national title【3:5†source】【3:6†source】【3:9†source】.
        Annotation :> https://www.usatoday.com/story/sports/ncaab/2025/04/07/houston-florida-live-updates-national-championship-score/82982004007/, source=【3:5†source】, with start_index=147 and end_index=159
        Annotation :> https://bleacherreport.com/articles/25182096-winners-and-losers-2025-mens-ncaa-tournament, source=【3:6†source】, with start_index=159 and end_index=171
        Annotation :> https://wtop.com/ncaa-basketball/2025/04/ncaa-basketball-champions/, source=【3:9†source】, with start_index=171 and end_index=183
        """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
