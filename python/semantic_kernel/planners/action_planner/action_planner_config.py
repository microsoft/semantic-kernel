# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations


class ActionPlannerConfig:
    def __init__(
        self,
        excluded_plugins: list[str] | None = None,
        excluded_functions: list[str] | None = None,
        max_tokens: int = 1024,
    ):
        self.excluded_plugins: list[str] = excluded_plugins or []
        self.excluded_functions: list[str] = excluded_functions or []
        self.max_tokens: int = max_tokens
