from typing import Any


class Plan:
    # The goal that wants to be achieved
    goal: str

    # The prompt to be used to generate the plan
    prompt: str

    # The generated plan that consists of a list of steps to complete the goal
    generated_plan: Any

    def __init__(self, goal, prompt, plan):
        self.goal = goal
        self.prompt = prompt
        self.generated_plan = plan
