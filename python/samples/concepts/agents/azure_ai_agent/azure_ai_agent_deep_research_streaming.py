# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import DeepResearchTool
from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingAnnotationContent,
)

"""
The following sample demonstrates how to create an AzureAIAgent along
with the Deep Research Tool. Please visit the following documentation for more info
on what is required to run the sample: https://aka.ms/agents-deep-research. Please pay
attention to the purple `Note` boxes in the Azure docs.

Note that when you use your Bing Connection ID, it needs to be the connection ID from the project, not the resource.
It has the following format:

'/subscriptions/<sub_id>/resourceGroups/<rg_name>/providers/<provider_name>/accounts/<account_name>/projects/<project_name>/connections/<connection_name>'
"""

TASK = (
    "Research the current state of studies on orca intelligence and orca language, "
    "including what is currently known about orcas' cognitive capabilities and communication systems."
)


async def handle_intermediate_messages(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, StreamingAnnotationContent):
            label = item.title or item.url or "Annotation"
            print(f"Annotation:> {label} ({item.citation_type}) -> {item.url}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        azure_ai_agent_settings = AzureAIAgentSettings()
        # 1. Define the Deep Research tool
        deep_research_tool = DeepResearchTool(
            bing_grounding_connection_id=azure_ai_agent_settings.bing_connection_id,
            deep_research_model=azure_ai_agent_settings.deep_research_model,
        )

        # 2. Create an agent with the tool on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model="gpt-4o",  # Deep Research requires the use of gpt-4o for scope clarification.
            tools=deep_research_tool.definitions,
            instructions="You are a helpful Agent that assists in researching scientific topics.",
        )

        # 3. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(client=client, definition=agent_definition, name="DeepResearchAgent")

        # 4. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 5. Invoke the agent for the specified thread for response
            first_chunk = True
            async for response in agent.invoke_stream(
                messages=TASK,
                thread=thread,
                on_intermediate_message=handle_intermediate_messages,
            ):
                if first_chunk:
                    print(f"# {response.name}: ", end="", flush=True)
                    first_chunk = False
                # Print the text chunk
                print(f"{response}", end="", flush=True)
                # Print any streaming annotations that may arrive in this chunk
                for item in response.items or []:
                    if isinstance(item, StreamingAnnotationContent):
                        label = item.title or item.url or (item.quote or "Annotation")
                        print(f"\n[Annotation] {label} -> {item.url}")
                thread = response.thread
                print()
        finally:
            # 6. Cleanup: Delete the thread, agent, and file
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        
        # User: 'Research the current state of studies on orca intelligence and orca language, including what is 
            currently known about orcas' cognitive capabilities and communication systems.'
        Function Call:> deep_research with arguments: {'input': '{"prompt": "Research the current state of studies on 
            orca intelligence and orca communication, focusing on their cognitive capabilities and language systems. 
            Provide an overview of key discoveries, critical experiments, and major conclusions about their 
            intelligence and communication systems. Prioritize primary research papers, reputable academic sources, 
            and recent updates in the field (from the past 5 years if available). Format as a structured report with 
            appropriate headings for clarity, and respond in English."}'}
        # azure_agent_QhTQHlUs: Title: Current Studies on Orca Intelligence and Communication

        Starting deep research... 

        The user's task is to research orca intelligence, focusing on cognitive capabilities and communication.
          【1†Bing Search】

        [Annotation] Bing Search: 'orca communication research 2020 killer whale cognitive study' -> https://www.bing.com/search?q=orca%20communication%20research%202020%20killer%20whale%20cognitive%20study

        **Weighing options**

        I'm examining the research on orca social dynamics, comparing a potential review to a recent journal article 
        on large-scale unsupervised clustering of orca calls.

        **Investigating orca datasets**

        OK, let me see. PDF, Interspeech 2020, "ORCA-CLEAN: A Deep Denoising Toolkit for Killer Whale Communication" 
        seems relevant. They focus on cognitive capabilities, language systems, and communication.

        I'm considering if the PDF is relevant and may not need it. ResearchGate's content might need a login 
        to access. 【1†Bing Search】

        [Annotation] Bing Search: '"Social Dynamics and Intelligence of Killer Whales (Orcinus orca)"' -> https://www.bing.com/search?q=%22Social%20Dynamics%20and%20Intelligence%20of%20Killer%20Whales%20%28Orcinus%20orca%29%22

        **Evaluating sources**

        I'm gathering info on "Social Dynamics and Intelligence of Killer Whales," weighing access to PDFs through 
        ResearchGate, and considering associated online references for credibility.

        **Considering capabilities**

        I'm piecing together the intricacies of killer whale creativity under chemical stimuli, as explored 
        in "Manitzas, Hill, et al 2022." Would love to learn more about their findings.

        **Exploring external options**  
        I'm weighing opening the PDF directly or using an external search. 【1†Bing Search】

        [Annotation] Bing Search: 'Manitzas Hill 2022 killer whale creativity cognitive abilities' -> https://www.bing.com/search?q=Manitzas%20Hill%202022%20killer%20whale%20creativity%20cognitive%20abilities
        
        ...
        """


if __name__ == "__main__":
    asyncio.run(main())
