# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingAnnotationContent,
)

"""
The following sample demonstrates how to create an Azure AI agent that
uses the Bing grounding tool to answer a user's question.

Additionally, the `on_intermediate_message` callback is used to handle intermediate messages
from the agent.

Note: Please visit the following link to learn more about the Bing grounding tool:

https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding?tabs=python&pivots=overview
"""

TASK = "Which team won the 2025 NCAA basketball championship?"

intermediate_steps: list[ChatMessageContent] = []


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
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
            first_chunk = True
            async for response in agent.invoke_stream(
                messages=TASK, thread=thread, on_intermediate_message=handle_streaming_intermediate_steps
            ):
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                print(f"{response}", end="", flush=True)
                thread = response.thread

                # 7. Show annotations
                if any(isinstance(item, StreamingAnnotationContent) for item in response.items):
                    print()
                    for annotation in response.items:
                        if isinstance(annotation, StreamingAnnotationContent):
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
        Function Call:> bing_grounding with arguments: {'requesturl': 'https://api.bing.microsoft.com/v7.0/search?q=search(query: 2025 NCAA basketball championship winner)'}
        Function Call:> bing_grounding with arguments: {'response_metadata': "{'market': 'en-US', 'num_docs_retrieved': 5, 'num_docs_actually_used': 5}"}
        # BingGroundingAgent: The Florida Gators won the 2025 NCAA men's basketball championship. They defeated the Houston Cougars with a close score of 65-63 in the championship game held in San Antonio, Texas. This victory marked their third national title. Florida overcame a 12-point deficit during the game to claim the championship【3:0†source】
        Annotation :> https://en.wikipedia.org/wiki/2025_NCAA_Division_I_men%27s_basketball_championship_game, source=None, with start_index=308 and end_index=320
        【3:1†source】
        Annotation :> https://www.ncaa.com/history/basketball-men/d1, source=None, with start_index=320 and end_index=332
        【3:2†source】
        Annotation :> https://sports.yahoo.com/article/florida-gators-win-2025-ncaa-034021303.html, source=None, with start_index=332 and end_index=344.
        """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
