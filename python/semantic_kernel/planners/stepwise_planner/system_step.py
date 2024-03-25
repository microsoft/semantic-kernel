# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SystemStep:
    thought: str | None = None
    action: str | None = None
    action_variables: dict[str, str] | None = field(default_factory=dict)
    observation: str | None = None
    final_answer: str | None = None
    original_response: str | None = None
