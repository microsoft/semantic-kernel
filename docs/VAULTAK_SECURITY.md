# Vaultak Runtime Security Integration

[Vaultak](https://vaultak.com) is a runtime security platform that wraps Semantic Kernel agents
with real-time protection. Every plugin function call and LLM tool selection is risk-scored (0–10),
checked against your policy rules, and automatically blocked before it reaches your production
systems — without changing your agent logic.

## Why use Vaultak with Semantic Kernel?

SK agents given plugins can cause real damage: deleted records, leaked PII, unauthorized API calls.
Vaultak adds a security layer via SK's native **filter** system:

- **Risk scoring** on every plugin function call before it executes  
- **Policy enforcement** — block calls that violate your rules  
- **PII masking** — strip sensitive data from plugin outputs  
- **Audit trail** — every call, every score, in your Vaultak dashboard  

## How it works

Semantic Kernel's [filter system](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters)
is the native hook for security and observability. Vaultak registers two filters:

| Filter type | When it runs | Vaultak action |
|---|---|---|
| `FunctionInvocationFilter` | Every `kernel.invoke()` call (plugin functions only) | Risk-scores the call; raises `OperationCancelledException` if score meets or exceeds threshold; masks PII in output |
| `AutoFunctionInvocationFilter` | Each LLM-selected tool call (auto function calling) | Risk-scores the call; sets `context.terminate = True` to stop the loop if above threshold |

## Installation

```bash
pip install vaultak semantic-kernel
```

Sign up at [vaultak.com](https://vaultak.com) to get your API key (starts with `vtk_`).

## Quick start

```python
import asyncio
import os
from collections.abc import Callable, Coroutine
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.exceptions import OperationCancelledException
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import FunctionResult, KernelArguments

from vaultak import Vaultak

_api_key = os.environ.get("VAULTAK_API_KEY")
if not _api_key:
    raise ValueError(
        "VAULTAK_API_KEY environment variable is not set. "
        "Sign up at https://vaultak.com to get your API key."
    )

RISK_THRESHOLD = 7.0
vt = Vaultak(api_key=_api_key, agent_name="sk-agent")

kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat"))
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")


@kernel.filter(FilterTypes.FUNCTION_INVOCATION)
async def vaultak_function_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    # Skip inline prompt functions — only score real plugin calls
    if context.function.plugin_name is None:
        await next(context)
        return
    action = f"{context.function.plugin_name}-{context.function.name}"
    result = await asyncio.to_thread(vt.score_action, action=action, context=dict(context.arguments or {}))
    if result.score >= RISK_THRESHOLD:
        raise OperationCancelledException(
            f"[Vaultak] '{action}' blocked — risk {result.score:.1f}/10 "
            f"meets or exceeds threshold {RISK_THRESHOLD}. Review at app.vaultak.com"
        )
    await asyncio.to_thread(vt.check_policy, tool_name=action, input_data=str(context.arguments))
    await next(context)
    if context.result and context.result.value:
        masked = await asyncio.to_thread(vt.mask_pii, str(context.result.value))
        context.result = FunctionResult(function=context.function, value=masked)


@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def vaultak_auto_filter(
    context: AutoFunctionInvocationContext,
    next: Callable[[AutoFunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    action = f"{context.function.plugin_name or 'kernel'}-{context.function.name}"
    result = await asyncio.to_thread(vt.score_action, action=action, context={"auto_invoke": "true"})
    if result.score >= RISK_THRESHOLD:
        context.terminate = True  # Stop auto-invocation loop cleanly
        return
    await next(context)
```

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | — | Your Vaultak API key — required |
| `agent_name` | `str` | `"sk-agent"` | Label for this kernel in the Vaultak dashboard |
| `risk_threshold` | `float` | `7.0` | Score (0–10) above which calls are blocked |
| `verbose` | `bool` | `False` | Log every scored action to stdout |

## What gets monitored

| SK event | Vaultak action |
|---|---|
| `kernel.invoke()` (explicit call) | Risk-scores the plugin + function; blocks if above threshold |
| Auto function call selected by LLM | Risk-scores; terminates auto-invocation loop if above threshold |
| Plugin output returned | Scans for PII and masks before the result propagates |
| Policy check fails | Raises exception with dashboard URL |

## Complete sample

See [`python/samples/concepts/filtering/vaultak_security_filter.py`](../python/samples/concepts/filtering/vaultak_security_filter.py)
for a runnable end-to-end example with MathPlugin and TimePlugin.

## Links

- [Vaultak documentation](https://docs.vaultak.com)
- [PyPI: `vaultak`](https://pypi.org/project/vaultak)
- [GitHub](https://github.com/vaultak/vaultak-python)
- [Dashboard](https://app.vaultak.com)
- [SK Filters concept](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/filters)
