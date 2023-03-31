import pytest

import semantic_kernel as sk
from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.core_skills.time_skill import TimeSkill
from semantic_kernel.planning import plan_runner
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext


@pytest.fixture
def init_kernel_with_core_skills():
    kernel = sk.KernelBuilder.create_kernel()
    # add skills
    kernel.import_skill(TextSkill(), "text")
    return kernel


@pytest.fixture
def plan_payload():
    return """
    <goal>
    Convert a string to uppercase.
    </goal>
    <plan>
        <function.text.uppercase input="hello world"/>
    </plan>
    """


@pytest.mark.asyncio
async def test_plan_runner_can_execute_plan(init_kernel_with_core_skills, plan_payload):
    kernel = init_kernel_with_core_skills
    # create planner instance
    planner = plan_runner.PlanRunner(kernel)

    # get new context from kernel
    context_variables = ContextVariables()
    context = SKContext(context_variables, None, None, None)

    # execute plan
    _ = await planner.execute_xml_plan_async(
        context, plan_payload, None
    )  # TODO: Better understand the default_step_executor parameter
