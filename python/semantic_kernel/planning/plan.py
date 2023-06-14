import json
import regex
from typing import Any, List, Union, Optional
from python.semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.connectors.ai import CompleteRequestSettings


class Plan(SKFunctionBase):
    state: ContextVariables
    steps: List["Plan"]
    parameters: ContextVariables
    outputs: List[str]
    has_next_step: bool
    next_step_index: int
    name: str
    description: str
    is_semantic: bool
    is_sensitive: bool
    trust_service_instance: bool
    request_settings: CompleteRequestSettings

    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        next_step_index: int,
        state: ContextVariables,
        parameters: ContextVariables,
        outputs: List[str],
        steps: List["Plan"],
    ) -> None:
        self.name = name
        self.skill_name = skill_name
        self.description = description
        self.next_step_index = next_step_index
        self.state = state
        self.parameters = parameters
        self.outputs = outputs
        self.steps = steps

    def to_json(self, indented: Optional[bool] = False) -> str:
        return json.dumps(self.__dict__, indent=4 if indented else None)

    def from_json(self, json: Any, context: Optional[SKContext] = None) -> "Plan":
        # Filter out good JSON from the input in case additional text is present
        json_regex = r"\{(?:[^{}]|(?R))*\}"
        plan_string = regex.search(json_regex, json).group()
        new_plan = Plan() ## TODO: Fix this
        new_plan.__dict__ = json.loads(plan_string)

        if context is None:
            new_plan = self.set_available_functions(plan, context)

        return new_plan
    
    def set_available_functions(self, plan: "Plan", context: SKContext) -> "Plan":
        if len(plan.steps) == 0:
            if context.skills is None:
                raise KernelException(
                    KernelException.ErrorCodes.SkillCollectionNotSet,
                    "Skill collection not found in the context")
            try:
                skillFunction = context.skills.get_function(plan.skill_name, plan.name)
                plan.set_function(skillFunction)
            except:
                pass
        else:
            for step in plan.steps:
                step = self.set_available_functions(step, context)

        return plan
    


    # def __init__(self, goal, prompt, plan):
    #     self.state = ContextVariables()
    #     self.steps = []
    #     self.parameters = ContextVariables()
    #     self.outputs = []
    #     self.has_next_step = False
    #     self.next_step_index = 0
    #     self.name = ""
    #     self.description = ""
    #     self.is_semantic = False
    #     self.is_sensitive = False
    #     self.trust_service_instance = False
    #     self.request_settings = None


    #     self.goal = goal
    #     self.prompt = prompt
    #     self.generated_plan = plan
