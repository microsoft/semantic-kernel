# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union
from unittest.mock import Mock

import pytest

from semantic_kernel.connectors.utils.structured_output_schema import generate_structured_output_response_format_schema
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder


class ExampleModel(KernelBaseModel):
    name: str
    age: int


class AnotherModel:
    title: str
    score: float


class MockClass:
    name: str = None
    age: int = None


class ModelWithOptionalAttributes:
    name: str | None = None


class ModelWithUnionPrimitives:
    item: int | str


class EnumTest(Enum):
    OPTION_A = "OptionA"
    OPTION_B = "OptionB"
    OPTION_C = "OptionC"


class MockModel:
    __annotations__ = {
        "id": int,
        "name": str,
        "is_active": bool,
        "scores": list[int],
        "metadata": dict[str, Any],
        "tags": set[str],
        "coordinates": tuple[int, int],
        "status": Union[int, str],
        "optional_field": Optional[str],
    }
    model_fields = {
        "id": Mock(description="The ID of the model"),
        "name": Mock(description="The name of the model"),
        "is_active": Mock(description="Whether the model is active"),
        "tags": Mock(description="Tags associated with the model"),
        "status": Mock(description="The status of the model, either as an integer or a string"),
        "scores": Mock(description="The scores associated with the model"),
        "optional_field": Mock(description="An optional field that can be null"),
        "metadata": Mock(description="The optional metadata description"),
        "coordinates": Mock(description="The coordinates of the model"),
    }


class PydanticStep(KernelBaseModel):
    explanation: str
    output: str


class PydanticReasoning(KernelBaseModel):
    steps: list[PydanticStep]
    final_answer: str


class NonPydanticStep:
    explanation: str
    output: str


class NonPydanticReasoning:
    steps: list[NonPydanticStep]
    final_answer: str


def test_build_with_kernel_base_model():
    expected_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
    result = KernelJsonSchemaBuilder.build(ExampleModel)
    assert result == expected_schema


def test_build_with_model_with_optional_attributes():
    expected_schema = {
        "type": "object",
        "properties": {"name": {"type": ["string", "null"]}},
    }
    result = KernelJsonSchemaBuilder.build(ModelWithOptionalAttributes)
    assert result == expected_schema


def test_build_with_model_with_union_attributes():
    expected_schema = {
        "type": "object",
        "properties": {"item": {"anyOf": [{"type": "integer"}, {"type": "string"}]}},
        "required": ["item"],
    }
    result = KernelJsonSchemaBuilder.build(ModelWithUnionPrimitives)
    assert result == expected_schema


def test_build_with_model_with_annotations():
    expected_schema = {
        "type": "object",
        "properties": {"title": {"type": "string"}, "score": {"type": "number"}},
        "required": ["title", "score"],
    }
    result = KernelJsonSchemaBuilder.build(AnotherModel)
    assert result == expected_schema


def test_build_with_primitive_type():
    expected_schema = {"type": "string"}
    result = KernelJsonSchemaBuilder.build(str)
    assert result == expected_schema
    result = KernelJsonSchemaBuilder.build("str")
    assert result == expected_schema

    expected_schema = {"type": "integer"}
    result = KernelJsonSchemaBuilder.build(int)
    assert result == expected_schema
    result = KernelJsonSchemaBuilder.build("int")
    assert result == expected_schema


def test_build_with_primitive_type_and_description():
    expected_schema = {"type": "string", "description": "A simple string"}
    result = KernelJsonSchemaBuilder.build(str, description="A simple string")
    assert result == expected_schema


def test_build_model_schema():
    expected_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
        "description": "A model",
    }
    result = KernelJsonSchemaBuilder.build_model_schema(ExampleModel, description="A model")
    assert result == expected_schema


def test_build_from_type_name():
    expected_schema = {"type": "string", "description": "A simple string"}
    result = KernelJsonSchemaBuilder.build_from_type_name("str", description="A simple string")
    assert result == expected_schema


def test_build_from_type_name_with_union():
    expected_schema = {
        "anyOf": [
            {"type": "string", "description": "The value"},
            {"type": "integer", "description": "The value"},
        ]
    }
    result = KernelJsonSchemaBuilder.build_from_type_name("str, int", description="The value")
    assert result == expected_schema


def test_get_json_schema():
    expected_schema = {"type": "string"}
    result = KernelJsonSchemaBuilder.get_json_schema(str)
    assert result == expected_schema

    expected_schema = {"type": "integer"}
    result = KernelJsonSchemaBuilder.get_json_schema(int)
    assert result == expected_schema


def test_build_list():
    schema = KernelJsonSchemaBuilder.build(list[str])
    assert schema == {"type": "array", "items": {"type": "string"}}


def test_build_list_complex_type():
    schema = KernelJsonSchemaBuilder.build(list[MockClass])
    assert schema == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        },
    }


def test_build_dict():
    schema = KernelJsonSchemaBuilder.build(dict[str, int])
    assert schema == {"type": "object", "additionalProperties": {"type": "integer"}}


