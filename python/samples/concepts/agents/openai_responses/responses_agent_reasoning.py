# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents.open_ai.azure_responses_agent import AzureResponsesAgent
from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings, OpenAISettings
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates ResponsesAgent reasoning capabilities using both
Azure OpenAI and OpenAI. This shows all key reasoning functionality.

Features demonstrated:
1. Constructor-level reasoning effort configuration
2. Per-invocation reasoning effort override capability  
3. Priority hierarchy: per-invocation > constructor > model default
4. Multi-agent reasoning isolation
5. Reasoning output analysis and token monitoring
6. Practical reasoning scenarios (math, logic, strategy)
7. Function calling with reasoning capabilities

Requirements:
- OpenAI or Azure OpenAI API access
- Reasoning-capable model deployment (gpt-5, o4-mini, o3-mini, etc.)
- Environment variables configured (see semantic_kernel/.env.example)

The sample will try OpenAI first, then fall back to Azure OpenAI if not configured.
Uses GPT-5 as the default model (preferred for both reasoning and non-reasoning tasks).
Reasoning functionality requires models that support the reasoning parameter.
"""


class SimpleCalculator:
    """A simple calculator plugin for basic math operations."""

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
        print(f"Calculator: {a} × {b} = {result}")
        return result


class ReasoningAgentDemo:
    """Demonstration of ResponsesAgent reasoning capabilities."""

    def __init__(self):
        self.agent_low: OpenAIResponsesAgent | AzureResponsesAgent | None = None
        self.agent_high: OpenAIResponsesAgent | AzureResponsesAgent | None = None
        self.using_azure = False

    async def setup_agents(self):
        """Setup agents with different reasoning configurations."""
        print("Setting up ResponsesAgent instances...")

        # Try OpenAI first
        try:
            openai_settings = OpenAISettings()
            await self._setup_openai_agents(openai_settings)
            self.using_azure = False
            print("Using OpenAI")
            return
        except Exception as e:
            print(f"OpenAI not configured: {e}")

        # Fall back to Azure OpenAI (SK auto-loads from environment)
        try:
            azure_settings = AzureOpenAISettings()
            await self._setup_azure_agents(azure_settings)
            self.using_azure = True
            print(f"Using Azure OpenAI: {azure_settings.responses_deployment_name}")
            return
        except Exception as e:
            print(f"Azure OpenAI not configured: {e}")

        raise ValueError(
            "Missing configuration. Please set either:\n"
            "- OPENAI_API_KEY\n"
            "- OR AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME"
        )

    async def _setup_azure_agents(self, azure_settings: AzureOpenAISettings):
        """Setup Azure OpenAI agents."""
        # SK automatically loads configuration from environment
        client = AzureResponsesAgent.create_client()

        self.agent_low = AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="LowReasoningAgent",
            instructions=(
                "You are a helpful assistant that solves problems efficiently. "
                "Use the calculator functions when needed for mathematical operations."
            ),
            reasoning_effort="low",  # Constructor-level reasoning
            plugins=[SimpleCalculator()],
        )

        self.agent_high = AzureResponsesAgent(
            ai_model_id=azure_settings.responses_deployment_name,
            client=client,
            name="HighReasoningAgent",
            instructions="You are a helpful assistant that thinks through problems step-by-step.",
            reasoning_effort="high",  # Constructor-level reasoning
        )

    async def _setup_openai_agents(self, openai_settings: OpenAISettings):
        """Setup OpenAI agents."""
        # SK automatically loads configuration from environment
        model_id = openai_settings.chat_model_id or "gpt-5"  # Default to GPT-5 (preferred for reasoning)

        client = OpenAIResponsesAgent.create_client()

        self.agent_low = OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="LowReasoningAgent",
            instructions=(
                "You are a helpful assistant that solves problems efficiently. "
                "Use the calculator functions when needed for mathematical operations."
            ),
            reasoning_effort="low",  # Constructor-level reasoning
            plugins=[SimpleCalculator()],
        )

        self.agent_high = OpenAIResponsesAgent(
            ai_model_id=model_id,
            client=client,
            name="HighReasoningAgent",
            instructions="You are a helpful assistant that thinks through problems step-by-step.",
            reasoning_effort="high",  # Constructor-level reasoning
        )

    async def demo_constructor_reasoning(self):
        """Demonstrate constructor-level reasoning configuration."""
        print("\n" + "=" * 70)
        print("DEMO 1: Constructor-Level Reasoning Configuration")
        print("=" * 70)

        problem = (
            "I need to calculate a tip and split a bill. The restaurant bill is $45.60. "
            "I want to tip 18% and split the total equally among 3 people. "
            "How much does each person pay? Please use the calculator functions."
        )

        print(f"Problem: {problem}\n")

        # Low reasoning response (with function calling)
        print("LOW Reasoning Agent (constructor: 'low', with calculator):")
        print("-" * 50)

        async for content in self.agent_low.invoke([ChatMessageContent(role="user", content=problem)]):
            await self._display_response(content, "Low reasoning")
            break

        print()

        # High reasoning response (without function calling for comparison)
        problem_simple = (
            "A restaurant bill is $45.60. If you want to tip 18% and split "
            "the total equally among 3 people, how much does each person pay?"
        )
        print("HIGH Reasoning Agent (constructor: 'high', manual calculation):")
        print("-" * 50)

        async for content in self.agent_high.invoke([ChatMessageContent(role="user", content=problem_simple)]):
            await self._display_response(content, "High reasoning")
            break

    async def demo_per_invocation_override(self):
        """Demonstrate per-invocation reasoning override."""
        print("\n" + "=" * 70)
        print("DEMO 2: Per-Invocation Reasoning Override")
        print("=" * 70)
        print("Priority: per-invocation > constructor > model default\n")

        question = "What are the main benefits of renewable energy?"
        print(f"Question: {question}\n")

        # High agent with LOW override
        print("HIGH Agent with 'low' override (per-invocation wins):")
        print("-" * 50)

        async for content in self.agent_high.invoke(
            [ChatMessageContent(role="user", content=question)],
            reasoning_effort="low",  # Override constructor 'high'
        ):
            await self._display_response(content, "High→Low override")
            break

        print()

        # Low agent with HIGH override
        print("LOW Agent with 'high' override (per-invocation wins):")
        print("-" * 50)

        async for content in self.agent_low.invoke(
            [ChatMessageContent(role="user", content=question)],
            reasoning_effort="high",  # Override constructor 'low'
        ):
            await self._display_response(content, "Low→High override")
            break

    async def demo_complex_reasoning(self):
        """Demonstrate complex reasoning scenario."""
        print("\n" + "=" * 70)
        print("DEMO 3: Complex Reasoning Challenge")
        print("=" * 70)

        complex_problem = (
            "You have 8 coins that look identical, but one is counterfeit and weighs "
            "less than the others. You have a balance scale and can use it only twice. "
            "How do you find the counterfeit coin? Explain your strategy step-by-step."
        )

        print(f"Complex Problem: {complex_problem}\n")
        print("HIGH Reasoning Agent (thorough analysis):")
        print("-" * 50)

        async for content in self.agent_high.invoke([ChatMessageContent(role="user", content=complex_problem)]):
            await self._display_response(content, "Complex reasoning", truncate=600)
            break

    async def demo_reasoning_comparison(self):
        """Side-by-side reasoning comparison."""
        print("\n" + "=" * 70)
        print("DEMO 4: Reasoning Level Comparison")
        print("=" * 70)

        strategy_question = (
            "Should a startup focus on product development or customer acquisition first? "
            "Consider a tech startup with limited resources."
        )

        print(f"Strategic Question: {strategy_question}\n")

        # Get both responses
        print("LOW Reasoning Response:")
        print("-" * 30)
        async for content in self.agent_low.invoke([ChatMessageContent(role="user", content=strategy_question)]):
            await self._display_response(content, "Low reasoning", truncate=300)
            break

        print("\nHIGH Reasoning Response:")
        print("-" * 30)
        async for content in self.agent_high.invoke([ChatMessageContent(role="user", content=strategy_question)]):
            await self._display_response(content, "High reasoning", truncate=300)
            break

    async def _display_response(self, content, reasoning_type: str, truncate: int | None = None):
        """Display agent response with reasoning information."""
        # Check for reasoning metadata
        reasoning_info = {}
        if hasattr(content, "metadata") and content.metadata:
            reasoning_info = content.metadata.get("reasoning", {})

        if reasoning_info:
            tokens = reasoning_info.get("tokens", "unknown")
            print(f"Reasoning tokens: {tokens}")

            if reasoning_info.get("summary"):
                summary = reasoning_info["summary"]
                if len(summary) > 100:
                    print(f"Reasoning summary: {summary[:100]}...")
                else:
                    print(f"Reasoning summary: {summary}")

        # Display response
        response_text = str(content.content)
        if truncate and len(response_text) > truncate:
            print(f"Response: {response_text[:truncate]}...\n[Truncated for display]")
        else:
            print(f"Response: {response_text}")

    async def run_demo(self):
        """Run the complete reasoning demonstration."""
        print("OpenAI ResponsesAgent Reasoning Demonstration\n")

        try:
            await self.setup_agents()
            await self.demo_constructor_reasoning()
            await self.demo_per_invocation_override()
            await self.demo_complex_reasoning()
            await self.demo_reasoning_comparison()

            # Summary
            print("\n" + "=" * 70)
            print("DEMONSTRATION COMPLETE!")
            print("=" * 70)
            print("✓ Constructor-level reasoning configuration")
            print("✓ Per-invocation reasoning override")
            print("✓ Priority hierarchy demonstration")
            print("✓ Complex reasoning scenarios")
            print("✓ Reasoning level comparison")

            provider = "Azure OpenAI" if self.using_azure else "OpenAI"
            print(f"✓ Successfully demonstrated with {provider}")

        except Exception as e:
            print(f"Demo failed: {e}")
            print("\nTroubleshooting:")
            print("1. Verify your API keys are set correctly")
            print("2. Ensure you're using O-series models (o1, o3-mini, o4-mini)")
            print("3. Check your Azure OpenAI deployment if using Azure")


async def main():
    """Main entry point."""
    demo = ReasoningAgentDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
