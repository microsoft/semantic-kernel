# Copyright (c) Microsoft. All rights reserved.

import json
import os

import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_skills.time_skill import TimeSkill
from semantic_kernel.core_skills.web_search_engine_skill import WebSearchEngineSkill
from semantic_kernel.kernel import Kernel
from semantic_kernel.planning import StepwisePlanner
from semantic_kernel.planning.stepwise_planner.stepwise_planner_config import (
    StepwisePlannerConfig,
)


@pytest.fixture(scope="session")
def get_bing_config():
    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["Bing__ApiKey"]
    else:
        # Load credentials from .env file
        api_key = sk.bing_search_settings_from_dot_env()

    return api_key


def initialize_kernel(get_aoai_config, use_embeddings=False, use_chat_model=False):
    _, api_key, endpoint = get_aoai_config

    kernel = Kernel()
    if use_chat_model:
        kernel.add_chat_service(
            "chat_completion",
            sk_oai.AzureChatCompletion("gpt-35-turbo", endpoint, api_key),
        )
    else:
        kernel.add_text_completion_service(
            "text_completion",
            sk_oai.AzureChatCompletion("gpt-35-turbo", endpoint, api_key),
        )

    if use_embeddings:
        kernel.add_text_embedding_generation_service(
            "text_embedding",
            sk_oai.AzureTextEmbedding("text-embedding-ada-002", endpoint, api_key),
        )
    return kernel


# @pytest.mark.parametrize(
#     "use_chat_model, prompt, expected_function, expected_skill",
#     [
#         (
#             False,
#             "Who is the current president of the United States? What is his current age divided by 2",
#             "ExecutePlan",
#             "StepwisePlanner",
#         ),
#         (
#             True,
#             "Who is the current president of the United States? What is his current age divided by 2",
#             "ExecutePlan",
#             "StepwisePlanner",
#         ),
#     ],
# )
# @pytest.mark.asyncio
# async def test_can_create_stepwise_plan(
#     get_aoai_config,
#     get_bing_config,
#     use_chat_model,
#     prompt,
#     expected_function,
#     expected_skill,
# ):
#     # Arrange
#     use_embeddings = False
#     kernel = initialize_kernel(get_aoai_config, use_embeddings, use_chat_model)
#     bing_connector = BingConnector(api_key=get_bing_config)
#     web_search_engine_skill = WebSearchEngineSkill(bing_connector)
#     kernel.import_skill(web_search_engine_skill, "WebSearch")
#     kernel.import_skill(TimeSkill(), "time")

#     planner = StepwisePlanner(kernel, StepwisePlannerConfig(max_iterations=10))

#     # Act
#     plan = planner.create_plan(prompt)

#     # Assert
#     assert any(
#         step.name == expected_function and step.skill_name == expected_skill
#         for step in plan._steps
#     )


@pytest.mark.parametrize(
    "use_chat_model, prompt",
    [
        (
            False,
            "Who is the current president of the United States? What is his current age divided by 2",
        )
    ],
)
@pytest.mark.asyncio
async def test_can_create_stepwise_plan(
    get_aoai_config,
    get_bing_config,
    use_chat_model,
    prompt,
):
    # Arrange
    use_embeddings = False
    kernel = initialize_kernel(get_aoai_config, use_embeddings, use_chat_model)
    bing_connector = BingConnector(api_key=get_bing_config)
    web_search_engine_skill = WebSearchEngineSkill(bing_connector)
    kernel.import_skill(web_search_engine_skill, "WebSearch")
    kernel.import_skill(TimeSkill(), "time")

    planner = StepwisePlanner(kernel, StepwisePlannerConfig(max_iterations=10))

    # Act
    plan = planner.create_plan(prompt)
    result = await plan.invoke_async()

    assert "Biden" in result.result.lower()

    steps_taken_string = result.variables.get("steps_taken")
    assert steps_taken_string is not None

    steps_taken = json.loads(steps_taken_string)
    assert steps_taken is not None and len(steps_taken) > 0

    assert (
        3 <= len(steps_taken) <= 10
    ), f"Actual: {len(steps_taken)}. Expected at least 3 steps and at most 10 steps to be taken."


if __name__ == "__main__":
    pytest.main([__file__])
