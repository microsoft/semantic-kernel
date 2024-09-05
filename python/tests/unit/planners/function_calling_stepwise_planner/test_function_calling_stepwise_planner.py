# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.planner_exceptions import PlannerInvalidConfigurationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_result import (
    FunctionCallingStepwisePlannerResult,
    UserInteraction,
)


@pytest.fixture
def get_function_call_content():
    function_call_content = AsyncMock(spec=FunctionCallContent)
    function_call_content.id = "test"
    function_call_content.function_name = "function"
    function_call_content.plugin_name = "plugin"
    function_call_content.name = "USER_INTERACTION_SEND_FINAL_ANSWER"
    function_call_content.parse_arguments.return_value = {"answer": "Final answer"}
    function_call_content.ai_model_id = "test_model"
    function_call_content.metadata = KernelFunctionMetadata(
        name="function",
        plugin_name="plugin",
        description="A sample function",
        parameters=[
            KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
            KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
        ],
        is_prompt=False,
        is_asynchronous=True,
    )
    return function_call_content


@pytest.fixture
def get_kernel_function_metadata_list():
    [
        KernelFunctionMetadata(
            name="function",
            plugin_name="plugin",
            description="A sample function",
            parameters=[
                KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
            ],
            is_prompt=False,
            is_asynchronous=True,
        )
    ]


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


@pytest.mark.asyncio
async def test_invoke_with_function_call_content_and_processing(
    get_function_call_content, get_kernel_function_metadata_list
):
    kernel_mock = AsyncMock(spec=Kernel)
    question = "Test question"
    arguments = KernelArguments()

    options = FunctionCallingStepwisePlannerOptions(get_available_functions=AsyncMock(), max_iterations=1)
    options.get_available_functions.return_value = get_kernel_function_metadata_list

    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=options)

    chat_completion_mock = AsyncMock(spec=OpenAIChatCompletion)
    kernel_mock.get_service.return_value = chat_completion_mock

    planner._generate_plan = AsyncMock(return_value="generated plan")
    planner._build_chat_history_for_step = AsyncMock(return_value=AsyncMock(spec=ChatHistory))
    chat_completion_mock.instantiate_prompt_execution_settings.return_value = AsyncMock()

    other_function_call_content = AsyncMock(spec=FunctionCallContent)
    other_function_call_content.name = "SomeOtherFunction"

    chat_result = AsyncMock()
    chat_result.items = [other_function_call_content]
    chat_completion_mock.get_chat_message_contents.return_value = [chat_result]

    chat_completion_mock._process_function_call = AsyncMock(return_value=MagicMock(function_result="Function result"))

    with patch(
        "semantic_kernel.contents.function_result_content.FunctionResultContent.from_function_call_content_and_result",
        return_value=MagicMock(),
    ) as frc_mock:
        result = await planner.invoke(kernel_mock, question, arguments)

        assert isinstance(result, FunctionCallingStepwisePlannerResult)
        assert result.final_answer == ""
        assert result.iterations == options.max_iterations

        chat_completion_mock._process_function_call.assert_called_with(
            function_call=other_function_call_content,
            kernel=kernel_mock,
            chat_history=planner._build_chat_history_for_step.return_value,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_call_behavior=chat_completion_mock.instantiate_prompt_execution_settings.return_value.function_choice_behavior,
        )

        frc_mock.assert_called_with(function_call_content=other_function_call_content, result="Function result")


