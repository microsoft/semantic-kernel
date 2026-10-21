# Copyright (c) Microsoft. All rights reserved.

import asyncio
from datetime import timedelta

from azure.ai.agents.models import DeepResearchTool
from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread, RunPollingOptions
from semantic_kernel.contents import AnnotationContent, ChatMessageContent, FunctionCallContent, FunctionResultContent

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
        else:
            print(f"{item}")
        print()


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
            model="gpt-4o",
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
            async for response in agent.invoke(
                messages=TASK,
                thread=thread,
                on_intermediate_message=handle_intermediate_messages,
                polling_options=RunPollingOptions(run_polling_timeout=timedelta(minutes=10)),
            ):
                # Note that the underlying Deep Research Tool uses the o3 reasoning model.
                # When using the non-streaming invoke, it is normal for there to be
                # several minutes of processing before agent response(s) appear.
                # For a fast response, consider using the streaming invoke method.
                # A sample exists in the `concepts/agents/azure_ai_agent` directory.
                print(f"# {response.name}: {response}")
                for item in response.items or []:
                    if isinstance(item, AnnotationContent):
                        label = item.title or item.url or (item.quote or "Annotation")
                        print(f"\n[Annotation] {label} -> {item.url}")
                thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread, agent, and file
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        
        # User: 'Research the current state of studies on orca intelligence and orca language, including what is 
        currently known about orcas' cognitive capabilities and communication systems.'

        Function Call:> deep_research with arguments: {'input': '{"prompt": "Research the current state of studies on 
        orca intelligence and orca language. Include up-to-date findings on both their cognitive capabilities and 
        communication systems. Structure the findings as a detailed report with well-formatted headers that break down 
        topics such as orcas\' cognitive skills (e.g., problem-solving, memory, and social intelligence), their 
        language or communication methods (e.g., vocalizations, dialects, and symbolic communication), and comparisons 
        to other highly intelligent species. Include sources, prioritize recent peer-reviewed studies and reputable 
        marine biology publications, and ensure the report is well-cited and clear."}'}

        # DeepResearchAgent: Got it! I'll gather recent studies and findings on orca intelligence and their 
        # communication systems, focusing on cognitive abilities and the mechanisms of their language. 
        # I'll update you with a comprehensive overview soon.

        Title: Current Research on Orca Intelligence and Language

        Starting deep research... 

        # DeepResearchAgent: cot_summary: **Examining orca intelligence**  
        The task involves looking into orca cognitive abilities, communication methods, and comparisons with 
        other intelligent species. It includes recent peer-reviewed studies and credible sources. 【1†Bing Search】


        [Annotation] Bing Search: '2024 orca intelligence cognitive study research' -> https://www.bing.com/search?q=2024%20orca%20intelligence%20cognitive%20study%20research
        # DeepResearchAgent: cot_summary: **Investigating orca intelligence**

        I'm curious about headlines discussing orcas' cognitive abilities and behaviors, especially their tool use, 
        recent attacks, and comparisons with dolphins. 【1†Bing Search】


        [Annotation] Bing Search: 'orca cognition recent peer-reviewed studies orca communication recent study' -> https://www.bing.com/search?q=orca%20cognition%20recent%20peer-reviewed%20studies%20orca%20communication%20recent%20study
        # DeepResearchAgent: cot_summary: **Researching social dynamics**

        I'm gathering info on killer whale social dynamics from what appears to be a 2024 article on ResearchGate.

        # DeepResearchAgent: cot_summary: **Assessing publication type**  
        I'm exploring if the ResearchGate link points to a preprint, student paper, or journal article. 
        Progress is steady as I look into its initiation and source.

        # DeepResearchAgent: cot_summary: **Investigating PDF issues**

        ...
        """


if __name__ == "__main__":
    asyncio.run(main())
