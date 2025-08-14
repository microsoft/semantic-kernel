# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents.open_ai.azure_responses_agent import AzureResponsesAgent
from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings, OpenAISettings
from semantic_kernel.contents.reasoning_content import ReasoningContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI Responses Agent
with reasoning capabilities using either OpenAI or Azure OpenAI. The sample 
shows how to capture and display the agent's reasoning process via the 
on_intermediate_message callback.

This sample demonstrates two configurations:

1. Basic reasoning (reasoning={"effort": "high"}):
   - Works for all OpenAI organizations
   - Reasoning happens internally but no intermediate thoughts are exposed
   - Still benefits from the model's reasoning process in final responses

2. Reasoning with summary (reasoning={"effort": "high", "summary": "detailed"}):
   - Requires verified OpenAI organization access
   - Exposes the model's internal thought process via ReasoningContent
   - Shows step-by-step reasoning in visual "MODEL THOUGHTS" boxes

The reasoning content shows the internal thought process of models that
support reasoning (like gpt-5, o3, o1-mini). Examples include both streaming
and non-streaming invocation patterns with and without tool usage.
"""


class MathPlugin:
    """A sample Math Plugin used for the concept sample."""

    @kernel_function(description="Add two numbers together")
    def add(
        self, a: Annotated[float, "The first number"], b: Annotated[float, "The second number"]
    ) -> Annotated[float, "The sum of the two numbers"]:
        result = a + b
        print(f"Calculator: {a} + {b} = {result}")
        return result

    @kernel_function(description="Multiply two numbers")
    def multiply(
        self, a: Annotated[float, "The first number"], b: Annotated[float, "The second number"]
    ) -> Annotated[float, "The product of the two numbers"]:
        result = a * b
        print(f"Calculator: {a} * {b} = {result}")
        return result


async def create_reasoning_agent_with_summary():
    """Create a reasoning-enabled agent with summary (requires verified org)."""
    # Try OpenAI first
    openai_settings = OpenAISettings()
    model_id = openai_settings.responses_model_id or openai_settings.chat_model_id
    if openai_settings.api_key and model_id:
        client = OpenAIResponsesAgent.create_client()
        agent = OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step and uses tools when needed.",
            plugins=[MathPlugin()],
            reasoning={"effort": "high", "summary": "detailed"},
        )
        return agent, f"OpenAI ({model_id})"

    # Fallback to Azure OpenAI
    azure_settings = AzureOpenAISettings()
    if azure_settings.endpoint and azure_settings.responses_deployment_name:
        client = AzureResponsesAgent.create_client()
        agent = AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step and uses tools when needed.",
            plugins=[MathPlugin()],
            reasoning={"effort": "high", "summary": "detailed"},
        )
        return agent, f"Azure OpenAI ({azure_settings.responses_deployment_name})"

    return None, None


async def create_reasoning_agent():
    """Create a reasoning-enabled agent without summary (works for all orgs)."""
    # Try OpenAI first
    openai_settings = OpenAISettings()
    model_id = openai_settings.responses_model_id or openai_settings.chat_model_id
    if openai_settings.api_key and model_id:
        client = OpenAIResponsesAgent.create_client()
        agent = OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step and uses tools when needed.",
            plugins=[MathPlugin()],
            reasoning={"effort": "high"},
        )
        return agent, f"OpenAI ({model_id})"

    # Fallback to Azure OpenAI
    azure_settings = AzureOpenAISettings()
    if azure_settings.endpoint and azure_settings.responses_deployment_name:
        client = AzureResponsesAgent.create_client()
        agent = AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="ReasoningAgent",
            instructions="You are a helpful assistant that thinks step-by-step and uses tools when needed.",
            plugins=[MathPlugin()],
            reasoning={"effort": "high"},
        )
        return agent, f"Azure OpenAI ({azure_settings.responses_deployment_name})"

    return None, None


# Global variable to accumulate streaming reasoning content
reasoning_accumulator = ""


async def handle_reasoning_message(message):
    """Handle reasoning content from the agent's intermediate messages."""
    reasoning_items = [item for item in message.items if isinstance(item, ReasoningContent)]
    if reasoning_items:
        for reasoning in reasoning_items:
            if reasoning.text:
                # Just print reasoning text in cyan color
                print(f"\033[36m{reasoning.text}\033[0m", end="", flush=True)