@pytest.mark.asyncio
async def test_invoke_with_function_call_content_and_processing_error(get_kernel_function_metadata_list):
    kernel_mock = AsyncMock(spec=Kernel)
    question = "Test question"
    arguments = KernelArguments()

    options = FunctionCallingStepwisePlannerOptions(get_available_functions=AsyncMock(), max_iterations=1)
    options.get_available_functions.return_value = get_kernel_function_metadata_list

    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=options)

    chat_completion_mock = AsyncMock(spec=OpenAIChatCompletion)
    kernel_mock.get_service.return_value = chat_completion_mock

    planner._generate_plan = AsyncMock(return_value="generated plan")
    planner._build_chat_history_for_step = AsyncMock(return_value=AsyncMock(spec=ChatHistory))
    chat_completion_mock.instantiate_prompt_execution_settings.return_value = AsyncMock()

    other_function_call_content = AsyncMock(spec=FunctionCallContent)
    other_function_call_content.name = "SomeOtherFunction"

    chat_result = AsyncMock()
    chat_result.items = [other_function_call_content]
    chat_completion_mock.get_chat_message_contents.return_value = [chat_result]

    chat_completion_mock._process_function_call.side_effect = Exception("Function call error")

    with patch(
        "semantic_kernel.contents.function_result_content.FunctionResultContent.from_function_call_content_and_result",
        return_value=MagicMock(),
    ) as frc_mock:
        result = await planner.invoke(kernel_mock, question, arguments)

        assert isinstance(result, FunctionCallingStepwisePlannerResult)
        assert result.final_answer == ""
        assert result.iterations == options.max_iterations

        chat_completion_mock._process_function_call.assert_called_with(
            function_call=other_function_call_content,
            kernel=kernel_mock,
            chat_history=planner._build_chat_history_for_step.return_value,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_call_behavior=chat_completion_mock.instantiate_prompt_execution_settings.return_value.function_choice_behavior,
        )

        frc_mock.assert_called_with(
            function_call_content=other_function_call_content,
            result=TextContent(text="An error occurred during planner invocation: Function call error"),
        )


@pytest.mark.asyncio
async def test_invoke_with_invalid_service_type():
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=None)
    kernel_mock = AsyncMock(spec=Kernel)
    kernel_mock.get_service.return_value = MagicMock()
    with pytest.raises(PlannerInvalidConfigurationError):
        await planner.invoke(kernel_mock, "test question")


@pytest.mark.asyncio
async def test_invoke_with_no_arguments():
    planner = FunctionCallingStepwisePlanner(service_id="test_service", options=None)
    kernel_mock = AsyncMock(spec=Kernel)
    question = "Test question"

    chat_completion_mock = AsyncMock(spec=OpenAIChatCompletion)
    kernel_mock.get_service.return_value = chat_completion_mock

    planner._generate_plan = AsyncMock(return_value="generated plan")
    planner._build_chat_history_for_step = AsyncMock(return_value=AsyncMock(spec=ChatHistory))
    chat_completion_mock.instantiate_prompt_execution_settings.return_value = AsyncMock()

    chat_completion_mock.get_chat_message_contents.return_value = [
        AsyncMock(items=[FunctionResultContent(text="Test result", id="test")])
    ]

    result = await planner.invoke(kernel_mock, question)

    assert isinstance(result, FunctionCallingStepwisePlannerResult)
    assert result.final_answer == ""
    assert result.iterations == planner.options.max_iterations


@patch("semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner.yaml.safe_load")
def test_create_config_from_yaml(mock_safe_load):
    mock_safe_load.return_value = {
        "template": "some template",
        "execution_settings": {"default": {"setting1": "value1"}},
    }

    kernel_mock = MagicMock(spec=Kernel)
    kernel_function_mock = MagicMock(spec=KernelFunction)
    kernel_mock.add_function.return_value = kernel_function_mock

    planner = FunctionCallingStepwisePlanner(service_id="test_service")

    planner.generate_plan_yaml = "some_yaml_content"

    DEFAULT_SERVICE_NAME = "default"

    with patch("semantic_kernel.const.DEFAULT_SERVICE_NAME", DEFAULT_SERVICE_NAME):
        result = planner._create_config_from_yaml(kernel_mock)
        mock_safe_load.assert_called_once_with("some_yaml_content")
        assert result == kernel_function_mock


def test_user_interaction():
    user_interaction = UserInteraction()
    assert user_interaction.send_final_answer("answer") == "Thanks"
