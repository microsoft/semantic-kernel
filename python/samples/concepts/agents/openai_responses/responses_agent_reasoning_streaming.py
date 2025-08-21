# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai.azure_responses_agent import AzureResponsesAgent
from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings, OpenAISettings
from semantic_kernel.contents.reasoning_content import ReasoningContent

"""
The following sample demonstrates how to create an OpenAI Responses Agent
with reasoning capabilities using streaming patterns with either OpenAI or 
Azure OpenAI. The sample shows how to enable basic reasoning and reasoning 
with summaries that stream the agent's internal thought process.

Two streaming reasoning configurations are demonstrated:

1. Basic reasoning streaming:
   - Works for all OpenAI organizations
   - Reasoning happens internally but no intermediate thoughts are exposed
   - Still benefits from the model's reasoning process in final responses
   - Uses invoke_stream for real-time response streaming

2. Reasoning with summary streaming:
   - Requires verified OpenAI organization access
   - Exposes the model's internal thought process via ReasoningContent
   - Shows step-by-step reasoning through the intermediate message callback
   - Streams both reasoning summaries and final responses in real-time

The reasoning content shows the internal thought process of models that
support reasoning (like gpt-5, o3, o1-mini). This sample uses streaming
invocation patterns with invoke_stream.
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
    """Create a reasoning-enabled agent with summaries (requires verified org)."""
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
    """Handle reasoning content from the agent's intermediate messages during streaming.

    This callback function will be called for each intermediate message
    when reasoning summaries are enabled, allowing access to the model's
    internal thought process via ReasoningContent items during streaming.

    Args:
        message: The intermediate message containing potential ReasoningContent items.
    """
    reasoning_items = [item for item in message.items if isinstance(item, ReasoningContent)]
    for reasoning in reasoning_items:
        if reasoning.text:
            print(f"\033[36m{reasoning.text}\033[0m", end="", flush=True)


async def main():
    """The main function that demonstrates OpenAI Reasoning responses with streaming."""
    print("OpenAI ResponsesAgent Reasoning (streaming)")
    print("=" * 60)

    # 1. Create and use a basic reasoning agent with streaming
    try:
        agent = await create_reasoning_agent()
        if agent is None:
            print("No configuration detected. Set either OpenAI or Azure OpenAI environment variables:")
            print("- OpenAI: OPENAI_API_KEY and OPENAI_RESPONSES_MODEL_ID (or OPENAI_CHAT_MODEL_ID)")
            print("- Azure:  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")
            return

        user_input = "Plan a weekend camping trip for 4 people. What essential items should we pack?"
        print(f"\n=== Basic reasoning (streaming, no summary) ===\n# User: '{user_input}'")
        thread = None
        first_chunk = True
        async for response in agent.invoke_stream(messages=user_input, thread=thread):
            thread = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()
    except Exception as e:
        print(f"\nBasic reasoning example failed. Error: {e}")
        print("Please check your API configuration and model availability.")
        return

    # 2. Create and use a reasoning agent with summaries and streaming
    try:
        agent_summary = await create_reasoning_agent_with_summary()
        if agent_summary is None:
            print("\nNo configuration available for reasoning summaries.")
            return

        user_input2 = "Compare the benefits and drawbacks of renewable energy sources like solar and wind power."
        print(f"\n=== Reasoning with summaries (streaming) ===\n# User: '{user_input2}'")
        print("\nReasoning summary:")
        first_chunk = True
        async for response in agent_summary.invoke_stream(
            messages=user_input2, thread=thread, on_intermediate_message=handle_reasoning_message
        ):
            thread = response.thread
            if first_chunk:
                print(f"\n# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()
    except Exception as e:
        print(f"\nSummary examples require a verified organization. Error: {e}")
        print("The reasoning summary feature is only available to verified OpenAI organizations.")

    print("\n===== Done! =====")


if __name__ == "__main__":
    asyncio.run(main())