def test_build_set():
    schema = KernelJsonSchemaBuilder.build(set[int])
    assert schema == {"type": "array", "items": {"type": "integer"}}


def test_build_tuple():
    schema = KernelJsonSchemaBuilder.build(tuple[int, str])
    assert schema == {
        "type": "array",
        "items": [{"type": "integer"}, {"type": "string"}],
    }


def test_build_union():
    schema = KernelJsonSchemaBuilder.build(Union[int, str])
    assert schema == {"anyOf": [{"type": "integer"}, {"type": "string"}]}


def test_build_optional():
    schema = KernelJsonSchemaBuilder.build(Optional[int])
    assert schema == {"type": ["integer", "null"]}


def test_build_model_schema_for_many_types():
    schema = KernelJsonSchemaBuilder.build(MockModel)
    expected = """
{
    "type": "object",
    "properties":
    {
        "id":
        {
            "type": "integer",
            "description": "The ID of the model"
        },
        "name":
        {
            "type": "string",
            "description": "The name of the model"
        },
        "is_active":
        {
            "type": "boolean",
            "description": "Whether the model is active"
        },
        "scores":
        {
            "type": "array",
            "items":
            {
                "type": "integer"
            },
            "description": "The scores associated with the model"
        },
        "metadata":
        {
            "type": "object",
            "additionalProperties":
            {
                "type": "object",
                "properties":
                {}
            },
            "description": "The optional metadata description"
        },
        "tags":
        {
            "type": "array",
            "items":
            {
                "type": "string"
            },
            "description": "Tags associated with the model"
        },
        "coordinates":
        {
            "type": "array",
            "items":
            [
                {
                    "type": "integer"
                },
                {
                    "type": "integer"
                }
            ],
            "description": "The coordinates of the model"
        },
        "status":
        {
            "anyOf":
            [
                {
                    "type": "integer",
                    "description": "The status of the model, either as an integer or a string"
                },
                {
                    "type": "string",
                    "description": "The status of the model, either as an integer or a string"
                }
            ]
        },
        "optional_field": {
            "description": "An optional field that can be null",
            "type": ["string", "null"]
        }
    },
    "required":
    [
        "id",
        "name",
        "is_active",
        "scores",
        "metadata",
        "tags",
        "coordinates",
        "status"
    ]
}
"""
    expected_schema = json.loads(expected)
    assert schema == expected_schema


@pytest.mark.parametrize(
    "type_name, expected",
    [
        ("int", {"type": "integer"}),
        ("str", {"type": "string"}),
        ("bool", {"type": "boolean"}),
        ("float", {"type": "number"}),
        ("list", {"type": "array"}),
        ("dict", {"type": "object"}),
        ("object", {"type": "object"}),
        ("array", {"type": "array"}),
    ],
)
def test_build_from_many_type_names(type_name, expected):
    assert KernelJsonSchemaBuilder.build_from_type_name(type_name) == expected


@pytest.mark.parametrize(
    "type_obj, expected",
    [
        (int, {"type": "integer"}),
        (str, {"type": "string"}),
        (bool, {"type": "boolean"}),
        (float, {"type": "number"}),
    ],
)
def test_get_json_schema_multiple(type_obj, expected):
    assert KernelJsonSchemaBuilder.get_json_schema(type_obj) == expected


class Items(KernelBaseModel):
    title: Annotated[str, "Description of the item"]
    resource: Annotated[int, "Number of turns required for the item"]


def test_build_complex_type_list():
    schema = KernelJsonSchemaBuilder.build(list[Items])
    assert schema is not None


def test_enum_schema():
    schema = KernelJsonSchemaBuilder.build(EnumTest, "Test Enum Description")
    expected_schema = {
        "type": "string",
        "enum": ["OptionA", "OptionB", "OptionC"],
        "description": "Test Enum Description",
    }
    assert schema == expected_schema


def test_enum_schema_without_description():
    schema = KernelJsonSchemaBuilder.build(EnumTest)
    expected_schema = {"type": "string", "enum": ["OptionA", "OptionB", "OptionC"]}
    assert schema == expected_schema


def test_handle_complex_type():
    schema = KernelJsonSchemaBuilder.handle_complex_type(str, "Description")
    expected_schema = {"type": "string", "description": "Description"}
    assert schema == expected_schema


def test_build_schema_with_pydantic_structured_output():
    schema = KernelJsonSchemaBuilder.build(parameter_type=PydanticReasoning, structured_output=True)
    structured_output_schema = generate_structured_output_response_format_schema(name="Reasoning", schema=schema)

    expected_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "Reasoning",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"explanation": {"type": "string"}, "output": {"type": "string"}},
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    assert structured_output_schema == expected_schema


def test_build_schema_with_nonpydantic_structured_output():
    schema = KernelJsonSchemaBuilder.build(parameter_type=NonPydanticReasoning, structured_output=True)
    structured_output_schema = generate_structured_output_response_format_schema(
        name="NonPydanticReasoning", schema=schema
    )

    expected_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "NonPydanticReasoning",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"explanation": {"type": "string"}, "output": {"type": "string"}},
                            "required": ["explanation", "output"],
                            "additionalProperties": False,
                        },
                    },
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    assert structured_output_schema == expected_schema


