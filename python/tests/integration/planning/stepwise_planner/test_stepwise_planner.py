# Copyright (c) Microsoft. All rights reserved.

import json
import os

import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.planning import StepwisePlanner
from semantic_kernel.planning.stepwise_planner.stepwise_planner_config import (
    StepwisePlannerConfig,
)
from semantic_kernel.plugin_definition import kernel_function, kernel_function_context_parameter


class TempWebSearchEnginePlugin:
    """
    TODO: replace this class with semantic_kernel.core_plugins.web_search_engine_plugin.WebSearchEnginePlugin

    SKFunction.describe() does not contains info for arguments.

    so that `query: str` is not shown in the function description,
    BUT this argument must be passed to planner to work appropriately.

    This function temporarily add `query` as parameter by using @sk_function_context_parameter.
    original file is here: semantic-kernel/python/semantic_kernel/core_plugins/web_search_engine_plugin.py
    """

    def __init__(self, connector) -> None:
        self._connector = connector

    @kernel_function(description="Performs a web search for a given query", name="searchAsync")
    @kernel_function_context_parameter(
        name="query",
        description="The search query",
    )
    async def search(self, query: str, context: KernelContext) -> str:
        query = query or context.variables.get("query")
        result = await self._connector.search(query, num_results=5, offset=0)
        return str(result)


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
            sk_oai.AzureChatCompletion(deployment_name="gpt-35-turbo", endpoint=endpoint, api_key=api_key),
        )
    else:
        kernel.add_text_completion_service(
            "text_completion",
            sk_oai.AzureChatCompletion(
                deployment_name="gpt-35-turbo",
                endpoint=endpoint,
                api_key=api_key,
            ),
        )

    if use_embeddings:
        kernel.add_text_embedding_generation_service(
            "text_embedding",
            sk_oai.AzureTextEmbedding(
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
            "What is the tallest mountain on Earth? How tall is it divided by 2?",
            "ExecutePlan",
            "StepwisePlanner",
        ),
        (
            True,
            "What is the tallest mountain on Earth? How tall is it divided by 2?",
            "ExecutePlan",
            "StepwisePlanner",
        ),
    ],
)
@pytest.mark.asyncio
async def test_can_create_stepwise_plan(
    get_aoai_config,
    get_bing_config,
    use_chat_model,
    prompt,
    expected_function,
    expected_plugin,
):
    # Arrange
    use_embeddings = False
    kernel = initialize_kernel(get_aoai_config, use_embeddings, use_chat_model)
    bing_connector = BingConnector(api_key=get_bing_config)
    web_search_engine_plugin = TempWebSearchEnginePlugin(bing_connector)
    kernel.import_plugin(web_search_engine_plugin, "WebSearch")
    kernel.import_plugin(TimePlugin(), "time")

    planner = StepwisePlanner(kernel, StepwisePlannerConfig(max_iterations=10, min_iteration_time_ms=1000))

    # Act
    plan = planner.create_plan(prompt)

    # Assert
    assert any(step.name == expected_function and step.plugin_name == expected_plugin for step in plan._steps)


@pytest.mark.parametrize(
    "use_chat_model, prompt",
    [
        (
            False,
            "What is the tallest mountain on Earth? How tall is it divided by 2?",
        )
    ],
)
@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test is known to occasionally produce unexpected results.",
)
async def test_can_execute_stepwise_plan(
    get_aoai_config,
    get_bing_config,
    use_chat_model,
    prompt,
):
    # Arrange
    use_embeddings = False
    kernel = initialize_kernel(get_aoai_config, use_embeddings, use_chat_model)
    bing_connector = BingConnector(api_key=get_bing_config)
    web_search_engine_plugin = TempWebSearchEnginePlugin(bing_connector)
    kernel.import_plugin(web_search_engine_plugin, "WebSearch")
    kernel.import_plugin(TimePlugin(), "time")
    kernel.import_plugin(MathPlugin(), "math")

    planner = StepwisePlanner(kernel, StepwisePlannerConfig(max_iterations=10, min_iteration_time_ms=1000))

    # Act
    plan = planner.create_plan(prompt)
    result = await plan.invoke_async()

    steps_taken_string = result.variables["steps_taken"]
    assert steps_taken_string is not None

    steps_taken = json.loads(steps_taken_string)
    assert steps_taken is not None and len(steps_taken) > 0

    assert (
        3 <= len(steps_taken) <= 10
    ), f"Actual: {len(steps_taken)}. Expected at least 3 steps and at most 10 steps to be taken."
