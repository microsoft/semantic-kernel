# Copyright (c) Microsoft. All rights reserved.

import os
from collections.abc import Callable
from typing import Any

import pytest
from pytest import raises

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.openapi_plugin.openapi_parser import OpenApiParser
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.fixture
def mock_function() -> Callable[..., Any]:
    @kernel_function
    def mock_function(input: str) -> None:
        pass

    return mock_function


# region Init


def test_init_fail_no_name():
    with raises(TypeError):
        KernelPlugin(description="A unit test plugin")


def test_init_with_no_functions():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"
    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert not plugin.functions


def test_init_with_kernel_functions(mock_function):
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


def test_init_with_kernel_functions_list(mock_function):
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


def test_init_with_list_other_fail():
    with raises(ValueError):
        KernelPlugin(name="test_plugin", description="A unit test plugin", functions=["str"])


def test_init_with_other_fail():
    with raises(ValueError):
        KernelPlugin(name="test_plugin", description="A unit test plugin", functions="str")


def test_init_with_kernel_functions_dict(mock_function):
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


def test_init_with_callable_functions(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=mock_function)
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name


def test_init_with_callable_functions_list(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=[mock_function])
    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].plugin_name == expected_plugin_name


def test_init_with_kernel_plugin(mock_function):
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


def test_init_with_kernel_plugin_list(mock_function):
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


def test_init_exposes_the_native_function_it_contains(mock_function):
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


def test_init_with_prompt_function():
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


def test_init_with_both_function_types(mock_function):
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


def test_init_with_same_function_names(mock_function):
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


# region Dict-like methods


def test_set_item(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=expected_plugin_name)

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    plugin["mock_function"] = native_function

    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].metadata == native_function.metadata

    function = plugin["mock_function"]
    assert function.name == "mock_function"


def test_set(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=expected_plugin_name)

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    plugin.set("mock_function", native_function)

    assert plugin.name == expected_plugin_name
    assert plugin.description == expected_plugin_description
    assert len(plugin.functions) == 1
    assert plugin["mock_function"].metadata == native_function.metadata

    function = plugin.get("mock_function", None)
    assert function.name == "mock_function"
    function2 = plugin.get("mock_function2", None)
    assert function2 is None


def test_set_default(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=expected_plugin_name)
    native_function2 = KernelFunction.from_method(method=mock_function, plugin_name="other")

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    native_function == plugin.setdefault("mock_function", native_function)
    native_function == plugin.setdefault("mock_function", native_function2)

    assert len(plugin.functions) == 1

    with raises(ValueError):
        plugin.setdefault("mock_function2", None)


def test_update(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=expected_plugin_name)
    native_function2 = KernelFunction.from_method(method=mock_function, plugin_name="p2")
    native_function3 = KernelFunction.from_method(method=mock_function, plugin_name="p3")

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description)
    plugin.update(mock_function=native_function)
    assert len(plugin.functions) == 1

    plugin.update([native_function2])
    assert len(plugin.functions) == 1

    plugin.update({"mock_function": native_function3})
    assert len(plugin.functions) == 1

    plugin2 = KernelPlugin(name="p2", description="p2")
    plugin2.update(plugin)
    assert len(plugin2.functions) == 1

    plugin2.update([plugin])
    assert len(plugin2.functions) == 1

    with raises(TypeError):
        plugin.update(1)

    with raises(TypeError):
        plugin.update(1, 2)


def test_iter():
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    func1 = KernelFunctionFromPrompt("test1", expected_plugin_name, None, "test prompt")
    func2 = KernelFunctionFromPrompt("test1", expected_plugin_name, None, "test prompt")
    func3 = KernelFunctionFromPrompt("test1", expected_plugin_name, None, "test prompt")

    plugin = KernelPlugin(
        name=expected_plugin_name, description=expected_plugin_description, functions=[func1, func2, func3]
    )

    for func in plugin:
        assert func.metadata in [func1.metadata, func2.metadata, func3.metadata]


