# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.planner_exceptions import PlannerInvalidConfigurationError
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
async def test_execute_with_empty_question_raises_error():
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
    chat_history = await planner._build_chat_history_for_step("goal", "initial_plan", kernel_mock)
    assert chat_history is not None


@pytest.mark.asyncio
async def test_get_completion_with_functions():
    chat_completion_mock = AsyncMock(ChatCompletionClientBase)
    chat_history = ChatHistory()
    execution_settings = OpenAIChatPromptExecutionSettings()

    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=None)

    kernel_mock = AsyncMock(Kernel)
    kernel_mock.get_service.return_value = AsyncMock()

    kernel_mock.get_service.return_value = chat_completion_mock
    chat_completion_mock.complete_chat.return_value = AsyncMock()

    result = await planner._get_completion_with_functions(
        chat_history, kernel_mock, chat_completion_mock, execution_settings
    )

    chat_completion_mock.complete_chat.assert_called_once_with(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=kernel_mock,
    )
    assert result is not None


@pytest.mark.asyncio
async def test_generate_plan():
    planner = FunctionCallingStepwisePlanner(service_id="test_service")

    kernel_mock = AsyncMock(Kernel)
    kernel_mock.get_service.return_value = AsyncMock()

    with patch(
        "semantic_kernel.planners.function_calling_stepwise_planner.FunctionCallingStepwisePlanner._create_config_from_yaml",
        return_value=AsyncMock(spec=KernelFunction),
    ) as mock_create_yaml_config, patch(
        "semantic_kernel.planners.planner_extensions.PlannerKernelExtension.get_functions_manual",
        new=AsyncMock(),
    ) as mock_get_functions_manual:
        question = "Why is the sky blue?"
        result = await planner._generate_plan(question, kernel_mock)

        mock_create_yaml_config.assert_called_once_with(kernel_mock)
        mock_get_functions_manual.assert_awaited_once()
        assert result is not None
