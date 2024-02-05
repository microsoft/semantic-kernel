# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.orchestration.kernel_function import KernelFunction
from semantic_kernel.plugin_definition.kernel_function_decorator import kernel_function

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext


def test_init_native_function_with_input_description():
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

    assert native_function.function == mock_method
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "Mock input description"
    assert native_function.parameters[0].default_value == "default_input_value"
    assert native_function.parameters[0].type_ == "string"
    assert native_function.parameters[0].required is False
    assert native_function.parameters[1].name == "param1"
    assert native_function.parameters[1].description == "Param 1 description"
    assert native_function.parameters[1].default_value == "default_param1_value"
    assert native_function.parameters[1].type_ == "string"
    assert native_function.parameters[1].required is False


def test_init_native_function_without_input_description():
    def mock_function(context: "KernelContext") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function_no_input_desc"
    mock_function.__kernel_function_description__ = "Mock description no input desc"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
            "required": True,
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    assert native_function.function == mock_method
    assert native_function.parameters[0].name == "param1"
    assert native_function.parameters[0].description == "Param 1 description"
    assert native_function.parameters[0].default_value == "default_param1_value"
    assert native_function.parameters[0].type_ == "string"
    assert native_function.parameters[0].required is True


def test_init_native_function_from_kernel_function_decorator():
    @kernel_function(
        description="Test description",
        name="test_function",
        input_description="Test input description",
        input_default_value="test_default_value",
    )
    def decorated_function() -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ == "Test description"
    assert decorated_function.__kernel_function_name__ == "test_function"
    assert decorated_function.__kernel_function_input_description__ == "Test input description"
    assert decorated_function.__kernel_function_input_default_value__ == "test_default_value"

    native_function = KernelFunction.from_native_method(decorated_function, "MockPlugin")

    assert native_function.function == decorated_function
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "Test input description"
    assert native_function.parameters[0].default_value == "test_default_value"
    assert native_function.parameters[0].type_ == "string"
    assert native_function.parameters[0].required is False


def test_init_native_function_from_kernel_function_decorator_defaults():
    @kernel_function()
    def decorated_function() -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ == ""
    assert decorated_function.__kernel_function_name__ == "decorated_function"
    assert decorated_function.__kernel_function_input_description__ == ""
    assert decorated_function.__kernel_function_input_default_value__ == ""

    native_function = KernelFunction.from_native_method(decorated_function, "MockPlugin")

    assert native_function.function == decorated_function
    assert len(native_function.parameters) == 0
