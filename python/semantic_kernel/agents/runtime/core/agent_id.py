# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Protocol, runtime_checkable

from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover

from semantic_kernel.agents.runtime.core.agent_type import AgentType
from semantic_kernel.agents.runtime.core.validation_utils import is_valid_agent_type


@experimental
@runtime_checkable
class AgentId(Protocol):
    """Defines the minimal interface an AgentId.

    It must fulfill a 'type' and a 'key' that identify the agent instance.
    """

    @property
    def type(self) -> str:
        """Defines the 'type' or category of the agent."""
        ...

    @property
    def key(self) -> str:
        """Defines the unique instance key within the agent type."""
        ...

    def __eq__(self, other: object) -> bool:
        """Equality check must differentiate between different IDs."""
        ...

    def __hash__(self) -> int:
        """Hash value needed to store AgentIds in sets/dicts."""
        ...

    def __str__(self) -> str:
        """String representation of the AgentId, e.g. 'type/key'."""
        ...


@experimental
class CoreAgentId(AgentId):
    """Core implementation of the AgentId protocol."""

    def __init__(self, type: str | AgentType, key: str) -> None:
        """Initialize the AgentId with the given type and key."""
        # If `type` is itself an AgentType, extract the string property.
        if isinstance(type, AgentType):
            type = type.type

        if not is_valid_agent_type(type):
            raise ValueError(
                rf"Invalid agent type: {type}. "
                r"Allowed values MUST match the regex: `^[\w\-\.]+\Z`"
            )

        self._type = type
        self._key = key

    @classmethod
    def from_str(cls, agent_id: str) -> Self:
        """Convert a string of the format ``type/key`` into a CoreAgentId."""
        items = agent_id.split("/", maxsplit=1)
        if len(items) != 2:
            raise ValueError(f"Invalid agent id: {agent_id}")
        t, k = items[0], items[1]
        return cls(t, k)

    @property
    def type(self) -> str:
        r"""The agent's 'type' (or category). Must match `^[\\w\\-\\.]+$`."""
        return self._type

    @property
    def key(self) -> str:
        """The agent's instance key, e.g. 'default' or a unique identifier."""
        return self._key

    def __eq__(self, value: object) -> bool:
        """Check if two AgentIds are equal by comparing 'type' and 'key'."""
        if not isinstance(value, AgentId):
            return False
        return (self.type == value.type) and (self.key == value.key)

    def __hash__(self) -> int:
        """Generate a hash so we can store AgentIds in sets/dicts."""
        return hash((self._type, self._key))

    def __str__(self) -> str:
        """Convert the AgentId to a user-friendly string."""
        return f"{self._type}/{self._key}"

    def __repr__(self) -> str:
        """Generate a detailed string representation."""
        return f'CoreAgentId(type="{self._type}", key="{self._key}")'
