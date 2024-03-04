import sys
from typing import TYPE_CHECKING, AsyncIterable, Optional, Union

import pytest

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import _parse_annotation, kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments


class InputObject(KernelBaseModel):
    arg1: str
    arg2: int


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

    @kernel_function()
    def func_input_object(self, input: InputObject):
        return input

    @kernel_function()
    def func_input_object_optional(self, input: Optional[InputObject] = None):
        return input

    @kernel_function()
    def func_input_object_annotated(self, input: Annotated[InputObject, "input description"]):
        return input

    @kernel_function()
    def func_input_object_annotated_optional(self, input: Annotated[Optional[InputObject], "input description"] = None):
        return input

    @kernel_function()
    def func_input_object_union(self, input: Union[InputObject, str]):
        return input

    @kernel_function()
    def func_no_typing(self, input):
        return input


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
    assert my_func.__kernel_function_description__ == "description"


def test_kernel_function_param_annotated():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_annotated")
    assert my_func.__kernel_function_parameters__[0]["description"] == "input description"
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"


def test_kernel_function_param_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_optional")
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"


def test_kernel_function_param_annotated_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_annotated_optional")
    assert my_func.__kernel_function_parameters__[0]["description"] == "input description"
    assert my_func.__kernel_function_parameters__[0]["type_"] == "str"
    assert not my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0]["default_value"] == "test"
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"


def test_kernel_function_return_type():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_return_type")
    assert my_func.__kernel_function_return_type__ == "str"
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
    assert my_func.__kernel_function_return_type__ == "str"
    assert my_func.__kernel_function_return_description__ == "test return"
    assert my_func.__kernel_function_return_required__
    assert my_func.__kernel_function_streaming__


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
    assert my_func.__kernel_function_parameters__[0]["description"] == "input description"
    assert my_func.__kernel_function_parameters__[0]["type_"] == "InputObject"
    assert my_func.__kernel_function_parameters__[0]["is_required"]
    assert my_func.__kernel_function_parameters__[0].get("default_value") is None
    assert my_func.__kernel_function_parameters__[0]["name"] == "input"
    assert my_func.__kernel_function_parameters__[0]["type_object"] == InputObject


def test_kernel_function_input_object_annotated_optional():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_input_object_annotated_optional")
    assert my_func.__kernel_function_parameters__[0]["description"] == "input description"
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
    ("annotation", "description", "type_", "is_required"),
    [
        (Annotated[str, "test"], "test", "str", True),
        (Annotated[Optional[str], "test"], "test", "str", False),
        (Annotated[AsyncIterable[str], "test"], "test", "str", True),
        (Annotated[Optional[Union[str, int]], "test"], "test", "str, int", False),
        (str, None, "str", True),
        (Union[str, int, float, "KernelArguments"], None, "str, int, float, KernelArguments", True),
    ],
)
def test_annotation_parsing(annotation, description, type_, is_required):
    annotations = _parse_annotation(annotation)

    assert description == annotations.get("description")
    assert type_ == annotations["type_"]
    assert is_required == annotations["is_required"]
