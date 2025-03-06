# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TYPE_CHECKING

from dapr.actor import ActorId
from dapr.actor.runtime.context import ActorRuntimeContext
from dapr.ext.fastapi import DaprActor as FastAPIDaprActor
from flask_dapr.actor import DaprActor as FlaskDaprActor

from semantic_kernel.processes.dapr_runtime import (
    EventBufferActor,
    ExternalEventBufferActor,
    MessageBufferActor,
    ProcessActor,
    StepActor,
)

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


def create_actor_factories(kernel: "Kernel", factories: dict[str, Callable] | None = None) -> tuple:
    """Creates actor factories for ProcessActor and StepActor."""
    if factories is None:
        factories = {}

    def process_actor_factory(
        ctx: ActorRuntimeContext,
        actor_id: ActorId,
    ) -> ProcessActor:
        return ProcessActor(ctx, actor_id, kernel=kernel, factories=factories)

    def step_actor_factory(
        ctx: ActorRuntimeContext,
        actor_id: ActorId,
    ) -> StepActor:
        return StepActor(ctx, actor_id, kernel=kernel, factories=factories)

    return process_actor_factory, step_actor_factory


# Asynchronous registration for FastAPI
async def register_fastapi_dapr_actors(
    actor: FastAPIDaprActor, kernel: "Kernel", factories: dict[str, Callable] | None = None
) -> None:
    """Registers the actors with the Dapr runtime for use with a FastAPI app."""
    process_actor_factory, step_actor_factory = create_actor_factories(kernel, factories)
    await actor.register_actor(ProcessActor, actor_factory=process_actor_factory)
    await actor.register_actor(StepActor, actor_factory=step_actor_factory)
    await actor.register_actor(EventBufferActor)
    await actor.register_actor(MessageBufferActor)
    await actor.register_actor(ExternalEventBufferActor)


# Synchronous registration for Flask
def register_flask_dapr_actors(
    actor: FlaskDaprActor, kernel: "Kernel", factory: dict[str, Callable] | None = None
) -> None:
    """Registers the actors with the Dapr runtime for use with a Flask app."""
    process_actor_factory, step_actor_factory = create_actor_factories(kernel, factory)
    actor.register_actor(ProcessActor, actor_factory=process_actor_factory)
    actor.register_actor(StepActor, actor_factory=step_actor_factory)
    actor.register_actor(EventBufferActor)
    actor.register_actor(MessageBufferActor)
    actor.register_actor(ExternalEventBufferActor)
