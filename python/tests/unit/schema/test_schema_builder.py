# Copyright (c) Microsoft. All rights reserved.

import collections.abc
import json
import logging
import sys
import types
import typing
from enum import Enum
from typing import Annotated, Any, ClassVar, Final, ForwardRef, Literal, Optional, Union, get_args
from unittest.mock import Mock

import pytest
from pydantic import Field

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


class PydanticModelWithConstrainedField(KernelBaseModel):
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="nucleus sampling")


class PydanticModelWithAnnotatedDescription(KernelBaseModel):
    name: Annotated[str, "display name"]


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


def test_build_model_schema_uses_pydantic_description_with_constraints():
    schema = KernelJsonSchemaBuilder.build_model_schema(PydanticModelWithConstrainedField)

    assert schema["properties"]["top_p"] == {"type": "number", "description": "nucleus sampling"}
    json.dumps(schema)


def test_build_model_schema_uses_annotated_metadata_description():
    schema = KernelJsonSchemaBuilder.build_model_schema(PydanticModelWithAnnotatedDescription)

    assert schema["properties"]["name"] == {"type": "string", "description": "display name"}
    json.dumps(schema)


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


def test_build_variadic_tuple():
    schema = KernelJsonSchemaBuilder.build(tuple[int, ...], "ids")
    assert schema == {"type": "array", "items": {"type": "integer"}, "description": "ids"}


def test_build_optional_variadic_tuple():
    schema = KernelJsonSchemaBuilder.build(Optional[tuple[str, ...]])
    assert schema == {"type": ["array", "null"], "items": {"type": "string"}}


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


class ModelWithClassVar(KernelBaseModel):
    marker: ClassVar[str] = "constant"
    value: int


class ModelWithBareClassVar(KernelBaseModel):
    marker: ClassVar = 0
    value: str


class ModelInheritingClassVar(ModelWithClassVar):
    extra: float


class PlainClassWithClassVar:
    marker: ClassVar[dict] = {}
    name: str


class ModelWithClassVarAndOptional(KernelBaseModel):
    counter: ClassVar[int] = 5
    keep: str
    drop: str | None = None


def test_build_model_schema_excludes_class_var():
    schema = KernelJsonSchemaBuilder.build(ModelWithClassVar)

    assert schema == {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}


def test_build_model_schema_excludes_bare_class_var():
    schema = KernelJsonSchemaBuilder.build(ModelWithBareClassVar)

    assert schema == {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]}


def test_build_model_schema_excludes_inherited_class_var():
    schema = KernelJsonSchemaBuilder.build(ModelInheritingClassVar)

    assert schema == {
        "type": "object",
        "properties": {"value": {"type": "integer"}, "extra": {"type": "number"}},
        "required": ["value", "extra"],
    }


def test_build_model_schema_excludes_class_var_on_plain_class():
    schema = KernelJsonSchemaBuilder.build(PlainClassWithClassVar)

    assert schema == {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}


def test_build_model_schema_class_var_with_optional_fields():
    schema = KernelJsonSchemaBuilder.build(ModelWithClassVarAndOptional)

    assert schema == {
        "type": "object",
        "properties": {"keep": {"type": "string"}, "drop": {"type": ["string", "null"]}},
        "required": ["keep"],
    }


def test_build_model_schema_class_var_structured_output():
    schema = KernelJsonSchemaBuilder.build(ModelWithClassVar, structured_output=True)

    assert schema == {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
        "additionalProperties": False,
    }


def test_build_model_schema_class_var_with_description():
    schema = KernelJsonSchemaBuilder.build(ModelWithClassVar, description="A payload")

    assert schema == {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
        "description": "A payload",
    }


def test_build_model_schema_class_var_via_instance():
    instance = ModelWithClassVar(value=1)

    schema = KernelJsonSchemaBuilder.build(instance)

    assert schema == {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}


@pytest.mark.parametrize(
    "instance",
    [
        ModelWithClassVar(value=1),
        ModelInheritingClassVar(value=1, extra=2.0),
        ModelWithClassVarAndOptional(keep="value"),
    ],
)
@pytest.mark.parametrize("structured_output", [False, True])
def test_build_model_schema_instance_matches_class(instance, structured_output):
    expected = KernelJsonSchemaBuilder.build(type(instance), structured_output=structured_output)
    assert KernelJsonSchemaBuilder.build(instance, structured_output=structured_output) == expected


