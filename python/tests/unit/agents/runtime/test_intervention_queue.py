# Copyright (c) Microsoft. All rights reserved.

import asyncio
from dataclasses import dataclass

import pytest

from semantic_kernel.agents.runtime.core.agent_id import CoreAgentId
from semantic_kernel.agents.runtime.core.exceptions import MessageDroppedException
from semantic_kernel.agents.runtime.core.intervention import DefaultInterventionHandler, DropMessage
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import RoutedAgent, message_handler
from semantic_kernel.agents.runtime.in_process.default_topic import DefaultTopicId
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.agents.runtime.in_process.type_subscription import TypeSubscription


@dataclass
class Payload:
    text: str


class EchoAgent(RoutedAgent):
    def __init__(self):
        super().__init__("Deterministic echo agent")

    @message_handler
    async def echo(self, message: Payload, ctx: MessageContext) -> Payload:
        return message


class Interceptor(DefaultInterventionHandler):
    def __init__(self, stage, outcome):
        self.stage = stage
        self.outcome = outcome
        self.entered = asyncio.Event()

    def intercept(self, stage, message):
        if stage != self.stage:
            return message
        self.entered.set()
        if self.outcome == "raise":
            raise ValueError("intercepted")
        if self.outcome == "drop-class":
            return DropMessage
        if self.outcome == "drop-instance":
            return DropMessage()
        return message

    async def on_send(self, message, *, message_context, recipient):
        return self.intercept("send", message)

    async def on_publish(self, message, *, message_context):
        return self.intercept("publish", message)

    async def on_response(self, message, *, sender, recipient):
        return self.intercept("response", message)


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["send", "publish", "response"])
@pytest.mark.parametrize("outcome", ["drop-class", "drop-instance", "raise", "pass"])
async def test_interception_releases_idle_waiter(stage, outcome):
    interceptor = Interceptor(stage, outcome)
    runtime = InProcessRuntime(intervention_handlers=[interceptor])
    await EchoAgent.register(runtime, "echo", EchoAgent)
    await runtime.add_subscription(TypeSubscription("default", "echo"))
    runtime.start()
    # Retain the run context for cleanup even if a timed-out public stop resets it.
    run_context = runtime._run_context
    idle_task = None
    try:
        message = Payload("hello")
        if stage == "publish":
            await runtime.publish_message(message, DefaultTopicId())
        elif outcome == "pass":
            assert await asyncio.wait_for(runtime.send_message(message, CoreAgentId("echo", "default")), 1) == message
        else:
            error = ValueError if outcome == "raise" else MessageDroppedException
            with pytest.raises(error):
                await asyncio.wait_for(runtime.send_message(message, CoreAgentId("echo", "default")), 1)

        await asyncio.wait_for(interceptor.entered.wait(), 1)
        # Exercise the public idle-stop API. Shield avoids cancelling the runtime's
        # stop coroutine merely because the assertion deadline expires.
        idle_task = asyncio.create_task(runtime.stop_when_idle())
        await asyncio.wait_for(asyncio.shield(idle_task), 0.5)
    finally:
        if run_context is not None and not run_context._run_task.done():
            await run_context.stop()
        if idle_task is not None and not idle_task.done():
            idle_task.cancel()
            await asyncio.gather(idle_task, return_exceptions=True)
        await runtime.close()
