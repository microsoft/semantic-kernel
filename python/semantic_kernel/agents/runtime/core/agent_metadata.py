# Copyright (c) Microsoft. All rights reserved.

from typing import Protocol, runtime_checkable

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
@runtime_checkable
class AgentMetadata(Protocol):
    """Provides a description for an agent: type, key, and an optional 'description' field."""

    @property
    def type(self) -> str:
        """Defines the 'type' or category of the agent."""
        ...

    @property
    def key(self) -> str:
        """Defines the 'key' or identifier of the agent."""
        ...

    @property
    def description(self) -> str:
        """Defines the 'description' of the agent."""
        ...


@experimental
class CoreAgentMetadata(AgentMetadata):
    """Concrete immutable implementation of AgentMetadata."""

    _type: str
    _key: str
    _description: str

    def __init__(self, type: str, key: str, description: str = "") -> None:
        """Initialize the agent metadata."""
        self._type = type
        self._key = key
        self._description = description

    @property
    def type(self) -> str:
        """Defines the 'type' or category of the agent."""
        return self._type

    @property
    def key(self) -> str:
        """Defines the 'key' or identifier of the agent."""
        return self._key

    @property
    def description(self) -> str:
        """Defines the 'description' of the agent."""
        return self._description
