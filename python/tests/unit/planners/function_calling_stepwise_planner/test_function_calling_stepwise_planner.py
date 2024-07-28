# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole
from semantic_kernel.exceptions.planner_exceptions import PlannerInvalidConfigurationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)


def test_initialization():
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=None)
    assert planner.service_id == "test_service"
    assert planner.options is not None


@pytest.mark.asyncio
async def test_invoke_with_empty_question_raises_error():
    planner = FunctionCallingStepwisePlanner(service_id="test-service", options=None)
    kernel_mock = AsyncMock(Kernel)
    with pytest.raises(PlannerInvalidConfigurationError):
        await planner.invoke(kernel_mock, "")


@pytest.mark.asyncio
async def test_get_initial_plan_callback_usage():
    fake_get_initial_plan = MagicMock(return_value="custom initial plan")
    options = FunctionCallingStepwisePlannerOptions(get_initial_plan=fake_get_initial_plan)
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=options)
    assert planner.generate_plan_yaml == "custom initial plan"
    fake_get_initial_plan.assert_called_once()


@pytest.mark.asyncio
async def test_get_step_prompt_callback_usage():
    fake_get_step_prompt = MagicMock(return_value="custom step prompt")
    options = FunctionCallingStepwisePlannerOptions(get_step_prompt=fake_get_step_prompt)
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=options)
    assert planner.step_prompt == "custom step prompt"
    fake_get_step_prompt.assert_called_once_with()


@pytest.mark.asyncio
async def test_build_chat_history_for_step():
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=None)
    kernel_mock = AsyncMock(Kernel)
    kernel_mock.get_service.return_value = AsyncMock()
    service_mock = AsyncMock(spec=OpenAIChatCompletion)
    arguments_mock = KernelArguments(goal="Test", initial_plan="Initial Plan")
    chat_history = await planner._build_chat_history_for_step(
        "goal", "initial_plan", kernel_mock, arguments_mock, service_mock
    )
    assert chat_history is not None
    assert chat_history[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_generate_plan():
    planner = FunctionCallingStepwisePlanner(service_id="test_service")

    kernel_mock = AsyncMock(Kernel)
    kernel_mock.get_service.return_value = AsyncMock()
    kernel_mock.get_list_of_function_metadata.return_value = []
    plugins_mock = MagicMock()
    kernel_mock.plugins = MagicMock(plugins=plugins_mock)

    mock_arguments = KernelArguments()

    with patch(
        "semantic_kernel.planners.function_calling_stepwise_planner.FunctionCallingStepwisePlanner._create_config_from_yaml",
        return_value=AsyncMock(spec=KernelFunction),
    ) as mock_create_yaml_config:
        question = "Why is the sky blue?"
        result = await planner._generate_plan(question, kernel_mock, mock_arguments)

        mock_create_yaml_config.assert_called_once_with(kernel_mock)
        assert result is not None


@pytest.mark.asyncio
async def test_invoke_with_no_configured_AI_service_raises_exception(kernel: Kernel):
    planner = FunctionCallingStepwisePlanner(service_id="test", options=None)
    with pytest.raises(PlannerInvalidConfigurationError):
        await planner.invoke(kernel, "test question")
