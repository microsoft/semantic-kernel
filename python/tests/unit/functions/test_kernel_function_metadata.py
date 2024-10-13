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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    function_metadata_2 = KernelParameterMetadata(
        name="function2", description="Semantic function", default_value=""
    )
=======
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    function_metadata_2 = KernelParameterMetadata(
        name="function2", description="Semantic function", default_value=""
    )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    function_metadata_2 = KernelParameterMetadata(
        name="function2", description="Semantic function", default_value=""
    )
=======
    function_metadata_2 = KernelParameterMetadata(name="function2", description="Semantic function", default_value="")
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert function_metadata_1 != function_metadata_2