def test_build_model_schema_allows_serialized_payload():
    schema = KernelJsonSchemaBuilder.build(ModelWithClassVar)

    serialized = ModelWithClassVar(value=1).model_dump()
    for field in schema.get("required", []):
        assert field in serialized


class LiteralModel(KernelBaseModel):
    level: Literal["low", "high"]
    maybe: Literal["a", "b"] | None = None


@pytest.mark.parametrize(
    ("literal_type", "expected"),
    [
        (Literal["fast", "slow"], {"type": "string", "enum": ["fast", "slow"]}),
        (Literal[1, 2], {"type": "integer", "enum": [1, 2]}),
        (Literal[True], {"type": "boolean", "enum": [True]}),
        (Literal["a", 1], {"type": ["integer", "string"], "enum": ["a", 1]}),
        (Optional[Literal["fast", "slow"]], {"type": ["string", "null"], "enum": ["fast", "slow", None]}),  # noqa: UP045
        (Literal["fast", "slow"] | None, {"type": ["string", "null"], "enum": ["fast", "slow", None]}),
        (Optional[Literal["a", None]], {"type": ["string", "null"], "enum": ["a", None]}),  # noqa: UP045
        (list[Literal["a", "b"]], {"type": "array", "items": {"type": "string", "enum": ["a", "b"]}}),
    ],
)
def test_build_literal(literal_type, expected):
    assert KernelJsonSchemaBuilder.build(literal_type) == expected


def test_build_literal_with_description():
    schema = KernelJsonSchemaBuilder.build(Literal["fast", "slow"], "speed mode")
    assert schema == {"type": "string", "enum": ["fast", "slow"], "description": "speed mode"}


def test_build_literal_enum_member():
    schema = KernelJsonSchemaBuilder.build(Literal[EnumTest.OPTION_A])
    assert schema == {"type": "string", "enum": ["OptionA"]}


def test_build_model_with_literal_fields():
    schema = KernelJsonSchemaBuilder.build(LiteralModel)
    assert schema == {
        "type": "object",
        "properties": {
            "level": {"type": "string", "enum": ["low", "high"]},
            "maybe": {"type": ["string", "null"], "enum": ["a", "b", None]},
        },
        "required": ["level"],
    }


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


def test_resolve_forward_refs_rebuilds_pep604_union_nested_in_list():
    """A PEP 604 union has no subscriptable origin, so it needs its own rebuild."""

    class Inner(KernelBaseModel):
        name: str

    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(list[list["Inner"] | None], {"Inner": Inner})

    assert resolved == list[list[Inner] | None]
    assert isinstance(get_args(resolved)[0], types.UnionType)


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        (list["ForwardRefTarget"] | None, list[ForwardRefTarget] | None),
        (None | list["ForwardRefTarget"], None | list[ForwardRefTarget]),
        (list[list["ForwardRefTarget"] | None], list[list[ForwardRefTarget] | None]),
        (dict[str, "ForwardRefTarget"] | None, dict[str, ForwardRefTarget] | None),
        (list[dict[str, "ForwardRefTarget"] | None], list[dict[str, ForwardRefTarget] | None]),
        (dict[str, list["ForwardRefTarget"] | None], dict[str, list[ForwardRefTarget] | None]),
        (
            list["ForwardRefTarget"] | dict[str, "ForwardRefTarget"] | None,
            list[ForwardRefTarget] | dict[str, ForwardRefTarget] | None,
        ),
        (tuple["ForwardRefTarget", ...] | None, tuple[ForwardRefTarget, ...] | None),
        (
            dict[str, list[dict[str, list["ForwardRefTarget"] | None] | None]],
            dict[str, list[dict[str, list[ForwardRefTarget] | None] | None]],
        ),
        (Union[list["ForwardRefTarget"], None], Union[list[ForwardRefTarget], None]),
        (list[Optional[list["ForwardRefTarget"]]], list[Optional[list[ForwardRefTarget]]]),
        (
            Union["ForwardRefTarget", "NotDefinedAnywhere"],  # noqa: F821
            Union[ForwardRefTarget, "NotDefinedAnywhere"],  # noqa: F821
        ),
        (
            list["NotDefinedAnywhere"] | list["ForwardRefTarget"],  # noqa: F821
            list["NotDefinedAnywhere"] | list[ForwardRefTarget],  # noqa: F821
        ),
    ],
)
def test_resolve_forward_refs_rebuilds_unions(annotation, expected):
    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(annotation, {"ForwardRefTarget": ForwardRefTarget})

    assert resolved == expected


