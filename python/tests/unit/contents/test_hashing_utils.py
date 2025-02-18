# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import BaseModel

from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent


class SimpleModel(BaseModel):
    field1: str
    field2: int


class NestedModel(BaseModel):
    name: str
    values: list[int]


class ModelContainer(BaseModel):
    container_name: str
    nested_model: NestedModel


def test_hash_with_nested_structures():
    """
    Deeply nested dictionaries and lists, but with no cyclical references.
    Ensures multiple levels of nested transformations work.
    """
    data = {
        "level1": {
            "list1": [1, 2, 3],
            "dict1": {"keyA": "valA", "keyB": "valB"},
        },
        "level2": [
            {"sub_dict1": {"x": 99}},
            {"sub_dict2": {"y": 100}},
        ],
    }
    content = FunctionResultContent(
        id="test_nested_structures",
        result=data,
        function_name="TestNestedStructures",
    )
    _ = hash(content)
    assert True, "Hashing deeply nested structures succeeded."


def test_hash_with_repeated_references():
    """
    Multiple references to the same object, but no cycle.
    Ensures repeated objects are handled consistently and do not cause duplication.
    """
    shared_dict = {"common_key": "common_value"}
    data = {
        "ref1": shared_dict,
        "ref2": shared_dict,  # same object, repeated reference
    }
    content = FunctionResultContent(
        id="test_repeated_references",
        result=data,
        function_name="TestRepeatedRefs",
    )
    _ = hash(content)
    assert True, "Hashing repeated references (no cycles) succeeded."


def test_hash_with_simple_pydantic_model():
    """
    Hash a Pydantic model that doesn't reference itself or another model.
    """
    model_instance = SimpleModel(field1="hello", field2=42)
    content = FunctionResultContent(
        id="test_simple_model",
        result=model_instance,
        function_name="TestSimpleModel",
    )
    _ = hash(content)
    assert True, "Hashing a simple Pydantic model succeeded."


def test_hash_with_nested_pydantic_models():
    """
    Hash a Pydantic model containing another Pydantic model, no cycles.
    """
    nested = NestedModel(name="MyNestedModel", values=[1, 2, 3])
    container = ModelContainer(container_name="TopLevel", nested_model=nested)
    content = FunctionResultContent(
        id="test_nested_models",
        result=container,
        function_name="TestNestedModels",
    )
    _ = hash(content)
    assert True, "Hashing nested Pydantic models succeeded."


def test_hash_with_triple_cycle():
    """
    Three dictionaries referencing each other to form a cycle.
    This ensures that multi-node cycles are also handled.
    """
    dict_a: dict[str, Any] = {"a_key": 1}
    dict_b: dict[str, Any] = {"b_key": 2}
    dict_c: dict[str, Any] = {"c_key": 3}

    dict_a["ref_to_b"] = dict_b
    dict_b["ref_to_c"] = dict_c
    dict_c["ref_to_a"] = dict_a

    content = FunctionResultContent(
        id="test_triple_cycle",
        result=dict_a,
        function_name="TestTripleCycle",
    )

    _ = hash(content)
    assert True, "Hashing triple cyclical references succeeded."


def test_hash_with_cyclical_references():
    """
    The original cyclical references test for thorough coverage.
    """

    class CyclicalModel(BaseModel):
        name: str
        partner: "CyclicalModel" = None  # type: ignore

    CyclicalModel.model_rebuild()

    model_a = CyclicalModel(name="ModelA")
    model_b = CyclicalModel(name="ModelB")
    model_a.partner = model_b
    model_b.partner = model_a

    dict_x = {"x_key": 42}
    dict_y = {"y_key": 99, "ref_to_x": dict_x}
    dict_x["ref_to_y"] = dict_y  # type: ignore

    giant_data_structure = {
        "models": [model_a, model_b],
        "nested": {"cyclical_dict_x": dict_x, "cyclical_dict_y": dict_y},
    }

    content = FunctionResultContent(
        id="test_id_cyclical",
        result=giant_data_structure,
        function_name="TestFunctionCyclical",
    )

    _ = hash(content)


def test_hash_with_large_structure():
    """
    Tests performance or at least correctness when dealing with
    a large structure, ensuring we don't crash or exceed recursion.
    """
    large_list = list(range(1000))
    large_dict = {f"key_{i}": i for i in range(1000)}
    combined = {
        "big_list": large_list,
        "big_dict": large_dict,
        "nested": [
            {"inner_list": large_list},
            {"inner_dict": large_dict},
        ],
    }
    content = FunctionResultContent(
        id="test_large_structure",
        result=combined,
        function_name="TestLargeStructure",
    )

    _ = hash(content)


def test_hash_function_call_content():
    call_content = FunctionCallContent(
        inner_content=None,
        ai_model_id=None,
        metadata={},
        id="call_LAbz",
        index=None,
        name="menu-get_specials",
        function_name="get_specials",
        plugin_name="menu",
        arguments="{}",
    )

    content = FunctionResultContent(
        id="test_function_call_content", result=call_content, function_name="TestFunctionCallContent"
    )

    _ = hash(content)
