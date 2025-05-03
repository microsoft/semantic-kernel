# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce

from azure.ai.projects.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    StreamingAnnotationContent,
    StreamingChatMessageContent,
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
    intermediate_steps.append(message)


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Enter your Bing Grounding Connection Name
        # <your-bing-grounding-connection-name>
        bing_connection = await client.connections.get(connection_name="skbinggrounding")
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

        print("====================================================")
        print("\nResponse complete:\n")
        # Combine the intermediate `StreamingChatMessageContent` chunks into a single message
        filtered_steps = [step for step in intermediate_steps if isinstance(step, StreamingChatMessageContent)]
        streaming_full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, filtered_steps)
        # Grab the other messages that are not `StreamingChatMessageContent`
        other_steps = [s for s in intermediate_steps if not isinstance(s, StreamingChatMessageContent)]
        final_msgs = [streaming_full_completion] + other_steps
        for msg in final_msgs:
            if any(isinstance(item, FunctionCallContent) for item in msg.items):
                for item in msg.items:
                    if isinstance(item, FunctionCallContent):
                        # Note: the AI Projects SDK is not returning a `requesturl` for streaming events
                        # The issue was raised with the AI Projects team
                        print(f"Function call: {item.function_name} with arguments: {item.arguments}")

            print(f"{msg.content}")

        """
        Sample Output:
        
        # User: 'Which team won the 2025 NCAA basketball championship?'
        # BingGroundingAgent: The Florida Gators won the 2025 NCAA men's basketball championship, defeating the Houston Cougars 65-63. It marked Florida's third national title and their first since back-to-back wins in 2006-2007【5:0†source】
        Annotation :> https://www.usatoday.com/story/sports/ncaab/2025/04/07/houston-florida-live-updates-national-championship-score/82982004007/, source=Florida vs Houston final score: Gators win 2025 NCAA championship, with start_index=198 and end_index=210
        【5:5†source】
        Annotation :> https://www.nbcsports.com/mens-college-basketball/live/florida-vs-houston-live-score-updates-game-news-stats-highlights-for-2025-ncaa-march-madness-mens-national-championship, source=Houston vs. Florida RECAP: Highlights, stats, box score, results as ..., with start_index=210 and end_index=222
        .
        ====================================================

        Response complete:

        Function call: bing_grounding with arguments: None
        Function call: bing_grounding with arguments: None

        The Florida Gators won the 2025 NCAA men's basketball championship, defeating the Houston Cougars 65-63. It marked Florida's third national title and their first since back-to-back wins in 2006-2007【5:0†source】【5:5†source】.
        """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
