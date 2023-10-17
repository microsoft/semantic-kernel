from typing import List


class ActionPlannerConfig:
    def __init__(
        self,
        excluded_skills: List[str] = None,
        excluded_functions: List[str] = None,
        max_tokens: int = 1024,
    ):
        self.excluded_skills: List[str] = excluded_skills or []
        self.excluded_functions: List[str] = excluded_functions or []
        self.max_tokens: int = max_tokens
