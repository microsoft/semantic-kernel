import pytest
import json

import semantic_kernel as sk
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.core_skills.planner_skill import PlannerSkill
from semantic_kernel.planning.plan import Plan


@pytest.fixture
def initialized_kernel() -> KernelBase:
    kernel = sk.KernelBuilder.create_kernel()

    # configure backend as Azure OpenAI
    model_id, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.config.add_azure_openai_completion_backend(
        "davinci-003", model_id, endpoint, api_key
    )

    # TODO: determine if we want to create a dependency on samples folder?
    skills_directory = "./samples/skills"
    _ = kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")
    return kernel


def test_function_can_be_imported(initialized_kernel: KernelBase):
    kernel = initialized_kernel
    planner = kernel.import_skill(PlannerSkill(kernel=kernel), "planner")
    assert kernel.skills.has_function("planner", "CreatePlan")


@pytest.mark.asyncio
async def test_can_create_plan_async(initialized_kernel: KernelBase):
    kernel = initialized_kernel
    planner = PlannerSkill(kernel=kernel)
    ask = "Tomorrow is Valentine's day. Come up with an excuse why you didn't get flowers."

    context = kernel.create_new_context()
    plan = await planner.create_plan_async(ask, context=context)

    plan_string = json.loads(plan.result)["plan_string"]

    assert "<goal>" in plan_string and "</goal>" in plan_string
    assert "<plan>" in plan_string and "</plan>" in plan_string
    assert "function.FunSkill.Excuses" in plan_string


@pytest.mark.asyncio
async def test_can_execute_plan_async(initialized_kernel: KernelBase):
    step = 1
    maxSteps = 10
    kernel = initialized_kernel
    planner = PlannerSkill(kernel=kernel)
    ask = "Tomorrow is Valentine's day. Come up with only an excuse for why you didn't get flowers."

    context = kernel.create_new_context()
    plan = await planner.create_plan_async(ask, context=context)
    while not context.variables.get(Plan.IS_COMPLETE_KEY)[1] and step < maxSteps:
        plan = await planner.execute_plan_async(plan)