@pytest.mark.parametrize(
    "annotation",
    [list["NotDefinedAnywhere"] | None, list[list["NotDefinedAnywhere"] | None]],  # noqa: F821
)
def test_resolve_forward_refs_keeps_unresolvable_name_in_union(annotation, caplog):
    with caplog.at_level(logging.WARNING):
        resolved = KernelJsonSchemaBuilder.resolve_forward_refs(annotation, {"ForwardRefTarget": ForwardRefTarget})

    assert resolved is annotation
    assert not caplog.records


def test_resolve_forward_refs_keeps_metadata_of_annotated_pep604_union():
    metadata = ("ForwardRefTarget", {"key": "value"})

    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(
        Annotated[(list["ForwardRefTarget"] | None, *metadata)], {"ForwardRefTarget": ForwardRefTarget}
    )

    assert resolved == Annotated[(list[ForwardRefTarget] | None, *metadata)]
    assert resolved.__metadata__ == metadata


def test_resolve_forward_refs_leaves_literal_value_in_union_alone():
    annotation = list[Literal["ForwardRefTarget"] | None]

    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(annotation, {"ForwardRefTarget": ForwardRefTarget})

    assert resolved == annotation


@pytest.mark.parametrize("callable_alias", [collections.abc.Callable, typing.Callable])
def test_resolve_forward_refs_resolves_callable_parameter_list(callable_alias):
    """Callable keeps its parameter types in a nested list."""
    namespace = {"ForwardRefTarget": ForwardRefTarget}

    only_parameters = KernelJsonSchemaBuilder.resolve_forward_refs(
        callable_alias[["ForwardRefTarget", int], str], namespace
    )
    nested = KernelJsonSchemaBuilder.resolve_forward_refs(
        list[callable_alias[[list["ForwardRefTarget"] | None], "ForwardRefTarget"]], namespace
    )
    ellipsis_parameters = KernelJsonSchemaBuilder.resolve_forward_refs(
        callable_alias[..., "ForwardRefTarget"], namespace
    )

    assert get_args(only_parameters) == ([ForwardRefTarget, int], str)
    assert get_args(get_args(nested)[0]) == ([list[ForwardRefTarget] | None], ForwardRefTarget)
    assert get_args(ellipsis_parameters) == (..., ForwardRefTarget)


@pytest.mark.parametrize("special_form", [ClassVar, Final])
def test_resolve_forward_refs_rebuilds_single_type_special_forms(special_form):
    """Special forms accept a single type and reject a one element tuple."""
    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(
        special_form["ForwardRefTarget"], {"ForwardRefTarget": ForwardRefTarget}
    )

    assert resolved == special_form[ForwardRefTarget]


def test_resolve_forward_refs_warns_when_an_alias_cannot_be_rebuilt(caplog):
    annotation = types.GenericAlias(int, ("ForwardRefTarget",))

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.schema.kernel_json_schema_builder"):
        resolved = KernelJsonSchemaBuilder.resolve_forward_refs(annotation, {"ForwardRefTarget": ForwardRefTarget})

    assert resolved is annotation
    assert "Could not rebuild" in caplog.text


class ForwardRefNullableListHolder(KernelBaseModel):
    items: list["ForwardRefTarget"] | None = None


class ForwardRefNestedNullableListHolder(KernelBaseModel):
    items: list[list["ForwardRefTarget"] | None] = []


class ForwardRefNullableDictInUnionHolder(KernelBaseModel):
    mapping: dict[str, list["ForwardRefTarget"] | None] | None = None


def test_build_model_schema_resolves_forward_ref_in_nullable_list():
    schema = KernelJsonSchemaBuilder.build(ForwardRefNullableListHolder)["properties"]["items"]

    assert schema["type"] == ["array", "null"]
    assert schema["items"]["properties"] == {"value": {"type": "integer"}, "label": {"type": "string"}}


