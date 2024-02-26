# Copyright (c) Microsoft. All rights reserved.
import sys
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_init_native_function_with_input_description():
    @kernel_function(description="Mock description", name="mock_function")
    def mock_function(input: Annotated[str, "input"], arguments: "KernelArguments") -> None:
        pass

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    assert native_function.function == mock_method
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "input"
    assert not native_function.parameters[0].default_value
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].required is True
    assert native_function.parameters[1].name == "arguments"
    assert native_function.parameters[1].description == ""
    assert not native_function.parameters[1].default_value
    assert native_function.parameters[1].type_ == "KernelArguments"
    assert native_function.parameters[1].required is True


def test_init_native_function_without_input_description():
    @kernel_function()
    def mock_function(arguments: "KernelArguments") -> None:
        pass

    mock_function.__kernel_function__ = True
    mock_function.__kernel_function_name__ = "mock_function_no_input_desc"
    mock_function.__kernel_function_description__ = "Mock description no input desc"
    mock_function.__kernel_function_context_parameters__ = [
        {
            "name": "arguments",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
            "required": True,
        }
    ]

    mock_method = mock_function

    native_function = KernelFunction.from_native_method(mock_method, "MockPlugin")

    assert native_function.function == mock_method
    assert native_function.parameters[0].name == "arguments"
    assert native_function.parameters[0].description == "Param 1 description"
    assert native_function.parameters[0].default_value == "default_param1_value"
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].required is True


def test_init_native_function_from_kernel_function_decorator():
    @kernel_function(
        description="Test description",
        name="test_function",
    )
    def decorated_function(input: Annotated[Optional[str], "Test input description"] = "test_default_value") -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ == "Test description"
    assert decorated_function.__kernel_function_name__ == "test_function"

    native_function = KernelFunction.from_native_method(decorated_function, "MockPlugin")

    assert native_function.function == decorated_function
    assert native_function.parameters[0].name == "input"
    assert native_function.parameters[0].description == "Test input description"
    assert native_function.parameters[0].default_value == "test_default_value"
    assert native_function.parameters[0].type_ == "str"
    assert native_function.parameters[0].required is False


def test_init_native_function_from_kernel_function_decorator_defaults():
    @kernel_function()
    def decorated_function() -> None:
        pass

    assert decorated_function.__kernel_function__ is True
    assert decorated_function.__kernel_function_description__ is None
    assert decorated_function.__kernel_function_name__ == "decorated_function"

    native_function = KernelFunction.from_native_method(decorated_function, "MockPlugin")

    assert native_function.function == decorated_function
    assert len(native_function.parameters) == 0
