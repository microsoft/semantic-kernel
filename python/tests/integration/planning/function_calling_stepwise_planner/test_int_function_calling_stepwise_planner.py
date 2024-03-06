# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
)
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_result import (
    FunctionCallingStepwisePlannerResult,
)
from semantic_kernel.utils.settings import openai_settings_from_dot_env


@pytest.mark.asyncio
async def test_can_execute_function_calling_stepwise_plan(get_oai_config):
    kernel = Kernel()

    api_key, _ = get_oai_config

    service_id = "planner"
    api_key, _ = openai_settings_from_dot_env()
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
        ),
    )

    kernel.import_plugin_from_object(MathPlugin(), "MathPlugin")

    questions = [
        "What is the current hour number, plus 5?",
    ]

    options = FunctionCallingStepwisePlannerOptions(
        max_iterations=5,
        max_tokens=1000,
    )

    planner = FunctionCallingStepwisePlanner(service_id=service_id, options=options)

    for question in questions:
        result = await planner.execute(kernel, question)
        print(f"Q: {question}\nA: {result.final_answer}\n")
        assert isinstance(result, FunctionCallingStepwisePlannerResult)
        assert 0 < len(result.final_answer) < 100