class ForwardRefTarget(KernelBaseModel):
    value: int
    label: str


class DirectListHolder(KernelBaseModel):
    items: list[ForwardRefTarget] = []


class ForwardRefListHolder(KernelBaseModel):
    items: list["ForwardRefTarget"] = []


class ForwardRefDictHolder(KernelBaseModel):
    mapping: dict[str, "ForwardRefTarget"] = {}


class ForwardRefNestedHolder(KernelBaseModel):
    items: list[list["ForwardRefTarget"]] = []


class ForwardRefOptionalHolder(KernelBaseModel):
    items: list[Optional["ForwardRefTarget"]] = []


class UnresolvableForwardRefHolder(KernelBaseModel):
    items: list["NotDefinedAnywhere"] = []  # noqa: F821


def test_build_model_schema_resolves_forward_ref_in_list():
    """list["Target"] must produce the same schema as list[Target]."""
    forward_ref = KernelJsonSchemaBuilder.build(ForwardRefListHolder)["properties"]["items"]
    direct = KernelJsonSchemaBuilder.build(DirectListHolder)["properties"]["items"]

    assert forward_ref == direct
    assert forward_ref["items"]["properties"] == {"value": {"type": "integer"}, "label": {"type": "string"}}
    assert forward_ref["items"]["required"] == ["value", "label"]


def test_build_model_schema_resolves_forward_ref_in_dict():
    """dict[str, "Target"] must carry the element schema through additionalProperties."""
    schema = KernelJsonSchemaBuilder.build(ForwardRefDictHolder)["properties"]["mapping"]

    assert schema["additionalProperties"]["properties"] == {
        "value": {"type": "integer"},
        "label": {"type": "string"},
    }


def test_build_model_schema_resolves_nested_forward_ref():
    """Resolution recurses into nested generic aliases."""
    schema = KernelJsonSchemaBuilder.build(ForwardRefNestedHolder)["properties"]["items"]

    assert schema["items"]["items"]["properties"] == {
        "value": {"type": "integer"},
        "label": {"type": "string"},
    }


def test_build_model_schema_resolves_forward_ref_inside_optional():
    """A ForwardRef nested under Optional inside a list still resolves."""
    schema = KernelJsonSchemaBuilder.build(ForwardRefOptionalHolder)["properties"]["items"]

    assert schema["items"]["type"] == ["object", "null"]
    assert schema["items"]["properties"] == {"value": {"type": "integer"}, "label": {"type": "string"}}


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="On 3.11+ get_type_hints raises NameError for the unresolvable name before the builder sees it",
)
def test_build_model_schema_unresolvable_forward_ref_falls_back():
    """An unresolvable name keeps the previous placeholder rather than raising."""
    schema = KernelJsonSchemaBuilder.build(UnresolvableForwardRefHolder)["properties"]["items"]

    assert schema == {"type": "array", "items": {"type": "object"}}


def test_resolve_forward_refs_leaves_literal_values_and_annotated_metadata_alone():
    """Strings that are values, not names, must not be looked up even when a global matches."""
    namespace = {"ForwardRefTarget": ForwardRefTarget}

    literal = KernelJsonSchemaBuilder.resolve_forward_refs(list[Literal["ForwardRefTarget"]], namespace)
    annotated = KernelJsonSchemaBuilder.resolve_forward_refs(
        list[Annotated["ForwardRefTarget", "ForwardRefTarget"]], namespace
    )

    assert literal == list[Literal["ForwardRefTarget"]]
    assert annotated == list[Annotated[ForwardRefTarget, "ForwardRefTarget"]]


def _not_a_type():
    return None


NOT_A_TYPE_VALUE = 3


def test_resolve_forward_refs_ignores_names_that_do_not_refer_to_a_type():
    """A reference that collides with a module, function or value keeps the placeholder fallback."""
    namespace = {
        "json": json,
        "_not_a_type": _not_a_type,
        "NOT_A_TYPE_VALUE": NOT_A_TYPE_VALUE,
        "ForwardRefTarget": ForwardRefTarget,
    }

    assert KernelJsonSchemaBuilder.resolve_forward_refs(list["json"], namespace) == list["json"]
    assert KernelJsonSchemaBuilder.resolve_forward_refs(list["_not_a_type"], namespace) == list["_not_a_type"]
    assert (
        KernelJsonSchemaBuilder.resolve_forward_refs(dict[str, "NOT_A_TYPE_VALUE"], namespace)
        == (dict[str, "NOT_A_TYPE_VALUE"])
    )
    # a sibling argument that does name a type is still resolved
    assert (
        KernelJsonSchemaBuilder.resolve_forward_refs(dict["json", "ForwardRefTarget"], namespace)
        == (dict["json", ForwardRefTarget])
    )
