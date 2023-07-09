class SequentialPlannerConfig:
    def __init__(self):
        self.relevancy_threshold = None
        self.max_relevant_functions = 100
        self.excluded_skills = set()
        self.excluded_functions = set()
        self.included_functions = set()
        self.max_tokens = 1024
        self.allow_missing_functions = False
        self.get_available_functions_async = None
        self.get_skill_function = None
