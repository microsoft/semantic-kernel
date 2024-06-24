# Copyright (c) Microsoft. All rights reserved.

from typing import Callable, List, Optional


class SequentialPlannerConfig:
    def __init__(
        self,
        relevancy_threshold: Optional[float] = None,
        max_relevant_functions: int = 100,
        excluded_plugins: List[str] = None,
        excluded_functions: List[str] = None,
        included_functions: List[str] = None,
        max_tokens: int = 1024,
        allow_missing_functions: bool = False,
        get_available_functions: Callable = None,
        get_plugin_function: Callable = None,
    ):
        self.relevancy_threshold: float = relevancy_threshold
        self.max_relevant_functions: int = max_relevant_functions
        self.excluded_plugins: List[str] = excluded_plugins or []
        self.excluded_functions: List[str] = excluded_functions or []
        self.included_functions: List[str] = included_functions or []
        self.max_tokens: int = max_tokens
        self.allow_missing_functions: bool = allow_missing_functions
        self.get_available_functions = get_available_functions
        self.get_plugin_function = get_plugin_function
