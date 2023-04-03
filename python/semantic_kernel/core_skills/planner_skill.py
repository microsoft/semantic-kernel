from typing import Set
from dataclasses import dataclass

from semantic_kernel.core_skills import constants
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel import SKContext
from semantic_kernel.kernel_extensions.inline_function_definitions import (
    create_semantic_function,
)
from semantic_kernel.skill_definition import sk_function


@dataclass
class Parameters:
    bucket_count = "bucketCount"
    bucket_label_prefix = "bucketLabelPrefix"
    relevancy_threshold = "relevancyThreshold"
    max_relevant_functions = "MaxRelevantFunctions"
    excluded_skills = "excludedSkills"
    excluded_functions = "excludedFunctions"
    included_functions = "includedFunctions"


class PlannerSkillConfig:
    def __init__(self):
        self.relevancy_threshold: float = None
        self.max_relevant_functions: int = 100
        self.excluded_skills: Set[str] = set([PlannerSkill.RESTRICTED_SKILL_NAME])
        self.excluded_functions: Set[str] = set(["CreatePlan", "ExecutePlan"])
        self.included_functions: Set[str] = set(["BucketOutputs"])
        self.included_functions = "includedFunctions"


class PlannerSkill:
    RESTRICTED_SKILL_NAME = "PlannerSkill_Excluded"

    def __init__(self, kernel: KernelBase, max_tokens: int = 1024):
        # TODO: implement function flow runner
        # self._functionFlowRunner = FunctionFlowRunner(kernel)

        # TODO: implement bucket function
        # self._bucketFunction = create_semantic_function(
        #     kernel=kernel,
        #     prompt_template=constants.BucketFunctionDefinition,
        #     skill_name=self.RESTRICTED_SKILL_NAME,
        #     maxTokens=maxTokens,
        #     temperature=0.0,
        # )

        self._function_flow_function = create_semantic_function(
            kernel=kernel,
            skill_name=self.RESTRICTED_SKILL_NAME,
            prompt_template=constants.FUNCTION_FLOW_FUNCTION_DEFINITION,
            description="Given a request or command or goal generate a step by step plan to "
            + "fulfill the request using functions. This ability is also known as decision making and function flow",
            max_tokens=max_tokens,
            temperature=0.0,
            stop_sequences=["<!--"],
        )

    @sk_function(
        name="CreatePlan",
        description="Create a plan using registered functions to accomplish a goal.",
    )
    def create_plan_async(self, goal: str, context: SKContext) -> str:
        pass
