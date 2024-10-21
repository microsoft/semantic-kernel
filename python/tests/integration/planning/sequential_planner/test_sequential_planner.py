# Copyright (c) Microsoft. All rights reserved.

import time

import pytest

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.exceptions import PlannerException
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners import SequentialPlanner
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
=======
from semantic_kernel.planners.planning_exception import PlanningException
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
from semantic_kernel.planners.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from tests.integration.fakes.email_plugin_fake import EmailPluginFake
from tests.integration.fakes.fun_plugin_fake import FunPluginFake
from tests.integration.fakes.writer_plugin_fake import WriterPluginFake


async def retry(func, retries=3):
    min_delay = 2
    max_delay = 7
    for i in range(retries):
        try:
            return await func()
        except Exception:
            if i == retries - 1:  # Last retry
                raise
            time.sleep(max(min(i, max_delay), min_delay))
    return None


def initialize_kernel(use_embeddings=False, use_chat_model=False):
    kernel = Kernel()
    if use_chat_model:
        kernel.add_service(
            sk_oai.AzureChatCompletion(
                service_id="chat_completion",
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
=======
                deployment_name="gpt-35-turbo-0613",
                endpoint=endpoint,
                api_key=api_key,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ),
        )
    else:
        kernel.add_service(
            sk_oai.AzureTextCompletion(
                service_id="text_completion",
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
=======
                deployment_name="gpt-35-turbo-instruct",
                endpoint=endpoint,
                api_key=api_key,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ),
        )

    if use_embeddings:
        kernel.add_service(
            sk_oai.AzureTextEmbedding(
                service_id="text_embedding",
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
=======
                deployment_name="text-embedding-ada-002",
                endpoint=endpoint,
                api_key=api_key,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ),
        )
    return kernel


@pytest.mark.parametrize(
    "use_chat_model, prompt, expected_function, expected_plugin",
    [
        (
            False,
            "Write a joke and send it in an e-mail to Kai.",
            "SendEmail",
            "email_plugin_fake",
        ),
        (
            True,
            "Write a joke and send it in an e-mail to Kai.",
            "SendEmail",
            "email_plugin_fake",
        ),
    ],
)
@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test is known to be blocked by Azure OpenAI content policy.",
)
async def test_create_plan_function_flow(
    use_chat_model, prompt, expected_function, expected_plugin
):
    # Arrange
    service_id = "chat_completion" if use_chat_model else "text_completion"
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

    kernel = initialize_kernel(False, use_chat_model)
    kernel.add_plugin(EmailPluginFake(), "email_plugin_fake")
    kernel.add_plugin(FunPluginFake(), "fun_plugin_fake")

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

<<<<<<< main
    kernel = initialize_kernel(False, use_chat_model)
    kernel.add_plugin(EmailPluginFake(), "email_plugin_fake")
    kernel.add_plugin(FunPluginFake(), "fun_plugin_fake")
=======
    kernel = initialize_kernel(get_aoai_config, False, use_chat_model)
    kernel.import_plugin(EmailPluginFake(), "email_plugin_fake")
    kernel.import_plugin(FunPluginFake(), "fun_plugin_fake")
>>>>>>> ms/small_fixes

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    planner = SequentialPlanner(kernel, service_id=service_id)

    # Act
    plan = await planner.create_plan(prompt)

    # Assert
    assert any(
        step.name == expected_function and step.plugin_name == expected_plugin
        for step in plan._steps
    )


@pytest.mark.parametrize(
    "prompt, expected_function, expected_plugin, expected_default",
    [
        (
            "Write a novel outline.",
            "NovelOutline",
            "WriterPlugin",
            "<!--===ENDPART===-->",
        )
    ],
)
@pytest.mark.asyncio
@pytest.mark.xfail(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    raises=PlannerException,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    raises=PlannerException,
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    raises=PlannerException,
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    raises=PlannerException,
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    raises=PlannerException,
=======
    raises=PlanningException,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    reason="Test is known to occasionally produce unexpected results.",
)
async def test_create_plan_with_defaults(
    prompt, expected_function, expected_plugin, expected_default
):
    # Arrange
    kernel = initialize_kernel()
    kernel.add_plugin(EmailPluginFake(), "email_plugin_fake")
    kernel.add_plugin(WriterPluginFake(), "WriterPlugin")

    planner = SequentialPlanner(kernel, service_id="text_completion")

    # Act
    plan = await retry(lambda: planner.create_plan(prompt))

    # Assert
    assert any(
        step.name == expected_function
        and step.plugin_name == expected_plugin
        and step.parameters.get("endMarker", expected_default) == expected_default
        for step in plan._steps
    )


@pytest.mark.parametrize(
    "prompt, expected_function, expected_plugin",
    [
        (
            "Write a poem or joke and send it in an e-mail to Kai.",
            "SendEmail",
            "email_plugin_fake",
        )
    ],
)
@pytest.mark.asyncio
@pytest.mark.xfail(
<<<<<<< main
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    raises=PlannerException,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    raises=PlannerException,
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    raises=PlannerException,
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    raises=PlannerException,
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    raises=PlannerException,
=======
    raises=PlanningException,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    reason="Test is known to occasionally produce unexpected results.",
=======
    reason="Test is known to be blocked by Azure OpenAI content policy.",
>>>>>>> upstream/main
)
async def test_create_plan_goal_relevant(prompt, expected_function, expected_plugin):
    # Arrange
    kernel = initialize_kernel(use_embeddings=True)
    kernel.add_plugin(EmailPluginFake(), "email_plugin_fake")
    kernel.add_plugin(FunPluginFake(), "fun_plugin_fake")
    kernel.add_plugin(WriterPluginFake(), "writer_plugin_fake")

    planner = SequentialPlanner(
        kernel,
        service_id="text_completion",
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        config=SequentialPlannerConfig(
            relevancy_threshold=0.65, max_relevant_functions=30
        ),
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        config=SequentialPlannerConfig(
            relevancy_threshold=0.65, max_relevant_functions=30
        ),
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        config=SequentialPlannerConfig(
            relevancy_threshold=0.65, max_relevant_functions=30
        ),
=======
        config=SequentialPlannerConfig(relevancy_threshold=0.65, max_relevant_functions=30),
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    )

    # Act
    plan = await retry(lambda: planner.create_plan(prompt))

    # Assert
    assert any(
        step.name == expected_function and step.plugin_name == expected_plugin
        for step in plan._steps
    )
