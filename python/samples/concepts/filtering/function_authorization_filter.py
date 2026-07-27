# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.filters import (
    FilterTypes,
    FunctionAuthorizationFilter,
    FunctionAuthorizationPolicy,
    FunctionRiskLevel,
)
from semantic_kernel.functions import kernel_function

"""
This sample shows how to gate auto function invocation behind an explicit,
auditable authorization decision using the FunctionAuthorizationFilter
(see https://github.com/microsoft/semantic-kernel/issues/14072).

The scenario: an agent has both a harmless read-only function and a
destructive one. An indirect prompt injection (e.g. hidden instructions in a
retrieved document) can trick the model into *proposing* a destructive tool
call — but with the authorization filter registered, proposing a call is no
longer the same as executing it:

- low-risk calls are dispatched as usual;
- the destructive call is suspended as a pending decision and never runs;
- a human grants the pending decision, and re-issuing the *identical* call
  executes exactly once;
- replaying that approval with tampered arguments is rejected, because the
  approval is bound to the canonical argument digest.

The model side is simulated with hand-built FunctionCallContent objects, so
the sample runs without any model API key: kernel.invoke_function_call() is
exactly the entry point a chat completion service uses for every tool call
the model proposes during auto function invocation.
"""


class FileSystemPlugin:
    """A plugin exposing a harmless function and a destructive one."""

    def __init__(self):
        self.deleted: list[str] = []

    @kernel_function(name="read_file", description="Read a file from the workspace.")
    def read_file(self, path: str) -> str:
        return f"contents of {path}"

    @kernel_function(name="delete_path", description="Delete a file or directory tree.")
    def delete_path(self, path: str) -> str:
        self.deleted.append(path)
        return f"deleted {path}"


async def main() -> None:
    kernel = Kernel()
    file_system = FileSystemPlugin()
    kernel.add_plugin(file_system, plugin_name="fs")

    # Declare risk in function metadata (the filter also supports policy-side
    # overrides, and fails closed to HIGH for anything left unclassified).
    kernel.get_function("fs", "read_file").metadata.additional_properties = {"risk_level": "low"}
    kernel.get_function("fs", "delete_path").metadata.additional_properties = {"risk_level": "high"}

    auth_filter = FunctionAuthorizationFilter(
        policy=FunctionAuthorizationPolicy(
            principal="demo_user",
            # A deterministic tripwire: suspicious argument content escalates
            # the risk before dispatch, whatever the function's declared risk.
            keyword_guard={"..": FunctionRiskLevel.CRITICAL},
        )
    )
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auth_filter)

    history = ChatHistory()

    async def model_proposes(call_id: str, function_name: str, arguments: str):
        """Stand-in for the model's tool call during auto function invocation."""
        print(f"\nModel proposes: {function_name}({arguments})")
        await kernel.invoke_function_call(
            function_call=FunctionCallContent(
                id=call_id, plugin_name="fs", function_name=function_name, arguments=arguments
            ),
            chat_history=history,
        )
        print(f"  -> fed back to the model: {history.messages[-1].items[0].result}")

    # 1. A benign, low-risk call is dispatched as usual.
    await model_proposes("call_1", "read_file", '{"path": "report.md"}')

    # 2. An indirect prompt injection tricks the model into proposing a
    #    destructive call. The filter suspends it: nothing is deleted.
    await model_proposes("call_2", "delete_path", '{"path": "workspace/archive"}')
    pending = auth_filter.audit_log[-1]
    print(f"  deleted so far: {file_system.deleted}  (decision: {pending.status.value})")

    # 3. A human reviews the pending decision and grants it, then the caller
    #    re-issues the identical call: it now executes exactly once.
    auth_filter.grant_approval(pending)
    await model_proposes("call_3", "delete_path", '{"path": "workspace/archive"}')
    print(f"  deleted so far: {file_system.deleted}")

    # 4. Replaying with tampered arguments fails twice over: the earlier
    #    approval was bound to the exact argument digest (and was consumed),
    #    and the path-traversal payload trips the keyword guard, which
    #    escalates the call to CRITICAL and denies it outright.
    await model_proposes("call_4", "delete_path", '{"path": "workspace/../production"}')
    print(f"  deleted so far: {file_system.deleted}")

    print("\nAudit trail:")
    for decision in auth_filter.audit_log:
        print(
            f"  [{decision.status.value:>16}] {decision.function_name} "
            f"risk={decision.risk.value} via {decision.authority_source}: {decision.reason}"
        )


if __name__ == "__main__":
    asyncio.run(main())
