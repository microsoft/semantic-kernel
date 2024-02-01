# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

import pytest

from semantic_kernel.orchestration.kernel_function import KernelFunction
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import PromptTemplateConfig
from semantic_kernel.semantic_functions.semantic_function_config import SemanticFunctionConfig
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext


def test_throws_for_missing_name():
    with pytest.raises(TypeError):
        KernelPlugin(description="A unit test plugin")


def test_default_kernel_plugin_construction_with_no_functions():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"
    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description


def test_default_kernel_plugin_construction_with_native_functions():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    def mock_function(input: str, context: "KernelContext") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[native_function]
    )
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"] == native_function


def test_default_kernel_plugin_exposes_the_native_function_it_contains():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    def mock_function(input: str, context: "KernelContext") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[native_function]
    )
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"] == native_function

    for func in [native_function]:
        assert func.name in plugin
        assert plugin[func.name] == func


def test_default_kernel_plugin_construction_with_semantic_function():
    prompt_config = PromptTemplateConfig.from_execution_settings(max_tokens=2000, temperature=0.7, top_p=0.8)
    prompt_template = ChatPromptTemplate("{{$user_input}}", PromptTemplateEngine(), prompt_config)
    function_config = SemanticFunctionConfig(prompt_config, prompt_template)

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_function"
    semantic_function = KernelFunction.from_semantic_config(
        plugin_name=expected_plugin_name, function_name=expected_function_name, function_config=function_config
    )

    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[semantic_function]
    )

    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"] == semantic_function


def test_default_kernel_plugin_construction_with_both_function_types():
    # Construct a semantic function
    prompt_config = PromptTemplateConfig.from_execution_settings(max_tokens=2000, temperature=0.7, top_p=0.8)
    prompt_template = ChatPromptTemplate("{{$user_input}}", PromptTemplateEngine(), prompt_config)
    function_config = SemanticFunctionConfig(prompt_config, prompt_template)

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_semantic_function"
    semantic_function = KernelFunction.from_semantic_config(
        plugin_name=expected_plugin_name, function_name=expected_function_name, function_config=function_config
    )

    # Construct a nativate function
    def mock_function(input: str, context: "KernelContext") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_native_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    # Add both types to the default kernel plugin
    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(
        name=expected_plugin_name,
        description=expected_plugin_description,
        functions=[semantic_function, native_function],
    )

    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 2

    for func in [semantic_function, native_function]:
        assert func.name in plugin
        assert plugin[func.name] == func


def test_default_kernel_plugin_construction_with_same_function_names_throws():
    # Construct a semantic function
    prompt_config = PromptTemplateConfig.from_execution_settings(max_tokens=2000, temperature=0.7, top_p=0.8)
    prompt_template = ChatPromptTemplate("{{$user_input}}", PromptTemplateEngine(), prompt_config)
    function_config = SemanticFunctionConfig(prompt_config, prompt_template)

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_function"
    semantic_function = KernelFunction.from_semantic_config(
        plugin_name=expected_plugin_name, function_name=expected_function_name, function_config=function_config
    )

    # Construct a nativate function
    def mock_function(input: str, context: "KernelContext") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = expected_function_name
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]

    mock_method = mock_function
    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    with pytest.raises(ValueError):
        KernelPlugin(name=expected_plugin_name, functions=[semantic_function, native_function])
