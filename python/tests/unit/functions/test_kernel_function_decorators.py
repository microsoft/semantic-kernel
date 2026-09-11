# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, AsyncIterable
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, Annotated, Any, Union

import pytest

from semantic_kernel.functions.kernel_function_decorator import _process_signature, kernel_function
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

    @kernel_function
    def func_docstring_as_description(self, input):
        """Description."""
        return input

    @kernel_function
    def func_forward_ref_list(self, items: list["InputObject"]):
        return items

    @kernel_function
    def func_forward_ref_colliding_with_module(self, items: list["pytest"]):
        return items

    @kernel_function
    def func_input_annotated(self, input: Annotated[str, "input description"]):
        return input

    @kernel_function
    def func_input_annotated_optional(self, input: Annotated[str | None, "input description"] = "test"):
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
    def func_input_object_annotated(self, input: Annotated[InputObject, "input description"]):
        return input

    @kernel_function
    def func_input_object_annotated_optional(self, input: Annotated[InputObject | None, "input description"] = None):
        return input

    @kernel_function
    def func_input_object_union(self, input: InputObject | str):
        return input

    @kernel_function
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
    assert my_func.__kernel_function_description__ == "Description."


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
    assert my_func.__kernel_function_return_type__ in ("str, Any", "str, typing.Any")
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
    ("name", "annotation", "description", "type_", "is_required"),
    [
        ("anno_str", Annotated[str, "test"], "test", "str", True),
        ("anno_opt_str", Annotated[str | None, "test"], "test", "str", False),
        ("anno_iter_str", Annotated[AsyncIterable[str], "test"], "test", "str", True),
        ("anno_opt_str_int", Annotated[str | int | None, "test"], "test", "str, int", False),
        ("str", str, None, "str", True),
        ("union", Union[str, int, float, "KernelArguments"], None, "str, int, float, KernelArguments", True),
        ("new_union", "str | int | float | KernelArguments", None, "str, int, float, KernelArguments", True),
        ("opt_str", str | None, None, "str", False),
        ("list_str", list[str], None, "list[str]", True),
        ("dict_str", dict[str, str], None, "dict[str, str]", True),
        ("list_str_opt", list[str] | None, None, "list[str]", False),
        ("anno_dict_str", Annotated[dict[str, str], "description"], "description", "dict[str, str]", True),
        ("anno_opt_dict_str", Annotated[dict | str | None, "description"], "description", "dict, str", False),
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


def test_kernel_function_resolves_forward_ref_in_list_parameter():
    """list["InputObject"] on a kernel function parameter resolves to list[InputObject]."""
    my_func = getattr(MiscClass(), "func_forward_ref_list")
    param = my_func.__kernel_function_parameters__[0]

    assert param["name"] == "items"
    assert param["type_"] == "list[InputObject]"
    assert param["type_object"] == list[InputObject]


@pytest.mark.parametrize(
    ("annotation", "expected_type_object", "expected_description"),
    [
        (list["InputObject"], list[InputObject], None),
        (dict[str, "InputObject"], dict[str, InputObject], None),
        (Annotated[list["InputObject"], "description"], list[InputObject], "description"),
        (list["InputObject"] | None, list[InputObject], None),
    ],
)
def test_process_signature_resolves_forward_refs_with_globalns(annotation, expected_type_object, expected_description):
    param = Parameter(
        name="items",
        annotation=annotation,
        default=Parameter.empty,
        kind=Parameter.POSITIONAL_OR_KEYWORD,
    )
    func_sig = Signature(parameters=[param])

    annotations = _process_signature(func_sig, globals())

    assert annotations[0]["type_object"] == expected_type_object
    assert annotations[0].get("description") == expected_description


def test_process_signature_without_globalns_leaves_forward_refs_unchanged():
    """Callers that pass no namespace get the previous behaviour."""
    param = Parameter(
        name="items",
        annotation=list["InputObject"],
        default=Parameter.empty,
        kind=Parameter.POSITIONAL_OR_KEYWORD,
    )
    func_sig = Signature(parameters=[param])

    annotations = _process_signature(func_sig)

    assert annotations[0]["type_object"] == list["InputObject"]


def test_kernel_function_forward_ref_that_names_a_module_is_left_unresolved():
    """A reference colliding with a non type global must not be substituted or raise at decoration."""
    my_func = getattr(MiscClass(), "func_forward_ref_colliding_with_module")
    param = my_func.__kernel_function_parameters__[0]

    assert param["type_"] == "list[pytest]"
    assert param["type_object"] == list["pytest"]
