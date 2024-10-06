<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, AsyncIterable
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, Annotated, Any, Union

import pytest

from semantic_kernel.functions.kernel_function_decorator import (
    _process_signature,
    kernel_function,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
import sys
from typing import TYPE_CHECKING, AsyncIterable, Optional, Union

import pytest

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import _parse_annotation, kernel_function
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
class InputObject(KernelBaseModel):
    arg1: str
    arg2: int


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
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
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
class MiscClass:
    __test__ = False

    @kernel_function(description="description")
    def func_with_description(self, input):
        return input

    @kernel_function(description="description")
    def func_no_name(self, input):
        return input

    @kernel_function(description="description", name="my-name")
    def func_with_name(self, input):
        return input

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    @kernel_function
    def func_docstring_as_description(self, input):
        """Description."""
        return input

    @kernel_function
    def func_input_annotated(self, input: Annotated[str, "input description"]):
        return input

    @kernel_function
    def func_input_annotated_optional(
        self, input: Annotated[str | None, "input description"] = "test"
    ):
        return input

    @kernel_function
    def func_input_optional(self, input: str | None = "test"):
        return input

    @kernel_function
    def func_return_type(self, input: str) -> str:
        return input

    @kernel_function
    def func_return_type_optional(self, input: str) -> str | None:
        return input

    @kernel_function
    def func_return_type_annotated(self, input: str) -> Annotated[str, "test return"]:
        return input

    @kernel_function
    def func_return_type_streaming(self, input: str) -> Annotated[AsyncGenerator[str, Any], "test return"]:  # type: ignore
        yield input

    @kernel_function
    def func_input_object(self, input: InputObject):
        return input

    @kernel_function
    def func_input_object_optional(self, input: InputObject | None = None):
        return input

    @kernel_function
    def func_input_object_annotated(
        self, input: Annotated[InputObject, "input description"]
    ):
        return input

    @kernel_function
    def func_input_object_annotated_optional(
        self, input: Annotated[InputObject | None, "input description"] = None
    ):
        return input

    @kernel_function
    def func_input_object_union(self, input: InputObject | str):
        return input

    @kernel_function
    def func_no_typing(self, input):
        return input

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
    @kernel_function()
    def func_docstring_as_description(self, input):
        """description"""
        return input

    @kernel_function()
    def func_input_annotated(self, input: Annotated[str, "input description"]):
        return input

    @kernel_function()
    def func_input_annotated_optional(self, input: Annotated[Optional[str], "input description"] = "test"):
        return input

    @kernel_function()
    def func_input_optional(self, input: Optional[str] = "test"):
        return input

    @kernel_function()
    def func_return_type(self, input: str) -> str:
        return input

    @kernel_function()
    def func_return_type_optional(self, input: str) -> Optional[str]:
        return input

    @kernel_function()
    def func_return_type_annotated(self, input: str) -> Annotated[str, "test return"]:
        return input

    @kernel_function()
    def func_return_type_streaming(self, input: str) -> Annotated[AsyncIterable[str], "test return"]:
        yield input

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

def test_func_name_as_name():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_with_description")
    assert my_func.__kernel_function_name__ == "func_with_description"


def test_description():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_with_description")
    assert my_func.__kernel_function_description__ == "description"


def test_kernel_function_name_not_specified():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_no_name")
    assert my_func.__kernel_function_name__ == "func_no_name"


def test_kernel_function_with_name_specified():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_with_name")
    assert my_func.__kernel_function_name__ == "my-name"


def test_kernel_function_docstring_as_description():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_docstring_as_description")
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    assert my_func.__kernel_function_description__ == "Description."
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert my_func.__kernel_function_description__ == "Description."
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    assert my_func.__kernel_function_description__ == "Description."
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert my_func.__kernel_function_description__ == "Description."
=======
    assert my_func.__kernel_function_description__ == "description"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes


def test_kernel_function_param_annotated():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_annotated")
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    assert (
        my_func.__kernel_function_parameters__[0]["description"] == "input description"
    )
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    assert my_func.__kernel_function_context_parameters__[0]["description"] == "input description"
    assert my_func.__kernel_function_context_parameters__[0]["type"] == "str"
    assert my_func.__kernel_function_context_parameters__[0]["required"]
    assert my_func.__kernel_function_context_parameters__[0]["default_value"] is None
    assert my_func.__kernel_function_context_parameters__[0]["name"] == "input"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes


def test_kernel_function_param_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_optional")
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    assert my_func.__kernel_function_context_parameters__[0]["description"] == ""
    assert my_func.__kernel_function_context_parameters__[0]["type"] == "str"
    assert not my_func.__kernel_function_context_parameters__[0]["required"]
    assert my_func.__kernel_function_context_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_context_parameters__[0]["name"] == "input"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes


def test_kernel_function_param_annotated_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_annotated_optional")
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    assert (
        my_func.__kernel_function_parameters__[0]["description"] == "input description"
    )
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    assert my_func.__kernel_function_context_parameters__[0]["description"] == "input description"
    assert my_func.__kernel_function_context_parameters__[0]["type"] == "str"
    assert not my_func.__kernel_function_context_parameters__[0]["required"]
    assert my_func.__kernel_function_context_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_context_parameters__[0]["name"] == "input"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes


def test_kernel_function_return_type():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_return_type")
    assert my_func.__kernel_function_return_type__ == "str"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    assert my_func.__kernel_function_return_description__ == ""
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    assert my_func.__kernel_function_return_required__
    assert not my_func.__kernel_function_streaming__


def test_kernel_function_return_type_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_return_type_optional")
    assert my_func.__kernel_function_return_type__ == "str"
    assert my_func.__kernel_function_return_description__ == ""
    assert not my_func.__kernel_function_return_required__
    assert not my_func.__kernel_function_streaming__


def test_kernel_function_return_type_annotated():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_return_type_annotated")
    assert my_func.__kernel_function_return_type__ == "str"
    assert my_func.__kernel_function_return_description__ == "test return"
    assert my_func.__kernel_function_return_required__
    assert not my_func.__kernel_function_streaming__


def test_kernel_function_return_type_streaming():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_return_type_streaming")
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    assert my_func.__kernel_function_return_type__ in ("str, Any", "str, typing.Any")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert my_func.__kernel_function_return_type__ in ("str, Any", "str, typing.Any")
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    assert my_func.__kernel_function_return_type__ in ("str, Any", "str, typing.Any")
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert my_func.__kernel_function_return_type__ in ("str, Any", "str, typing.Any")
=======
    assert my_func.__kernel_function_return_type__ == "str"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    assert my_func.__kernel_function_return_description__ == "test return"
    assert my_func.__kernel_function_return_required__
    assert my_func.__kernel_function_streaming__


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
def test_kernel_function_input_object():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object")
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
    assert my_func.__kernel_function_parameters__[0]["type_object"] == InputObject


def test_kernel_function_input_object_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object_optional")
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
    assert my_func.__kernel_function_parameters__[0]["type_object"] == InputObject


def test_kernel_function_input_object_annotated():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object_annotated")
    assert (
        my_func.__kernel_function_parameters__[0]["description"] == "input description"
    )
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
    assert my_func.__kernel_function_parameters__[0]["type_object"] == InputObject


def test_kernel_function_input_object_annotated_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object_annotated_optional")
    assert (
        my_func.__kernel_function_parameters__[0]["description"] == "input description"
    )
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
    assert my_func.__kernel_function_parameters__[0]["type_object"] == InputObject


def test_kernel_function_input_object_union():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object_union")
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject, str"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"


def test_kernel_function_no_typing():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_no_typing")
    assert my_func.__kernel_function_parameters__[0]["type_"] == "Any"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"


@pytest.mark.parametrize(
    ("name", "annotation", "description", "type_", "is_required"),
    [
        ("anno_str", Annotated[str, "test"], "test", "str", True),
        ("anno_opt_str", Annotated[str | None, "test"], "test", "str", False),
        ("anno_iter_str", Annotated[AsyncIterable[str], "test"], "test", "str", True),
        (
            "anno_opt_str_int",
            Annotated[str | int | None, "test"],
            "test",
            "str, int",
            False,
        ),
        ("str", str, None, "str", True),
        (
            "union",
            Union[str, int, float, "KernelArguments"],
            None,
            "str, int, float, KernelArguments",
            True,
        ),
        (
            "new_union",
            "str | int | float | KernelArguments",
            None,
            "str, int, float, KernelArguments",
            True,
        ),
        ("opt_str", str | None, None, "str", False),
        ("list_str", list[str], None, "list[str]", True),
        ("dict_str", dict[str, str], None, "dict[str, str]", True),
        ("list_str_opt", list[str] | None, None, "list[str]", False),
        (
            "anno_dict_str",
            Annotated[dict[str, str], "description"],
            "description",
            "dict[str, str]",
            True,
        ),
        (
            "anno_opt_dict_str",
            Annotated[dict | str | None, "description"],
            "description",
            "dict, str",
            False,
        ),
    ],
)
def test_annotation_parsing(name, annotation, description, type_, is_required):
    param = Parameter(
        name=name,
        annotation=annotation,
        default=Parameter.empty,
        kind=Parameter.POSITIONAL_OR_KEYWORD,
    )
    func_sig = Signature(parameters=[param])

    annotations = _process_signature(func_sig)

    assert len(annotations) == 1
    annotation_dict = annotations[0]

    assert description == annotation_dict.get("description")
    assert type_ == annotation_dict["type_"]
    assert is_required == annotation_dict["is_required"]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
@pytest.mark.parametrize(
    ("annotation", "description", "type_", "required"),
    [
        (Annotated[str, "test"], "test", "str", True),
        (Annotated[Optional[str], "test"], "test", "str", False),
        (Annotated[AsyncIterable[str], "test"], "test", "str", True),
        (Annotated[Optional[Union[str, int]], "test"], "test", "str, int", False),
        (str, "", "str", True),
        (Union[str, int, float, "KernelArguments"], "", "str, int, float, KernelArguments", True),
    ],
)
def test_annotation_parsing(annotation, description, type_, required):
    out_description, out_type_, out_required = _parse_annotation(annotation)

    assert out_description == description
    assert out_type_ == type_
    assert out_required == required
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
