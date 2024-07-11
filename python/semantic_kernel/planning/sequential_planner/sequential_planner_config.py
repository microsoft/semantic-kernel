# Copyright (c) Microsoft. All rights reserved.

from typing import Callable, List, Optional


class SequentialPlannerConfig:
    def __init__(
        self,
        relevancy_threshold: Optional[float] = None,
        max_relevant_functions: int = 100,
        excluded_skills: List[str] = None,
        excluded_functions: List[str] = None,
        included_functions: List[str] = None,
        max_tokens: int = 1024,
        allow_missing_functions: bool = False,
        get_available_functions_async: Callable = None,
        get_skill_function: Callable = None,
    ):
        self.relevancy_threshold: float = relevancy_threshold
        self.max_relevant_functions: int = max_relevant_functions
        self.excluded_skills: List[str] = excluded_skills or []
        self.excluded_functions: List[str] = excluded_functions or []
        self.included_functions: List[str] = included_functions or []
        self.max_tokens: int = max_tokens
        self.allow_missing_functions: bool = allow_missing_functions
        self.get_available_functions_async = get_available_functions_async
        self.get_skill_function = get_skill_function
