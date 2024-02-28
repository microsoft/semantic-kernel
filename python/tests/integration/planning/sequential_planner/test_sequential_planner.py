# Copyright (c) Microsoft. All rights reserved.

import time

import pytest

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.exceptions import PlannerException
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners import SequentialPlanner
from semantic_kernel.planners.sequential_planner.sequential_planner_config import SequentialPlannerConfig
from tests.integration.fakes.email_plugin_fake import EmailPluginFake
from tests.integration.fakes.fun_plugin_fake import FunPluginFake
from tests.integration.fakes.writer_plugin_fake import WriterPluginFake


async def retry(func, retries=3):
    min_delay = 2
    max_delay = 7
    for i in range(retries):
        try:
            result = await func()
            return result
        except Exception:
            if i == retries - 1:  # Last retry
                raise
            time.sleep(max(min(i, max_delay), min_delay))


def initialize_kernel(get_aoai_config, use_embeddings=False, use_chat_model=False):
    _, api_key, endpoint = get_aoai_config

    kernel = Kernel()
    if use_chat_model:
        kernel.add_service(
            sk_oai.AzureChatCompletion(
                service_id="chat_completion",
                deployment_name="gpt-35-turbo-0613",
                endpoint=endpoint,
                api_key=api_key,
            ),
        )
    else:
        kernel.add_service(
            sk_oai.AzureTextCompletion(
                service_id="text_completion",
                deployment_name="gpt-35-turbo-instruct",
                endpoint=endpoint,
                api_key=api_key,
            ),
        )

    if use_embeddings:
        kernel.add_service(
            sk_oai.AzureTextEmbedding(
                service_id="text_embedding",
                deployment_name="text-embedding-ada-002",
                endpoint=endpoint,
                api_key=api_key,
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
async def test_create_plan_function_flow(get_aoai_config, use_chat_model, prompt, expected_function, expected_plugin):
    # Arrange
    service_id = "chat_completion" if use_chat_model else "text_completion"

    kernel = initialize_kernel(get_aoai_config, False, use_chat_model)
    kernel.import_plugin_from_object(EmailPluginFake(), "email_plugin_fake")
    kernel.import_plugin_from_object(FunPluginFake(), "fun_plugin_fake")

    planner = SequentialPlanner(kernel, service_id=service_id)

    # Act
    plan = await planner.create_plan(prompt)

    # Assert
    assert any(step.name == expected_function and step.plugin_name == expected_plugin for step in plan._steps)


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
    raises=PlannerException,
    reason="Test is known to occasionally produce unexpected results.",
)
async def test_create_plan_with_defaults(get_aoai_config, prompt, expected_function, expected_plugin, expected_default):
    # Arrange
    kernel = initialize_kernel(get_aoai_config)
    kernel.import_plugin_from_object(EmailPluginFake(), "email_plugin_fake")
    kernel.import_plugin_from_object(WriterPluginFake(), "WriterPlugin")

    planner = SequentialPlanner(kernel, service_id="text_completion")

    # Act
    plan = await retry(lambda: planner.create_plan(prompt))

    # Assert
    assert any(
        step.name == expected_function
        and step.plugin_name == expected_plugin
        and step.parameters["endMarker"] == expected_default
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
    raises=PlannerException,
    reason="Test is known to occasionally produce unexpected results.",
)
async def test_create_plan_goal_relevant(get_aoai_config, prompt, expected_function, expected_plugin):
    # Arrange
    kernel = initialize_kernel(get_aoai_config, use_embeddings=True)
    kernel.import_plugin_from_object(EmailPluginFake(), "email_plugin_fake")
    kernel.import_plugin_from_object(FunPluginFake(), "fun_plugin_fake")
    kernel.import_plugin_from_object(WriterPluginFake(), "writer_plugin_fake")

    planner = SequentialPlanner(
        kernel,
        service_id="text_completion",
        config=SequentialPlannerConfig(relevancy_threshold=0.65, max_relevant_functions=30),
    )

    # Act
    plan = await retry(lambda: planner.create_plan(prompt))

    # Assert
    assert any(step.name == expected_function and step.plugin_name == expected_plugin for step in plan._steps)
