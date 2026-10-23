# Copyright (c) Microsoft. All rights reserved.

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable, Coroutine, Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from semantic_kernel import Kernel
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import FunctionResult, kernel_function

logger = logging.getLogger(__name__)

# This sample shows how to put a guard in front of tools that run commands, such as a shell tool,
# using the existing function invocation filter. The guard is vendor neutral: it only needs an object
# with a `scan(command)` method that returns a verdict. That object can be a simple deny list, a policy
# engine, a call into an OS level sandbox, or a third party guardrail library.
#
# The filter runs before the function. If the scanner does not allow the command, the filter does not call
# `next`, so the function never runs, and it puts a short message in `context.result` instead.
# The same pattern works for the auto function invocation filter (FilterTypes.AUTO_FUNCTION_INVOCATION).
# In that case set `context.function_result` instead of `context.result`.
#
# Important: a check on the command text is a safety net, not a security boundary. For untrusted code, also
# run the tool inside real isolation (a container, a VM, or OS level sandboxing).


@dataclass
class ScanVerdict:
    """The decision of a scanner for one command."""

    allowed: bool
    reason: str = ""


class CommandScanner(Protocol):
    """Anything that can decide if a command is allowed to run.

    `scan` can be a normal method or a coroutine function.
    """

    def scan(self, command: str) -> ScanVerdict | Awaitable[ScanVerdict]: ...


def create_command_guard_filter(
    scanner: CommandScanner,
    argument_names: Iterable[str] = ("command",),
) -> Callable[[FunctionInvocationContext, Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]]], Any]:
    """Create a function invocation filter that checks command arguments with the scanner before the call.

    Args:
        scanner: The scanner that decides if a command is allowed.
        argument_names: The names of the function arguments that hold a command to check.
    """
    names = tuple(argument_names)

    async def command_guard_filter(
        context: FunctionInvocationContext,
        next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
    ) -> None:
        for name in names:
            value = context.arguments.get(name)
            if value is None:
                continue
            verdict = scanner.scan(str(value))
            if inspect.isawaitable(verdict):
                verdict = await verdict
            if not verdict.allowed:
                # Only log the function name, the command itself may contain secrets.
                logger.warning(f"Blocked call to {context.function.fully_qualified_name}: {verdict.reason}")
                context.result = FunctionResult(
                    function=context.function.metadata,
                    value=f"Blocked by command guard: {verdict.reason or 'not allowed'}",
                )
                # do not call next, so the function does not run
                return
        await next(context)

    return command_guard_filter


class DenyListScanner:
    """A toy scanner for this sample: it blocks commands that contain one of the given fragments.

    Replace this with a real scanner. A deny list is easy to get around and is only used here to
    keep the sample small and runnable without any model or service.
    """

    def __init__(self, blocked_fragments: Iterable[str]) -> None:
        """Initialize the scanner with the fragments to block."""
        self.blocked_fragments = tuple(blocked_fragments)

    def scan(self, command: str) -> ScanVerdict:
        """Return a blocked verdict if the command contains a blocked fragment."""
        for fragment in self.blocked_fragments:
            if fragment in command:
                return ScanVerdict(allowed=False, reason=f"command contains '{fragment}'")
        return ScanVerdict(allowed=True)


class FakeShellPlugin:
    """A stand in for a shell tool. It does not run anything, it only echoes the command."""

    @kernel_function(name="run", description="Run a shell command.")
    def run(self, command: str) -> str:
        """Pretend to run the command."""
        return f"ran: {command}"


async def main() -> None:
    kernel = Kernel()
    kernel.add_plugin(FakeShellPlugin(), plugin_name="shell")

    scanner = DenyListScanner(blocked_fragments=["rm -rf /", "mkfs"])
    kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, create_command_guard_filter(scanner))

    for command in ["ls -la", "rm -rf /"]:
        result = await kernel.invoke(plugin_name="shell", function_name="run", command=command)
        print(f"{command!r} -> {result}")


if __name__ == "__main__":
    asyncio.run(main())