def test_build_model_schema_resolves_forward_ref_in_nested_nullable_list():
    schema = KernelJsonSchemaBuilder.build(ForwardRefNestedNullableListHolder)["properties"]["items"]

    assert schema["items"]["type"] == ["array", "null"]
    assert schema["items"]["items"]["properties"] == {"value": {"type": "integer"}, "label": {"type": "string"}}


def test_build_model_schema_resolves_forward_ref_in_dict_nested_in_union():
    schema = KernelJsonSchemaBuilder.build(ForwardRefNullableDictInUnionHolder)["properties"]["mapping"]

    assert schema["type"] == ["object", "null"]
    assert schema["additionalProperties"]["type"] == ["array", "null"]
    assert schema["additionalProperties"]["items"]["properties"] == {
        "value": {"type": "integer"},
        "label": {"type": "string"},
    }


class SelfReferencingHolder(KernelBaseModel):
    name: str
    children: list["SelfReferencingHolder"] = []


class MutualReferenceFirst(KernelBaseModel):
    second: list["MutualReferenceSecond"] = []


class MutualReferenceSecond(KernelBaseModel):
    first: list["MutualReferenceFirst"] = []


class RepeatedTargetHolder(KernelBaseModel):
    first: list["ForwardRefTarget"] = []
    second: list["ForwardRefTarget"] = []


def test_build_model_schema_stops_at_a_self_reference():
    """A resolved reference back to the model being built ends at the placeholder instead of recursing."""
    schema = KernelJsonSchemaBuilder.build(SelfReferencingHolder)

    assert schema["properties"]["name"] == {"type": "string"}
    assert schema["properties"]["children"] == {"type": "array", "items": {"type": "object"}}


def test_build_model_schema_stops_at_a_mutual_reference():
    schema = KernelJsonSchemaBuilder.build(MutualReferenceFirst)

    assert schema["properties"]["second"]["items"]["properties"]["first"] == {
        "type": "array",
        "items": {"type": "object"},
    }


def test_build_model_schema_expands_a_repeated_model_every_time():
    """Only a model further up the call stack is cut short; a sibling field repeating a model is not."""
    properties = KernelJsonSchemaBuilder.build(RepeatedTargetHolder)["properties"]

    assert properties["first"] == properties["second"]
    assert properties["second"]["items"]["properties"] == {"value": {"type": "integer"}, "label": {"type": "string"}}


@pytest.mark.parametrize("reference", ["ForwardRefTarget", ForwardRef("ForwardRefTarget")])
def test_resolve_forward_refs_resolves_a_bare_reference(reference):
    """Unwrapping Optional["Target"] or Annotated["Target", ...] on a kernel function leaves a bare ForwardRef."""
    resolved = KernelJsonSchemaBuilder.resolve_forward_refs(reference, {"ForwardRefTarget": ForwardRefTarget})

    assert resolved is ForwardRefTarget


@pytest.mark.parametrize(
    ("reference", "namespace"),
    [
        ("NotDefinedAnywhere", {}),
        (ForwardRef("NotDefinedAnywhere"), {}),
        (ForwardRef("json"), {"json": json}),
    ],
)
def test_resolve_forward_refs_keeps_a_bare_reference_that_does_not_name_a_type(reference, namespace, caplog):
    with caplog.at_level(logging.WARNING):
        resolved = KernelJsonSchemaBuilder.resolve_forward_refs(reference, namespace)

    assert resolved is reference
    assert not caplog.records


class UnevaluableHintsTarget:
    value: "NotDefinedAnywhere"  # noqa: F821


@pytest.mark.parametrize(
    "annotation",
    [
        list["UnevaluableHintsTarget"],
        ForwardRef("UnevaluableHintsTarget"),
        list["UnevaluableHintsTarget"] | None,
    ],
)
def test_resolve_forward_refs_keeps_a_reference_to_a_class_whose_hints_do_not_evaluate(annotation, caplog):
    """Building such a class raises, so the reference keeps the placeholder fallback and says why."""
    namespace = {"UnevaluableHintsTarget": UnevaluableHintsTarget}

    with caplog.at_level(logging.WARNING, logger="semantic_kernel.schema.kernel_json_schema_builder"):
        resolved = KernelJsonSchemaBuilder.resolve_forward_refs(annotation, namespace)

    assert resolved is annotation
    assert "UnevaluableHintsTarget" in caplog.text
    assert "NotDefinedAnywhere" in caplog.text
