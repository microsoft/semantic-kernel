# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.planners.planner_extensions import PlannerFunctionExtension, PlannerKernelExtension
from semantic_kernel.planners.planner_options import PlannerOptions


@pytest.fixture
def sample_function_metadata():
    return KernelFunctionMetadata(
        name="function",
        plugin_name="sample_plugin",
        description="A sample function",
        parameters=[
            KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
            KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
        ],
        is_prompt=False,
        is_asynchronous=True,
    )


@pytest.mark.parametrize(
    "function, expected_output",
    [
        (
            KernelFunctionMetadata(
                name="function",
                plugin_name="sample_plugin",
                description="A sample function",
                parameters=[
                    KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                    KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
                ],
                is_prompt=False,
                is_asynchronous=True,
            ),
            "sample_plugin-function:\n  description: A sample function\n  inputs:\n    - param1: Parameter 1\n  - param2: Parameter 2 (default value: default)",  # noqa: E501
        )
    ],
)
def test_to_manual_string(function, expected_output):
    result = PlannerFunctionExtension.to_manual_string(function)
    assert result == expected_output


@pytest.mark.parametrize(
    "function, expected_output",
    [
        (
            KernelFunctionMetadata(
                name="function",
                plugin_name="sample_plugin",
                description="A sample function",
                parameters=[
                    KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                    KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
                ],
                is_prompt=False,
                is_asynchronous=True,
            ),
            "function:\n  description: A sample function\n  inputs:\n    - param1: Parameter 1\n    - param2: Parameter 2",  # noqa: E501
        )
    ],
)
def test_to_embedding_string(function, expected_output):
    result = PlannerFunctionExtension.to_embedding_string(function)
    assert result == expected_output


@pytest.mark.asyncio
async def test_get_functions_manual():
    kernel = MagicMock()
    arguments = MagicMock()
    options = PlannerOptions(get_available_functions=None)

    kernel.get_list_of_function_metadata = MagicMock(
        return_value=[
            KernelFunctionMetadata(
                name="function",
                plugin_name="sample_plugin",
                description="A sample function",
                parameters=[
                    KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                    KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
                ],
                is_prompt=False,
                is_asynchronous=True,
            )
        ]
    )

    result = await PlannerKernelExtension.get_functions_manual(kernel, arguments, options)
    expected_output = "sample_plugin-function:\n  description: A sample function\n  inputs:\n    - param1: Parameter 1\n  - param2: Parameter 2 (default value: default)"  # noqa: E501
    assert result == expected_output


@pytest.mark.asyncio
async def test_get_functions_manual_with_custom_get_available_functions():
    kernel = MagicMock()
    arguments = MagicMock()
    options = PlannerOptions(get_available_functions=AsyncMock())

    # Mock get_available_functions method
    options.get_available_functions.return_value = [
        KernelFunctionMetadata(
            name="function",
            plugin_name="sample_plugin",
            description="A sample function",
            parameters=[
                KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
            ],
            is_prompt=False,
            is_asynchronous=True,
        )
    ]

    result = await PlannerKernelExtension.get_functions_manual(kernel, arguments, options)
    expected_output = "sample_plugin-function:\n  description: A sample function\n  inputs:\n    - param1: Parameter 1\n  - param2: Parameter 2 (default value: default)"  # noqa: E501
    assert result == expected_output


@pytest.mark.asyncio
async def test_get_available_functions():
    kernel = MagicMock()
    arguments = MagicMock()
    options = PlannerOptions(excluded_plugins=[], excluded_functions=[])

    # Mock get_list_of_function_metadata method
    kernel.get_list_of_function_metadata = MagicMock(
        return_value=[
            KernelFunctionMetadata(
                name="function",
                plugin_name="sample_plugin",
                description="A sample function",
                parameters=[
                    KernelParameterMetadata(name="param1", description="Parameter 1", default_value=None),
                    KernelParameterMetadata(name="param2", description="Parameter 2", default_value="default"),
                ],
                is_prompt=False,
                is_asynchronous=True,
            )
        ]
    )

    result = await PlannerKernelExtension.get_available_functions(kernel, arguments, options)
    assert len(result) == 1
    assert result[0].name == "function"
