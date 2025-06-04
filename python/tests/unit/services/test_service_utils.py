# Copyright (c) Microsoft. All rights reserved.

import datetime
from enum import Enum
from typing import Annotated

import pytest
from pydantic import Field

from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_function_call_format,
)
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel

# region Test helpers


class DateTimePlugin:
    class Data(KernelBaseModel):
        timestamp: datetime.datetime

    @kernel_function(name="GetData", description="Get a Data class.")
    def get_data(data: Annotated[Data, "The data."]) -> Annotated[Data, "The data."]:
        """Get the data."""
        return data


class BooleanPlugin:
    @kernel_function(name="GetBoolean", description="Get a boolean value.")
    def get_boolean(self, value: Annotated[bool, "The boolean value."]) -> Annotated[bool, "The boolean value."]:
        return value


class StringPlugin:
    @kernel_function(name="GetWeather", description="Get the weather for a location.")
    def get_weather(
        self, location: Annotated[str, "The location to get the weather for."]
    ) -> Annotated[str, "The weather for the location."]:
        return f"The weather in {location} is sunny."


class ComplexRequest(KernelBaseModel):
    start_date: str = Field(
        ...,
        description="The start date in ISO 8601 format",
        examples=["2024-01-23", "2020-06-15"],
    )
    end_date: str = Field(
        ...,
        description="The end date in ISO-8601 format",
        examples=["2024-01-23", "2020-06-15"],
    )


class ComplexTypePlugin:
    @kernel_function(name="answer_request", description="Answer a request")
    def book_holiday(
        self, request: Annotated[ComplexRequest, "A request to answer."]
    ) -> Annotated[
        bool,
        "The result is the boolean value True if successful, False if unsuccessful.",
    ]:
        return True


class Items(KernelBaseModel):
    name: Annotated[str, "The name"]
    id: Annotated[int, "The id"]


class ItemsPlugin(KernelBaseModel):
    @kernel_function(
        name="return_items",
        description="Returns the items",
    )
    def return_items(
        self,
        items: Annotated[list[Items], "Ordered list of items to be returned"],
    ):
        pass


class ListPlugin:
    @kernel_function(name="get_items", description="Filters a list.")
    def get_configuration(
        self, items: Annotated[list[str], "The list of items."]
    ) -> Annotated[list[str], "The filtered list."]:
        return [item for item in items if item in ["skip"]]


class UnionTypePluginLegacySyntax:
    @kernel_function(name="union_legacy", description="Union type")
    def union(self, value: Annotated[str | int, "The union value"]) -> Annotated[str | int, "The union value"]:
        return value


class UnionTypePlugin:
    @kernel_function(name="union", description="Union type")
    def union(self, value: Annotated[str | int, "The union value"]) -> Annotated[str | int, "The union value"]:
        return value


class MyEnum(Enum):
    OPTION_A = "OptionA"
    OPTION_B = "OptionB"
    OPTION_C = "OptionC"


class EnumPlugin:
    @kernel_function(name="GetEnumValue", description="Get a value from the enum.")
    def get_enum_value(
        self, value: Annotated[MyEnum, "The enum value."]
    ) -> Annotated[str, "The string representation of the enum value."]:
        return value.value


@pytest.fixture
def setup_kernel():
    kernel = Kernel()
    kernel.add_plugins({
        "BooleanPlugin": BooleanPlugin(),
        "StringPlugin": StringPlugin(),
        "ComplexTypePlugin": ComplexTypePlugin(),
        "ListPlugin": ListPlugin(),
        "ItemsPlugin": ItemsPlugin(),
        "UnionPlugin": UnionTypePlugin(),
        "UnionPluginLegacy": UnionTypePluginLegacySyntax(),
        "EnumPlugin": EnumPlugin(),
        "DateTimePlugin": DateTimePlugin(),
    })
    return kernel


# endregion


def test_bool_schema(setup_kernel):
    kernel = setup_kernel

    boolean_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["BooleanPlugin"]}
    )

    boolean_schema = kernel_function_metadata_to_function_call_format(boolean_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "BooleanPlugin-GetBoolean",
            "description": "Get a boolean value.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "boolean", "description": "The boolean value."}},
                "required": ["value"],
            },
        },
    }

    assert boolean_schema == expected_schema


def test_bool_schema_no_plugins(setup_kernel):
    kernel = setup_kernel
    kernel.plugins = None

    boolean_func_metadata = kernel.get_list_of_function_metadata_bool()

    assert boolean_func_metadata == []


