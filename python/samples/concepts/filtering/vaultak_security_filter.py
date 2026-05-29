# Copyright (c) Microsoft. All rights reserved.

"""
Vaultak runtime security filter for Semantic Kernel.

Demonstrates how to integrate Vaultak (https://vaultak.com) with Semantic Kernel
using two filter types:

- FunctionInvocationFilter  — risk-scores every plugin function call before it
  executes and raises BlockedByVaultak when the score exceeds the threshold.
- AutoFunctionInvocationFilter — intercepts each tool call chosen by the LLM
  during auto-function-calling, allowing per-call blocking without stopping
  the whole invocation loop.

Install:
    pip install vaultak semantic-kernel

Set environment variables:
    OPENAI_API_KEY=sk-...
    VAULTAK_API_KEY=vtk_...
"""

import asyncio
import os
from collections.abc import Callable, Coroutine
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.exceptions import KernelFunctionCancelledError
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import KernelArguments

from vaultak import Vaultak

VAULTAK_API_KEY = os.environ.get("VAULTAK_API_KEY", "vtk_...")
RISK_THRESHOLD = 7.0  # Block function calls with a risk score >= this value

vt = Vaultak(api_key=VAULTAK_API_KEY, agent_name="sk-agent")

kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat"))
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")


# ---------------------------------------------------------------------------
# Filter 1: FunctionInvocationFilter
# Runs around every KernelFunction invocation (including prompt functions).
# Use this to risk-score explicit kernel.invoke() calls.
# ---------------------------------------------------------------------------
@kernel.filter(FilterTypes.FUNCTION_INVOCATION)
async def vaultak_function_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    """Risk-score every kernel function call before executing it."""
    plugin_name = context.function.plugin_name or "kernel"
    function_name = context.function.name
    action = f"{plugin_name}-{function_name}"

    # Collect function arguments as context for the risk scorer
    args_context = {k: str(v) for k, v in (context.arguments or {}).items()}

    result = vt.score_action(action=action, context=args_context)

    if result.score >= RISK_THRESHOLD:
        raise KernelFunctionCancelledError(
            f"[Vaultak] Function '{action}' blocked — risk score {result.score:.1f}/10 "
            f"exceeds threshold {RISK_THRESHOLD}. Review at app.vaultak.com"
        )

    # Check against configured policy rules
    vt.check_policy(tool_name=action, input_data=str(args_context))

    await next(context)

    # Scan the function output for PII before it propagates
    if context.result and context.result.value:
        raw_output = str(context.result.value)
        context.result._value = vt.mask_pii(raw_output)


# ---------------------------------------------------------------------------
# Filter 2: AutoFunctionInvocationFilter
# Runs for each tool call the LLM selects during auto-function-calling.
# Use this to risk-score or block individual tool calls mid-conversation.
# ---------------------------------------------------------------------------
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def vaultak_auto_filter(
    context: AutoFunctionInvocationContext,
    next: Callable[[AutoFunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    """Risk-score each LLM-selected tool call during auto function invocation."""
    plugin_name = context.function.plugin_name or "kernel"
    function_name = context.function.name
    action = f"{plugin_name}-{function_name}"

    result = vt.score_action(action=action, context={"auto_invoke": "true"})

    if result.score >= RISK_THRESHOLD:
        # Setting terminate=True stops the auto-invocation loop cleanly
        # instead of raising an exception that would surface to the user.
        context.terminate = True
        return

    vt.check_policy(tool_name=action, input_data=action)
    await next(context)


# ---------------------------------------------------------------------------
# Demo: run a short agent conversation
# ---------------------------------------------------------------------------
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=1000,
    function_choice_behavior=FunctionChoiceBehavior.Auto(
        filters={"included_plugins": ["math", "time"]}
    ),
)

history = ChatHistory()
history.add_system_message("You are a helpful assistant. Use math and time tools when asked.")


async def chat(user_input: str) -> None:
    history.add_user_message(user_input)
    arguments = KernelArguments(
        settings=execution_settings,
        chat_history=history,
        user_input=user_input,
    )
    result = await kernel.invoke_prompt(
        "{{$chat_history}}{{$user_input}}",
        arguments=arguments,
    )
    print(f"Assistant: {result}")
    history.add_assistant_message(str(result))


async def main() -> None:
    print("Vaultak security filters active. Every tool call is risk-scored before execution.")
    await chat("What is 42 multiplied by 7?")
    await chat("What time is it right now?")


if __name__ == "__main__":
    asyncio.run(main())
