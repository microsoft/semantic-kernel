# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.exceptions.function_exceptions import FunctionInvalidNameError
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


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

    def mock_function(input: str) -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_parameters__ = [
        {
            "name": "input",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]
    mock_function.__kernel_function_return_description__ = ""
    mock_function.__kernel_function_return_required__ = True
    mock_function.__kernel_function_return_type__ = "None"

    mock_method = mock_function

    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

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

    def mock_function(input: str) -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]
    mock_function.__kernel_function_return_description__ = ""
    mock_function.__kernel_function_return_required__ = True
    mock_function.__kernel_function_return_type__ = "None"

    mock_method = mock_function

    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

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


def test_default_kernel_plugin_construction_with_prompt_function():
    req_settings = PromptExecutionSettings(extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8})

    prompt = "Use this input: {{$request}}"

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
        ],
        execution_settings={"default": req_settings},
    )

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_function"
    semantic_function = KernelFunction.from_prompt(
        prompt=prompt,
        prompt_template_config=prompt_template_config,
        plugin_name=expected_plugin_name,
        function_name=expected_function_name,
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
    req_settings = PromptExecutionSettings(extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8})

    prompt = "Use this input: {{$request}}"

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
        ],
        execution_settings={"default": req_settings},
    )

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_function"
    semantic_function = KernelFunction.from_prompt(
        prompt=prompt,
        prompt_template_config=prompt_template_config,
        plugin_name=expected_plugin_name,
        function_name=expected_function_name,
    )

    # Construct a nativate function
    def mock_function(input: str) -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_native_function"
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]
    mock_function.__kernel_function_return_description__ = ""
    mock_function.__kernel_function_return_required__ = True
    mock_function.__kernel_function_return_type__ = "None"

    mock_method = mock_function

    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

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
    req_settings = PromptExecutionSettings(extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8})

    prompt = "Use this input: {{$request}}"

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
        ],
        execution_settings={"default": req_settings},
    )

    expected_plugin_name = "test_plugin"
    expected_function_name = "mock_function"
    semantic_function = KernelFunction.from_prompt(
        prompt=prompt,
        prompt_template_config=prompt_template_config,
        plugin_name=expected_plugin_name,
        function_name=expected_function_name,
    )

    # Construct a nativate function
    def mock_function(input: str) -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = expected_function_name
    mock_function.__kernel_function_description__ = "Mock description"
    mock_function.__kernel_function_input_description__ = "Mock input description"
    mock_function.__kernel_function_input_default_value__ = "default_input_value"
    mock_function.__kernel_function_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]
    mock_function.__kernel_function_return_description__ = ""
    mock_function.__kernel_function_return_required__ = True
    mock_function.__kernel_function_return_type__ = "None"

    mock_method = mock_function
    native_function = KernelFunction.from_method(method=mock_method, plugin_name="MockPlugin")

    with pytest.raises(FunctionInvalidNameError):
        KernelPlugin(name=expected_plugin_name, functions=[semantic_function, native_function])
