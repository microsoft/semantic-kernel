# Copyright (c) Microsoft. All rights reserved.


import os
from collections.abc import Callable
from typing import Any

import pytest

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_throws_for_missing_name():
    with pytest.raises(TypeError):
        KernelPlugin(description="A unit test plugin")


def test_plugin_construction_with_no_functions():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"
    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert not plugin.functions


@pytest.fixture
def mock_function() -> Callable[..., Any]:
    @kernel_function
    def mock_function(input: str) -> None:
        pass

    return mock_function


def test_plugin_construction_with_kernel_functions(mock_function):
    function_plugin_name = "MockPlugin"
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=function_plugin_name)

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=native_function)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name
    assert native_function.plugin_name == function_plugin_name


def test_plugin_construction_with_kernel_functions_list(mock_function):
    function_plugin_name = "MockPlugin"
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=function_plugin_name)

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[native_function]
    )
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name
    assert native_function.plugin_name == function_plugin_name


def test_plugin_construction_with_kernel_functions_dict(mock_function):
    function_plugin_name = "MockPlugin"
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=function_plugin_name)

    plugin = KernelPlugin(
        name=expected_plugin_name,
        description=expected_plugin_description,
        functions={native_function.name: native_function},
    )
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name
    assert native_function.plugin_name == function_plugin_name


def test_plugin_construction_with_callable_functions(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=mock_function)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name


def test_plugin_construction_with_callable_functions_list(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=[mock_function])
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name


def test_plugin_construction_with_kernel_plugin(mock_function):
    function_plugin_name = "MockPlugin"
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=function_plugin_name)
    first_plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=native_function
    )
    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=first_plugin)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name
    assert native_function.plugin_name == function_plugin_name


def test_plugin_construction_with_kernel_plugin_list(mock_function):
    function_plugin_name = "MockPlugin"
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=function_plugin_name)
    first_plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=native_function
    )
    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=[first_plugin])
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name
    assert native_function.plugin_name == function_plugin_name


def test_plugin_exposes_the_native_function_it_contains(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name="MockPlugin")

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[native_function]
    )
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].name == native_function.name


def test_plugin_construction_with_prompt_function():
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
    semantic_function = KernelFunctionFromPrompt(
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


def test_plugin_construction_with_both_function_types(mock_function):
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
    expected_function_name = "prompt_function"
    semantic_function = KernelFunction.from_prompt(
        prompt=prompt,
        prompt_template_config=prompt_template_config,
        plugin_name=expected_plugin_name,
        function_name=expected_function_name,
    )

    native_function = KernelFunctionFromMethod(method=mock_function, plugin_name="MockPlugin")

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
        assert plugin[func.name].name == func.name


def test_plugin_construction_with_same_function_names(mock_function):
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

    native_function = KernelFunctionFromMethod(method=mock_function, plugin_name="MockPlugin")

    plugin = KernelPlugin(name=expected_plugin_name, functions=[semantic_function, native_function])
    assert len(plugin.functions) == 1


def test_plugin_from_directory():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    # path to plugins directory
    plugin = KernelPlugin.from_directory("TestPlugin", plugins_directory)

    assert plugin is not None
    assert len(plugin.functions) == 2
    func = plugin.functions["TestFunction"]
    assert func is not None
    func_handlebars = plugin.functions["TestFunctionHandlebars"]
    assert func_handlebars is not None
