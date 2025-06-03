# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
@runtime_checkable
class AgentType(Protocol):
    """Defines the minimal interface an AgentType."""

    @property
    def type(self) -> str:
        """Defines the 'type' or category of the agent."""
        ...


@experimental
@dataclass(eq=True, frozen=True)
class CoreAgentType:
    """Concrete immutable implementation of AgentType."""

    _type: str

    @property
    def type(self) -> str:
        """Defines the 'type' or category of the agent."""
        return self._type

    def __str__(self) -> str:
        """Return the string representation of the agent type."""
        return self._type