def test_bool_schema_with_plugins(setup_kernel):
    kernel = setup_kernel

    boolean_func_metadata = kernel.get_list_of_function_metadata_bool()

    assert boolean_func_metadata is not None
    assert len(boolean_func_metadata) > 0


def test_string_schema(setup_kernel):
    kernel = setup_kernel

    string_func_metadata = kernel.get_list_of_function_metadata_filters(filters={"included_plugins": ["StringPlugin"]})

    string_schema = kernel_function_metadata_to_function_call_format(string_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "StringPlugin-GetWeather",
            "description": "Get the weather for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get the weather for.",
                    }
                },
                "required": ["location"],
            },
        },
    }

    assert string_schema == expected_schema


def test_string_schema_filter_functions(setup_kernel):
    kernel = setup_kernel

    string_func_metadata = kernel.get_list_of_function_metadata_filters(filters={"included_functions": ["random"]})

    assert string_func_metadata == []


def test_string_schema_throws_included_and_excluded_plugins(setup_kernel):
    kernel = setup_kernel

    with pytest.raises(ValueError):
        _ = kernel.get_list_of_function_metadata_filters(
            filters={"included_plugins": ["StringPlugin"], "excluded_plugins": ["BooleanPlugin"]}
        )


def test_string_schema_throws_included_and_excluded_functions(setup_kernel):
    kernel = setup_kernel

    with pytest.raises(ValueError):
        _ = kernel.get_list_of_function_metadata_filters(
            filters={"included_functions": ["function1"], "excluded_functions": ["function2"]}
        )


def test_complex_schema(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["ComplexTypePlugin"]}
    )

    complex_schema = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "ComplexTypePlugin-answer_request",
            "description": "Answer a request",
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "The start date in ISO 8601 format",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "The end date in ISO-8601 format",
                            },
                        },
                        "required": ["start_date", "end_date"],
                        "description": "A request to answer.",
                    }
                },
                "required": ["request"],
            },
        },
    }

    assert complex_schema == expected_schema


def test_list_schema(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(filters={"included_plugins": ["ListPlugin"]})

    complex_schema = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "ListPlugin-get_items",
            "description": "Filters a list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "The list of items.",
                        "items": {"type": "string"},
                    }
                },
                "required": ["items"],
            },
        },
    }

    assert complex_schema == expected_schema


def test_list_of_items_plugin(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(filters={"included_plugins": ["ItemsPlugin"]})

    complex_schema = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "ItemsPlugin-return_items",
            "description": "Returns the items",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "The name"},
                                "id": {
                                    "type": "integer",
                                    "description": "The id",
                                },
                            },
                            "required": ["name", "id"],
                        },
                        "description": "Ordered list of items to be returned",
                    }
                },
                "required": ["items"],
            },
        },
    }

    assert complex_schema == expected_schema


@pytest.mark.parametrize(
    ("plugin_name", "function_name"), [("UnionPlugin", "union"), ("UnionPluginLegacy", "union_legacy")]
)
def test_union_plugin(setup_kernel, plugin_name, function_name):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["UnionPlugin", "UnionPluginLegacy"]}
    )

    complex_schema_1 = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])
    complex_schema_2 = kernel_function_metadata_to_function_call_format(complex_func_metadata[1])

    expected_schema = {
        "type": "function",
        "function": {
            "name": f"{plugin_name}-{function_name}",
            "description": "Union type",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "anyOf": [
                            {"type": "string", "description": "The union value"},
                            {"type": "integer", "description": "The union value"},
                        ]
                    }
                },
                "required": ["value"],
            },
        },
    }

    if plugin_name == "UnionPlugin":
        assert complex_schema_1 == expected_schema
    else:
        assert complex_schema_2 == expected_schema


def test_enum_plugin(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(filters={"included_plugins": ["EnumPlugin"]})

    complex_schema = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "EnumPlugin-GetEnumValue",
            "description": "Get a value from the enum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "string",
                        "enum": ["OptionA", "OptionB", "OptionC"],
                        "description": "The enum value.",
                    }
                },
                "required": ["value"],
            },
        },
    }

    assert complex_schema == expected_schema


def test_datetime_parameter(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["DateTimePlugin"]}
    )

    complex_schema = kernel_function_metadata_to_function_call_format(complex_func_metadata[0])

    expected_schema = {
        "type": "function",
        "function": {
            "name": "DateTimePlugin-GetData",
            "description": "Get a Data class.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "properties": {"timestamp": {"type": "object"}},
                        "required": ["timestamp"],
                        "description": "The data.",
                    }
                },
                "required": ["data"],
            },
        },
    }

    assert complex_schema == expected_schema
