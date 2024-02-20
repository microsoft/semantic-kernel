# Copyright (c) Microsoft. All rights reserved.
import pytest

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_kernel_function_metadata():
    function_metadata = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        parameters=[],
        is_prompt=True,
        is_asynchronous=True,
    )
    assert function_metadata.is_prompt


def test_kernel_function_metadata_defaults():
    function_metadata = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    assert function_metadata.parameters == []
    assert function_metadata.is_asynchronous


def test_kernel_function_metadata_name_pattern_error():
    with pytest.raises(ValueError):
        KernelFunctionMetadata(
            name="-",
            plugin_name="plugin1",
            description="Semantic function",
            is_prompt=True,
        )


def test_kernel_function_metadata_name_empty_error():
    with pytest.raises(ValueError):
        KernelFunctionMetadata(
            name="",
            plugin_name="plugin1",
            description="Semantic function",
            is_prompt=True,
        )


def test_kernel_function_equals():
    function_metadata_1 = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    function_metadata_2 = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    assert function_metadata_1 == function_metadata_2


def test_kernel_function_not_equals():
    function_metadata_1 = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    function_metadata_2 = KernelFunctionMetadata(
        name="function2",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    assert function_metadata_1 != function_metadata_2


def test_kernel_function_not_equals_other_object():
    function_metadata_1 = KernelFunctionMetadata(
        name="function1",
        plugin_name="plugin1",
        description="Semantic function",
        is_prompt=True,
    )
    function_metadata_2 = KernelParameterMetadata(name="function2", description="Semantic function", default_value="")
    assert function_metadata_1 != function_metadata_2
