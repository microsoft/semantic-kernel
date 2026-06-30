# Copyright (c) Microsoft. All rights reserved.

# This sample demonstrates Anthropic prompt caching with Semantic Kernel.
# Prompt caching lets you mark parts of a request (system message, tool definitions)
# as cacheable so that repeated calls reuse the cached tokens at 0.1x read cost.
#
# Prerequisites:
#   - Set ANTHROPIC_API_KEY and ANTHROPIC_CHAT_MODEL_ID in your environment or a .env file.
#   - Model must support caching (claude-haiku-4-5, claude-sonnet-4-x, claude-opus-4-x).
#   - Minimum tokens to activate cache: 4,096 (Haiku), 1,024 (Sonnet/Opus).
#
# Run:
#   uv run python samples/concepts/caching/anthropic_prompt_caching.py

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.anthropic import (
    AnthropicCacheSettings,
    AnthropicChatCompletion,
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory

# A long system prompt that exceeds the minimum token threshold for caching.
# In production this would typically be a large instruction set, persona, or
# document that stays the same across many turns.
SYSTEM_PROMPT = (
    """
You are an expert software engineer specializing in Python and distributed systems.
You provide precise, production-quality answers. When writing code you follow these rules:
  - Use type hints throughout.
  - Prefer composition over inheritance.
  - Write small, single-purpose functions.
  - Handle errors explicitly; never silence exceptions.
  - Include a brief docstring only when the intent is non-obvious.
  - Use async/await for all I/O-bound operations.
  - Prefer dataclasses or Pydantic models for structured data.

You are also familiar with the following internal guidelines:
  - All public APIs must be versioned.
  - Services communicate over gRPC with Protobuf schemas checked into the repo.
  - Secrets are injected at runtime via environment variables; never hardcoded.
  - Observability: every service emits structured JSON logs and OpenTelemetry traces.
  - Deployments use Kubernetes with Helm charts; no raw manifests.

When asked to review code, structure your response as:
  1. Summary (1-2 sentences)
  2. Issues (bulleted, severity labeled)
  3. Suggested fix (code block if applicable)
"""
    * 3
)  # repeat to ensure we comfortably exceed the 1,024-token minimum


async def chat_with_caching() -> None:
    """Run a multi-turn chat with prompt caching enabled on the system message."""
    kernel = Kernel()

    service = AnthropicChatCompletion(service_id="anthropic")
    kernel.add_service(service)

    # AnthropicCacheSettings.on() enables caching for both the system message and
    # tool definitions. Use .system() or .tools() to cache only one section.
    # Use .long() for 1-hour TTL when calls are infrequent.
    settings = AnthropicChatPromptExecutionSettings(
        service_id="anthropic",
        max_tokens=512,
        cache=AnthropicCacheSettings.on(),
    )

    chat_history = ChatHistory(system_message=SYSTEM_PROMPT)

    questions = [
        "What is the difference between asyncio.gather and asyncio.TaskGroup?",
        "When would you choose gRPC over REST for an internal service?",
        "How do you structure a Pydantic settings class for a twelve-factor app?",
    ]

    print("Anthropic Prompt Caching Demo")
    print("=" * 50)
    print("System prompt is marked for caching. The first call writes the cache;")
    print("subsequent calls read from it at 0.1x token cost.\n")

    for i, question in enumerate(questions, start=1):
        print(f"Turn {i}: {question}")
        chat_history.add_user_message(question)

        response = await service.get_chat_message_content(
            chat_history=chat_history,
            settings=settings,
        )
        if response:
            print(f"Assistant: {response}\n")
            chat_history.add_message(response)


if __name__ == "__main__":
    asyncio.run(chat_with_caching())