# region Properties


def test_get_functions_metadata(mock_function):
    expected_plugin_name = "test_plugin"
    expected_plugin_description = "A unit test plugin"

    native_function = KernelFunction.from_method(method=mock_function, plugin_name=expected_plugin_name)

    plugin = KernelPlugin(name=expected_plugin_name, description=expected_plugin_description, functions=native_function)
    metadatas = plugin.get_functions_metadata()
    assert len(metadatas) == 1
    assert metadatas[0] == native_function.metadata


# region Class Methods


def test_from_directory():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    plugin = KernelPlugin.from_directory("TestMixedPlugin", plugins_directory)
    assert plugin is not None
    assert len(plugin.functions) == 3
    assert plugin.name == "TestMixedPlugin"
    assert plugin.get("TestFunctionYaml") is not None
    assert plugin.get("echoAsync") is not None
    assert plugin.get("TestFunction") is not None


def test_from_directory_parent_directory_does_not_exist():
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins_fail")
    # path to plugins directory
    with raises(PluginInitializationError, match="Plugin directory does not exist"):
        KernelPlugin.from_directory("TestPlugin", plugins_directory)


def test_from_python_fail():
    with raises(PluginInitializationError, match="No class found in file"):
        KernelPlugin.from_python_file(
            "TestNativePluginNoClass",
            os.path.join(
                os.path.dirname(__file__),
                "../../assets",
                "test_native_plugins",
                "TestNativePluginNoClass",
                "native_function.py",
            ),
        )


def test_from_python_in_directory_fail():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_native_plugins")
    # path to plugins directory
    with raises(PluginInitializationError, match="No functions found in folder"):
        KernelPlugin.from_directory("TestNativePluginNoClass", plugins_directory)


def test_from_yaml_in_directory_fail():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    # path to plugins directory
    with raises(PluginInitializationError, match="No functions found in folder"):
        KernelPlugin.from_directory("TestFunctionBadYaml", plugins_directory)


def test_from_directory_other():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    # path to plugins directory
    with raises(PluginInitializationError, match="No functions found in folder"):
        KernelPlugin.from_directory("TestNoFunction", plugins_directory)


def test_from_directory_with_args():
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_native_plugins")
    # path to plugins directory
    plugin = KernelPlugin.from_directory(
        "TestNativePluginArgs",
        plugins_directory,
        class_init_arguments={"TestNativeEchoBotPlugin": {"static_input": "prefix "}},
    )
    result = plugin["echo"].method(text="test")
    assert result == "prefix test"


def test_from_object_function(decorated_native_function):
    plugin = KernelPlugin.from_object("TestPlugin", {"getLightStatusFunc": decorated_native_function})
    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("getLightStatus") is not None


def test_from_object_class(custom_plugin_class):
    plugin = KernelPlugin.from_object("TestPlugin", custom_plugin_class())
    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("getLightStatus") is not None


def test_from_openapi():
    openapi_spec_file = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )

    plugin = KernelPlugin.from_openapi(
        plugin_name="TestOpenAPIPlugin",
        openapi_document_path=openapi_spec_file,
    )
    assert plugin is not None
    assert plugin.name == "TestOpenAPIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None


def test_custom_spec_from_openapi():
    openapi_spec_file = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )

    parser = OpenApiParser()
    openapi_spec = parser.parse(openapi_spec_file)

    plugin = KernelPlugin.from_openapi(
        plugin_name="TestOpenAPIPlugin",
        openapi_parsed_spec=openapi_spec,
    )
    assert plugin is not None
    assert plugin.name == "TestOpenAPIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None


def test_from_openapi_missing_document_and_parsed_spec_throws():
    with raises(PluginInitializationError):
        KernelPlugin.from_openapi(
            plugin_name="TestOpenAPIPlugin",
            openapi_document_path=None,
        )


# region Static Methods
def test_parse_or_copy_fail():
    with raises(ValueError):
        KernelPlugin._parse_or_copy(None, "test")
