# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.openapi_plugin.openapi_manager import OpenApiParser
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError


def test_parse_parameters_missing_in_field():
    parser = OpenApiParser()
    parameters = [{"name": "param1", "schema": {"type": "string"}}]
    with pytest.raises(PluginInitializationError, match="Parameter param1 is missing 'in' field"):
        parser._parse_parameters(parameters)


def test_get_payload_properties_schema_none():
    parser = OpenApiParser()
    properties = parser._get_payload_properties("operation_id", None, [])
    assert properties == []


def test_get_payload_properties_hierarchy_max_depth_exceeded():
    parser = OpenApiParser()
    schema = {
        "properties": {
            "prop1": {
                "type": "object",
                "properties": {
                    "prop2": {
                        "type": "object",
                        "properties": {
                            # Nested properties to exceed max depth
                        },
                    }
                },
            }
        }
    }
    with pytest.raises(
        Exception,
        match=f"Max level {OpenApiParser.PAYLOAD_PROPERTIES_HIERARCHY_MAX_DEPTH} of traversing payload properties of `operation_id` operation is exceeded.",  # noqa: E501
    ):
        parser._get_payload_properties("operation_id", schema, [], level=11)


def test_create_rest_api_operation_payload_media_type_none():
    parser = OpenApiParser()
    request_body = {"content": {"application/xml": {"schema": {"type": "object"}}}}
    with pytest.raises(Exception, match="Neither of the media types of operation_id is supported."):
        parser._create_rest_api_operation_payload("operation_id", request_body)
