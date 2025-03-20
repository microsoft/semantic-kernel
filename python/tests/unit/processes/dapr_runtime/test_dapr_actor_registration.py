# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest

from semantic_kernel.processes.dapr_runtime import (
    EventBufferActor,
    ExternalEventBufferActor,
    MessageBufferActor,
    ProcessActor,
    StepActor,
)
from semantic_kernel.processes.dapr_runtime.dapr_actor_registration import (
    create_actor_factories,
    register_fastapi_dapr_actors,
    register_flask_dapr_actors,
)


class MockActor:
    """Mock actor to record register_actor calls."""

    def __init__(self):
        self.registrations = []

    async def register_actor(self, actor_type, actor_factory=None):
        # Record registration details
        self.registrations.append({"actor_type": actor_type, "actor_factory": actor_factory})

    def register_actor_sync(self, actor_type, actor_factory=None):
        # Synchronous version for Flask
        self.registrations.append({"actor_type": actor_type, "actor_factory": actor_factory})


class MockFlaskDaprActor:
    """Mock Flask actor with synchronous register_actor method."""

    def __init__(self):
        self.registrations = []

    def register_actor(self, actor_type, actor_factory=None):
        self.registrations.append({"actor_type": actor_type, "actor_factory": actor_factory})


@pytest.fixture
def mock_kernel() -> MagicMock:
    """Provides a mock kernel object."""
    return MagicMock(name="Kernel")


@pytest.fixture
def mock_factories() -> dict:
    """Provides a mock factories dictionary."""
    return {"mock": lambda: "mock_factory"}


def test_create_actor_factories_returns_factories(mock_kernel, mock_factories):
    """
    Test that create_actor_factories returns callable factory functions that construct actors
    with the provided kernel and factories.
    """
    process_factory, step_factory = create_actor_factories(mock_kernel, mock_factories)

    # Check that the returned factories are callable
    assert callable(process_factory)
    assert callable(step_factory)

    # Create mock context and actor_id
    mock_ctx = MagicMock()
    mock_actor_id = MagicMock()
    mock_actor_id.id = "actor_1"

    # Call the factories to create ProcessActor and StepActor objects
    process_actor = process_factory(mock_ctx, mock_actor_id)
    step_actor = step_factory(mock_ctx, mock_actor_id)

    # Check that the actors have the kernel and factories set correctly
    assert hasattr(process_actor, "kernel")
    assert process_actor.kernel == mock_kernel
    assert hasattr(process_actor, "factories")
    assert process_actor.factories == mock_factories

    assert hasattr(step_actor, "kernel")
    assert step_actor.kernel == mock_kernel
    assert hasattr(step_actor, "factories")
    assert step_actor.factories == mock_factories


async def test_register_fastapi_dapr_actors(mock_kernel, mock_factories):
    """
    Test that register_fastapi_dapr_actors registers all the required actors with appropriate
    factories for FastAPI.
    """
    mock_actor = MockActor()

    # Call the registration function
    await register_fastapi_dapr_actors(mock_actor, mock_kernel, mock_factories)

    # There should be 5 registrations: ProcessActor, StepActor (with factories) and
    # three registrations without factories
    expected_actor_types = {ProcessActor, StepActor, EventBufferActor, MessageBufferActor, ExternalEventBufferActor}
    registered_actor_types = {reg["actor_type"] for reg in mock_actor.registrations}

    assert expected_actor_types == registered_actor_types

    # Verify that ProcessActor and StepActor registrations have an actor_factory
    for reg in mock_actor.registrations:
        if reg["actor_type"] in {ProcessActor, StepActor}:
            assert reg["actor_factory"] is not None
        else:
            assert reg.get("actor_factory") is None


def test_register_flask_dapr_actors(mock_kernel, mock_factories):
    """Test that register_flask_dapr_actors registers all the required actors with appropriate factories for Flask."""
    mock_actor = MockFlaskDaprActor()

    # Call the synchronous registration function
    register_flask_dapr_actors(mock_actor, mock_kernel, mock_factories)

    # There should be 5 registrations: ProcessActor, StepActor (with factories) and
    # three registrations without factories
    expected_actor_types = {ProcessActor, StepActor, EventBufferActor, MessageBufferActor, ExternalEventBufferActor}
    registered_actor_types = {reg["actor_type"] for reg in mock_actor.registrations}

    assert expected_actor_types == registered_actor_types

    # Check that ProcessActor and StepActor registrations have non-null actor_factory
    for reg in mock_actor.registrations:
        if reg["actor_type"] in {ProcessActor, StepActor}:
            assert reg["actor_factory"] is not None
        else:
            assert reg.get("actor_factory") is None
