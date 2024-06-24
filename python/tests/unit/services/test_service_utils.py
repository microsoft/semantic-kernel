# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

import pytest
from pydantic import Field

from semantic_kernel.connectors.ai.open_ai.services.utils import (
    kernel_function_metadata_to_openai_tool_format,
)
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel

# region Test helpers


class BooleanPlugin:
    @kernel_function(name="GetBoolean", description="Get a boolean value.")
    def get_boolean(
        self, value: Annotated[bool, "The boolean value."]
    ) -> Annotated[bool, "The boolean value."]:
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


@pytest.fixture
def setup_kernel():
    kernel = Kernel()
    kernel.add_plugins(
        {
            "BooleanPlugin": BooleanPlugin(),
            "StringPlugin": StringPlugin(),
            "ComplexTypePlugin": ComplexTypePlugin(),
            "ListPlugin": ListPlugin(),
            "ItemsPlugin": ItemsPlugin(),
        }
    )
    return kernel


# endregion


def test_bool_schema(setup_kernel):
    kernel = setup_kernel

    boolean_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["BooleanPlugin"]}
    )

    boolean_schema = kernel_function_metadata_to_openai_tool_format(
        boolean_func_metadata[0]
    )

    expected_schema = {
        "type": "function",
        "function": {
            "name": "BooleanPlugin-GetBoolean",
            "description": "Get a boolean value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "boolean", "description": "The boolean value."}
                },
                "required": ["value"],
            },
        },
    }

    assert boolean_schema == expected_schema


def test_string_schema(setup_kernel):
    kernel = setup_kernel

    string_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["StringPlugin"]}
    )

    string_schema = kernel_function_metadata_to_openai_tool_format(
        string_func_metadata[0]
    )

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


def test_complex_schema(setup_kernel):
    kernel = setup_kernel

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["ComplexTypePlugin"]}
    )

    complex_schema = kernel_function_metadata_to_openai_tool_format(
        complex_func_metadata[0]
    )

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

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["ListPlugin"]}
    )

    complex_schema = kernel_function_metadata_to_openai_tool_format(
        complex_func_metadata[0]
    )

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

    complex_func_metadata = kernel.get_list_of_function_metadata_filters(
        filters={"included_plugins": ["ItemsPlugin"]}
    )

    complex_schema = kernel_function_metadata_to_openai_tool_format(
        complex_func_metadata[0]
    )

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
