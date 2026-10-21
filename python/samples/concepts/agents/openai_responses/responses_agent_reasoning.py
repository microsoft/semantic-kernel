# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai.azure_responses_agent import AzureResponsesAgent
from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings, OpenAISettings
from semantic_kernel.contents.reasoning_content import ReasoningContent

"""
The following sample demonstrates how to create an OpenAI Responses Agent
with reasoning capabilities using either OpenAI or Azure OpenAI. The sample
shows how to enable basic reasoning and reasoning with summaries, which exposes
the agent's internal thought process via the on_intermediate_message callback.

Two reasoning configurations are demonstrated:

1. Basic reasoning:
   - Works for all OpenAI organizations
   - Reasoning happens internally but no intermediate thoughts are exposed
   - Still benefits from the model's reasoning process in final responses

2. Reasoning with summary:
   - Requires verified OpenAI organization access
   - Exposes the model's internal thought process via ReasoningContent
   - Shows step-by-step reasoning through the intermediate message callback

The reasoning content shows the internal thought process of models that
support reasoning (like gpt-5, o3, o1-mini). This sample uses non-streaming
invocation patterns.
"""


async def create_reasoning_agent():
    """Create a reasoning-enabled agent without summary (works for all orgs)."""
    openai_settings = OpenAISettings()
    model_id = openai_settings.responses_model_id or openai_settings.chat_model_id
    if openai_settings.api_key and model_id:
        client = OpenAIResponsesAgent.create_client()
        return OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step.",
            reasoning={"effort": "high"},
        )

    # Fallback to Azure OpenAI
    azure_settings = AzureOpenAISettings()
    if azure_settings.endpoint and azure_settings.responses_deployment_name:
        client = AzureResponsesAgent.create_client()
        return AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step.",
            reasoning={"effort": "high"},
        )

    return None


async def create_reasoning_agent_with_summary():
    """Create a reasoning-enabled agent with summary (requires verified org)."""
    openai_settings = OpenAISettings()
    model_id = openai_settings.responses_model_id or openai_settings.chat_model_id
    if openai_settings.api_key and model_id:
        client = OpenAIResponsesAgent.create_client()
        return OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step.",
            reasoning={"effort": "high", "summary": "detailed"},
        )

    azure_settings = AzureOpenAISettings()
    if azure_settings.endpoint and azure_settings.responses_deployment_name:
        client = AzureResponsesAgent.create_client()
        return AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step.",
            reasoning={"effort": "high", "summary": "detailed"},
        )

    return None


async def handle_reasoning_message(message):
    """Handle reasoning content from the agent's intermediate messages.

    This callback function will be called for each intermediate message
    when reasoning summaries are enabled, allowing access to the model's
    internal thought process via ReasoningContent items.

    Args:
        message: The intermediate message containing potential ReasoningContent items.
    """
    reasoning_items = [item for item in message.items if isinstance(item, ReasoningContent)]
    for reasoning in reasoning_items:
        if reasoning.text:
            print(f"\033[36m{reasoning.text}\033[0m", end="", flush=True)


async def main():
    """The main function that demonstrates OpenAI Reasoning responses."""
    # Define the query to test reasoning capabilities
    query = "Plan a birthday party for 15 people with a $500 budget. What are the key decisions I need to make?"

    # 1. Create and use a basic reasoning agent
    try:
        reasoning_agent = await create_reasoning_agent()
        if not reasoning_agent:
            print("Failed to create reasoning agent. Please check your API configuration.")
            return

        print("===== Basic Reasoning =====")
        print(f"Query: {query}")
        print("\nResponse:")
        await reasoning_agent.add_chat_message(content=query, role="user")
        reasoning_response = await reasoning_agent.invoke()
        print(f"{reasoning_response.content}")
    except Exception as e:
        print(f"Basic reasoning example failed. Error: {e}")
        print("Please check your API configuration and model availability.")
        return

    # 2. Create and use a reasoning agent with summaries enabled
    try:
        reasoning_with_summary_agent = await create_reasoning_agent_with_summary()
        if not reasoning_with_summary_agent:
            print("Failed to create reasoning agent with summary. This requires verified OpenAI organization access.")
            print("===== Done! =====")
            return

        print("\n\n===== Reasoning with Summaries =====")
        print(f"Query: {query}")
        print("\nReasoning summary:")
        await reasoning_with_summary_agent.add_chat_message(content=query, role="user")
        summary_response = await reasoning_with_summary_agent.invoke(handle_reasoning_message)
        print(f"\n\nAnswer: {summary_response.content}")
    except Exception as e:
        print(f"\nSummary examples require a verified organization. Error: {e}")
        print("The reasoning summary feature is only available to verified OpenAI organizations.")

    print("\n\n===== Done! =====")


if __name__ == "__main__":
    asyncio.run(main())
