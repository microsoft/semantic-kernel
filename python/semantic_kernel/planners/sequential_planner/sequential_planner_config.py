# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Callable

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated


@deprecated("Will be removed in a future version.")
class SequentialPlannerConfig:
    """Configuration for the SequentialPlanner."""

    def __init__(
        self,
        relevancy_threshold: float | None = None,
        max_relevant_functions: int = 100,
        excluded_plugins: list[str] | None = None,
        excluded_functions: list[str] | None = None,
        included_functions: list[str] | None = None,
        max_tokens: int = 1024,
        allow_missing_functions: bool = False,
        get_available_functions: Callable | None = None,
        get_plugin_function: Callable | None = None,
    ):
        """Initializes a new instance of the SequentialPlannerConfig class."""
        self.relevancy_threshold: float = relevancy_threshold
        self.max_relevant_functions: int = max_relevant_functions
        self.excluded_plugins: list[str] = excluded_plugins or []
        self.excluded_functions: list[str] = excluded_functions or []
        self.included_functions: list[str] = included_functions or []
        self.max_tokens: int = max_tokens
        self.allow_missing_functions: bool = allow_missing_functions
        self.get_available_functions = get_available_functions
        self.get_plugin_function = get_plugin_function