async def main():
    print("OpenAI ResponsesAgent Reasoning Demo")
    print("=" * 60)

    # Test basic reasoning configuration
    print("\nTesting WITHOUT summary parameter (works for all organizations)")
    print("-" * 60)

    agent_basic, label_basic = await create_reasoning_agent()
    if agent_basic is None:
        print("No configuration detected. Set either OpenAI or Azure OpenAI environment variables:")
        print("- OpenAI: OPENAI_API_KEY and OPENAI_RESPONSES_MODEL_ID (or OPENAI_CHAT_MODEL_ID)")
        print("- Azure:  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME")
        return

    print(f"Using {label_basic}")
    if "OpenAI (" in label_basic:
        print("Tip: Use reasoning-capable models like 'gpt-5', 'o3', or 'o1-mini' for best results")

    # Example 1: Basic reasoning without summary - invoke
    print("\n=== Example 1: Basic reasoning (invoke, no summary) ===")
    user_input = "What are the three main benefits of using renewable energy sources?"
    print(f"# User: '{user_input}'")

    thread = None
    async for response in agent_basic.invoke(
        messages=user_input, thread=thread, on_intermediate_message=handle_reasoning_message
    ):
        thread = response.thread
        print(f"# {response.name}: {response.content}")
        break

    # Example 2: Basic reasoning without summary - streaming
    print("\n=== Example 2: Basic reasoning (streaming, no summary) ===")
    user_input = "Explain how photosynthesis works in simple terms."
    print(f"# User: '{user_input}'")

    first_chunk = True
    async for response in agent_basic.invoke_stream(
        messages=user_input, thread=thread, on_intermediate_message=handle_reasoning_message
    ):
        thread = response.thread
        if first_chunk:
            print(f"# {response.name}: ", end="", flush=True)
            first_chunk = False
        print(response.content, end="", flush=True)
    print("\n")

    # Test reasoning with summary parameter
    print("\nTesting WITH summary parameter (requires verified organization)")
    print("-" * 60)

    try:
        agent_summary, label_summary = await create_reasoning_agent_with_summary()
        if agent_summary is None:
            print("No configuration available for summary testing.")
            return

        print(f"Using {label_summary} with summary enabled")

        # Example 3: Reasoning with summary - invoke
        print("\n=== Example 3: With reasoning summary (invoke) ===")
        user_input = "Calculate the compound interest on $1000 invested at 5% annually for 3 years."
        print(f"# User: '{user_input}'")

        thread_summary = None
        async for response in agent_summary.invoke(
            messages=user_input, thread=thread_summary, on_intermediate_message=handle_reasoning_message
        ):
            thread_summary = response.thread
            print(f"# {response.name}: {response.content}")
            break

        # Example 4: Reasoning with tools and summary - streaming
        print("\n=== Example 4: With tools and reasoning summary (streaming) ===")
        user_input = (
            "I want to buy 5 items that cost $8.75 each. Then I need to add 7.25% sales tax. "
            "What's the total amount I'll pay? Please use the calculator functions."
        )
        print(f"# User: '{user_input}'")

        first_chunk = True
        async for response in agent_summary.invoke_stream(
            messages=user_input, thread=thread_summary, on_intermediate_message=handle_reasoning_message
        ):
            thread_summary = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"Summary examples require a verified organization. Error: {e}")
        print("The reasoning summary feature is only available to verified OpenAI organizations.")

    print("\n" + "=" * 60)
    print("Demo complete! Key differences:")
    print("- Without summary: Reasoning happens internally, no intermediate thoughts shown")
    print("- With summary: Model thoughts/reasoning process visible in cyan color")
    print("- Summary parameter requires verified OpenAI organization access")


if __name__ == "__main__":
    asyncio.run(main())
