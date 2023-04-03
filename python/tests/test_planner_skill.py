import pytest

import semantic_kernel as sk
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.core_skills.planner_skill import PlannerSkill
from semantic_kernel.kernel_extensions.import_semantic_skill_from_directory import (
    import_semantic_skill_from_directory,
)


@pytest.fixture
def initialized_kernel() -> KernelBase:
    kernel = sk.KernelBuilder.create_kernel()

    # configure backend as Azure OpenAI
    model_id, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.config.add_openai_completion_backend(
        "davinci-003", model_id, api_key, endpoint
    )

    # TODO: determine if we want to create a dependency on samples folder?
    skills_directory = "./samples/skills"
    _ = import_semantic_skill_from_directory(kernel, skills_directory, "FunSkill")
    return kernel


@pytest.mark.asyncio
async def test_can_create_plan(initialized_kernel: KernelBase):
    kernel = initialized_kernel
    planner = kernel.import_skill(PlannerSkill(kernel=kernel))

    ask = "Tomorrow is Valentine's day. Come up with an excuse why you didn't get flowers."
    base_plan = await kernel.run_on_str_async(ask, planner["CreatePlan"])
