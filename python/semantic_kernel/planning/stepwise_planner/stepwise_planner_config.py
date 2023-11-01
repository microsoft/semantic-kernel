# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional


class StepwisePlannerConfig:
    def __init__(
        self,
        relevancy_threshold: Optional[float] = None,
        max_relevant_functions: int = 100,
        excluded_skills: List[str] = None,
        excluded_functions: List[str] = None,
        included_functions: List[str] = None,
        max_tokens: int = 1024,
        max_iterations: int = 100,
        min_iteration_time_ms: int = 0,
    ):
        self.relevancy_threshold: float = relevancy_threshold
        self.max_relevant_functions: int = max_relevant_functions
        self.excluded_skills: List[str] = excluded_skills or []
        self.excluded_functions: List[str] = excluded_functions or []
        self.included_functions: List[str] = included_functions or []
        self.max_tokens: int = max_tokens
        self.max_iterations: int = max_iterations
        self.min_iteration_time_ms: int = min_iteration_time_ms
