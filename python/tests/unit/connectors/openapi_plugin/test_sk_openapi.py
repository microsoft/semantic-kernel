# Copyright (c) Microsoft. All rights reserved.

import os
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import yaml
from openapi_core import Spec

from semantic_kernel.connectors.openapi_plugin import OperationSelectionPredicateContext
from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter import (
    RestApiParameter,
    RestApiParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_style import (
    RestApiParameterStyle,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload_property import (
    RestApiPayloadProperty,
)
from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
    OpenAPIFunctionExecutionParameters,
)
from semantic_kernel.connectors.openapi_plugin.openapi_manager import OpenApiParser, OpenApiRunner, RestApiOperation
from semantic_kernel.exceptions import FunctionExecutionException

directory = os.path.dirname(os.path.realpath(__file__))
openapi_document = directory + "/openapi.yaml"
invalid_openapi_document = directory + "/invalid_openapi.yaml"
with open(openapi_document) as f:
    openapi_document_json = yaml.safe_load(f)
spec = Spec.from_dict(openapi_document_json)

operation_names = [
    "getTodos",
    "addTodo",
    "getTodoById",
    "updateTodoById",
    "deleteTodoById",
]

put_operation = RestApiOperation(
    id="updateTodoById",
    method="PUT",
    servers="http://example.com",
    path="/todos/{id}",
    summary="Update a todo by ID",
    params=[
        {
            "name": "id",
            "in": "path",
            "required": True,
            "schema": {"type": "integer", "minimum": 1},
        },
        {
            "name": "Authorization",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "description": "The authorization token"},
        },
        {
            "name": "completed",
            "in": "query",
            "required": False,
            "schema": {
                "type": "boolean",
                "description": "Whether the todo is completed or not",
            },
        },
    ],
    request_body={
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the todo",
                            "example": "Buy milk",
                        },
                        "completed": {
                            "type": "boolean",
                            "description": "Whether the todo is completed or not",
                            "example": False,
                        },
                    },
                }
            }
        },
    },
)


"""OpenApiParser tests"""


def test_parse_valid():
    parser = OpenApiParser()
    result = parser.parse(openapi_document)
    assert result == spec.content()


def test_parse_invalid_location():
    parser = OpenApiParser()
    with pytest.raises(Exception):
        parser.parse("invalid_location")


def test_parse_invalid_format():
    parser = OpenApiParser()
    with pytest.raises(Exception):
        parser.parse(invalid_openapi_document)


def test_url_join_with_trailing_slash():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="test/path")
    base_url = "https://example.com/"
    path = "test/path"
    expected_url = "https://example.com/test/path"
    assert operation.url_join(base_url, path) == expected_url


def test_url_join_without_trailing_slash():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com"], path="test/path")
    base_url = "https://example.com"
    path = "test/path"
    expected_url = "https://example.com/test/path"
    assert operation.url_join(base_url, path) == expected_url


def test_url_join_base_path_with_path():
    operation = RestApiOperation(id="test", method="GET", servers="https://example.com/base/", path="test/path")
    base_url = "https://example.com/base/"
    path = "test/path"
    expected_url = "https://example.com/base/test/path"
    assert operation.url_join(base_url, path) == expected_url


def test_url_join_with_leading_slash_in_path():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/test/path")
    base_url = "https://example.com/"
    path = "/test/path"
    expected_url = "https://example.com/test/path"
    assert operation.url_join(base_url, path) == expected_url


def test_url_join_base_path_without_trailing_slash():
    operation = RestApiOperation(id="test", method="GET", servers="https://example.com/base", path="test/path")
    base_url = "https://example.com/base"
    path = "test/path"
    expected_url = "https://example.com/base/test/path"
    assert operation.url_join(base_url, path) == expected_url


def test_build_headers_with_required_parameter():
    parameters = [
        RestApiParameter(
            name="Authorization", type="string", location=RestApiParameterLocation.HEADER, is_required=True
        )
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com"], path="test/path", params=parameters
    )
    arguments = {"Authorization": "Bearer token"}
    expected_headers = {"Authorization": "Bearer token"}
    assert operation.build_headers(arguments) == expected_headers


def test_rest_api_operation_freeze():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=["https://example.com/"],
        path="test/path",
        summary="A test summary",
        description="A test description",
        params=[],
        request_body=None,
        responses={},
        security_requirements=[],
    )

    operation.description = "Modified description"
    assert operation.description == "Modified description"

    operation.freeze()

    with pytest.raises(FunctionExecutionException, match="is frozen and cannot be modified"):
        operation.description = "Another modification"

    with pytest.raises(FunctionExecutionException, match="is frozen and cannot be modified"):
        operation.path = "new/test/path"

    if operation.request_body:
        with pytest.raises(FunctionExecutionException):
            operation.request_body.description = "New request body description"


def test_build_headers_missing_required_parameter():
    parameters = [
        RestApiParameter(
            name="Authorization", type="string", location=RestApiParameterLocation.HEADER, is_required=True
        )
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com"], path="test/path", params=parameters
    )
    arguments = {}
    with pytest.raises(
        FunctionExecutionException,
        match="No argument is provided for the `Authorization` required parameter of the operation - `test`.",
    ):
        operation.build_headers(arguments)


def test_build_headers_with_optional_parameter():
    parameters = [
        RestApiParameter(
            name="Authorization", type="string", location=RestApiParameterLocation.HEADER, is_required=False
        )
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com"], path="test/path", params=parameters
    )
    arguments = {"Authorization": "Bearer token"}
    expected_headers = {"Authorization": "Bearer token"}
    assert operation.build_headers(arguments) == expected_headers


def test_build_headers_missing_optional_parameter():
    parameters = [
        RestApiParameter(
            name="Authorization", type="string", location=RestApiParameterLocation.HEADER, is_required=False
        )
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com"], path="test/path", params=parameters
    )
    arguments = {}
    expected_headers = {}
    assert operation.build_headers(arguments) == expected_headers


def test_build_headers_multiple_parameters():
    parameters = [
        RestApiParameter(
            name="Authorization", type="string", location=RestApiParameterLocation.HEADER, is_required=True
        ),
        RestApiParameter(
            name="Content-Type", type="string", location=RestApiParameterLocation.HEADER, is_required=False
        ),
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com"], path="test/path", params=parameters
    )
    arguments = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    expected_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    assert operation.build_headers(arguments) == expected_headers


def test_build_operation_url_with_override():
    parameters = [RestApiParameter(name="id", type="string", location=RestApiParameterLocation.PATH, is_required=True)]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource/{id}", params=parameters
    )
    arguments = {"id": "123"}
    server_url_override = urlparse("https://override.com")
    expected_url = "https://override.com/resource/123"
    assert operation.build_operation_url(arguments, server_url_override=server_url_override) == expected_url


def test_build_operation_url_without_override():
    parameters = [RestApiParameter(name="id", type="string", location=RestApiParameterLocation.PATH, is_required=True)]
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com/"}],
        path="/resource/{id}",
        params=parameters,
    )
    arguments = {"id": "123"}
    expected_url = "https://example.com/resource/123"
    assert operation.build_operation_url(arguments) == expected_url


def test_get_server_url_with_parse_result_override():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com"}],
        path="/resource/{id}",
    )
    server_url_override = urlparse("https://override.com")
    expected_url = "https://override.com/"
    assert operation.get_server_url(server_url_override=server_url_override) == expected_url


def test_get_server_url_with_string_override():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com"}],
        path="/resource/{id}",
    )
    server_url_override = "https://override.com"
    expected_url = "https://override.com/"
    assert operation.get_server_url(server_url_override=server_url_override) == expected_url


def test_get_server_url_with_servers_no_variables():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com"}],
        path="/resource/{id}",
    )
    expected_url = "https://example.com/"
    assert operation.get_server_url() == expected_url


def test_get_server_url_with_servers_and_variables():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[
            {
                "url": "https://example.com/{version}",
                "variables": {"version": {"default": "v1", "argument_name": "api_version"}},
            }
        ],
        path="/resource/{id}",
    )
    arguments = {"api_version": "v2"}
    expected_url = "https://example.com/v2/"
    assert operation.get_server_url(arguments=arguments) == expected_url


def test_get_server_url_with_servers_and_default_variable():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com/{version}", "variables": {"version": {"default": "v1"}}}],
        path="/resource/{id}",
    )
    expected_url = "https://example.com/v1/"
    assert operation.get_server_url() == expected_url


def test_get_server_url_with_override():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com"}],
        path="/resource/{id}",
    )
    server_url_override = "https://override.com"
    expected_url = "https://override.com/"
    assert operation.get_server_url(server_url_override=server_url_override) == expected_url


def test_get_server_url_without_override():
    operation = RestApiOperation(
        id="test",
        method="GET",
        servers=[{"url": "https://example.com"}],
        path="/resource/{id}",
    )
    expected_url = "https://example.com/"
    assert operation.get_server_url() == expected_url


def test_build_path_with_required_parameter():
    parameters = [RestApiParameter(name="id", type="string", location=RestApiParameterLocation.PATH, is_required=True)]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource/{id}", params=parameters
    )
    arguments = {"id": "123"}
    expected_path = "/resource/123"
    assert operation.build_path(operation.path, arguments) == expected_path


def test_build_path_missing_required_parameter():
    parameters = [RestApiParameter(name="id", type="string", location=RestApiParameterLocation.PATH, is_required=True)]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource/{id}", params=parameters
    )
    arguments = {}
    with pytest.raises(
        FunctionExecutionException,
        match="No argument is provided for the `id` required parameter of the operation - `test`.",
    ):
        operation.build_path(operation.path, arguments)


def test_build_path_with_optional_and_required_parameters():
    parameters = [
        RestApiParameter(name="id", type="string", location=RestApiParameterLocation.PATH, is_required=True),
        RestApiParameter(name="optional", type="string", location=RestApiParameterLocation.PATH, is_required=False),
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource/{id}/{optional}", params=parameters
    )
    arguments = {"id": "123"}
    expected_path = "/resource/123/{optional}"
    assert operation.build_path(operation.path, arguments) == expected_path


def test_build_query_string_with_required_parameter():
    parameters = [
        RestApiParameter(name="query", type="string", location=RestApiParameterLocation.QUERY, is_required=True)
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource", params=parameters
    )
    arguments = {"query": "value"}
    expected_query_string = "query=value"
    assert operation.build_query_string(arguments) == expected_query_string


def test_build_query_string_missing_required_parameter():
    parameters = [
        RestApiParameter(name="query", type="string", location=RestApiParameterLocation.QUERY, is_required=True)
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource", params=parameters
    )
    arguments = {}
    with pytest.raises(
        FunctionExecutionException,
        match="No argument or value is provided for the `query` required parameter of the operation - `test`.",
    ):
        operation.build_query_string(arguments)


def test_build_query_string_with_optional_and_required_parameters():
    parameters = [
        RestApiParameter(
            name="required_param", type="string", location=RestApiParameterLocation.QUERY, is_required=True
        ),
        RestApiParameter(
            name="optional_param", type="string", location=RestApiParameterLocation.QUERY, is_required=False
        ),
    ]
    operation = RestApiOperation(
        id="test", method="GET", servers=["https://example.com/"], path="/resource", params=parameters
    )
    arguments = {"required_param": "required_value"}
    expected_query_string = "required_param=required_value"
    assert operation.build_query_string(arguments) == expected_query_string


def test_create_payload_artificial_parameter_with_text_plain():
    properties = [
        RestApiPayloadProperty(
            name="prop1",
            type="string",
            properties=[],
            description="Property description",
            is_required=True,
            default_value=None,
            schema=None,
        )
    ]
    request_body = RestApiPayload(
        media_type=RestApiOperation.MEDIA_TYPE_TEXT_PLAIN,
        properties=properties,
        description="Test description",
        schema="Test schema",
    )
    operation = RestApiOperation(
        id="test", method="POST", servers=["https://example.com/"], path="/resource", request_body=request_body
    )
    expected_parameter = RestApiParameter(
        name=operation.PAYLOAD_ARGUMENT_NAME,
        type="string",
        is_required=True,
        location=RestApiParameterLocation.BODY,
        style=RestApiParameterStyle.SIMPLE,
        description="Test description",
        schema="Test schema",
    )
    parameter = operation.create_payload_artificial_parameter(operation)
    assert parameter.name == expected_parameter.name
    assert parameter.type == expected_parameter.type
    assert parameter.is_required == expected_parameter.is_required
    assert parameter.location == expected_parameter.location
    assert parameter.style == expected_parameter.style
    assert parameter.description == expected_parameter.description
    assert parameter.schema == expected_parameter.schema


def test_create_payload_artificial_parameter_with_object():
    properties = [
        RestApiPayloadProperty(
            name="prop1",
            type="string",
            properties=[],
            description="Property description",
            is_required=True,
            default_value=None,
            schema=None,
        )
    ]
    request_body = RestApiPayload(
        media_type="application/json", properties=properties, description="Test description", schema="Test schema"
    )
    operation = RestApiOperation(
        id="test", method="POST", servers=["https://example.com/"], path="/resource", request_body=request_body
    )
    expected_parameter = RestApiParameter(
        name=operation.PAYLOAD_ARGUMENT_NAME,
        type="object",
        is_required=True,
        location=RestApiParameterLocation.BODY,
        style=RestApiParameterStyle.SIMPLE,
        description="Test description",
        schema="Test schema",
    )
    parameter = operation.create_payload_artificial_parameter(operation)
    assert parameter.name == expected_parameter.name
    assert parameter.type == expected_parameter.type
    assert parameter.is_required == expected_parameter.is_required
    assert parameter.location == expected_parameter.location
    assert parameter.style == expected_parameter.style
    assert parameter.description == expected_parameter.description
    assert parameter.schema == expected_parameter.schema


def test_create_payload_artificial_parameter_without_request_body():
    operation = RestApiOperation(id="test", method="POST", servers=["https://example.com/"], path="/resource")
    expected_parameter = RestApiParameter(
        name=operation.PAYLOAD_ARGUMENT_NAME,
        type="object",
        is_required=True,
        location=RestApiParameterLocation.BODY,
        style=RestApiParameterStyle.SIMPLE,
        description="REST API request body.",
        schema=None,
    )
    parameter = operation.create_payload_artificial_parameter(operation)
    assert parameter.name == expected_parameter.name
    assert parameter.type == expected_parameter.type
    assert parameter.is_required == expected_parameter.is_required
    assert parameter.location == expected_parameter.location
    assert parameter.style == expected_parameter.style
    assert parameter.description == expected_parameter.description
    assert parameter.schema == expected_parameter.schema


def test_create_content_type_artificial_parameter():
    operation = RestApiOperation(id="test", method="POST", servers=["https://example.com/"], path="/resource")
    expected_parameter = RestApiParameter(
        name=operation.CONTENT_TYPE_ARGUMENT_NAME,
        type="string",
        is_required=False,
        location=RestApiParameterLocation.BODY,
        style=RestApiParameterStyle.SIMPLE,
        description="Content type of REST API request body.",
    )
    parameter = operation.create_content_type_artificial_parameter()
    assert parameter.name == expected_parameter.name
    assert parameter.type == expected_parameter.type
    assert parameter.is_required == expected_parameter.is_required
    assert parameter.location == expected_parameter.location
    assert parameter.style == expected_parameter.style
    assert parameter.description == expected_parameter.description


def test_get_property_name_with_namespacing_and_root_property():
    operation = RestApiOperation(id="test", method="POST", servers=["https://example.com/"], path="/resource")
    property = RestApiPayloadProperty(name="child", type="string", properties=[], description="Property description")
    result = operation._get_property_name(property, root_property_name="root", enable_namespacing=True)
    assert result == "root.child"


def test_get_property_name_without_namespacing():
    operation = RestApiOperation(id="test", method="POST", servers=["https://example.com/"], path="/resource")
    property = RestApiPayloadProperty(name="child", type="string", properties=[], description="Property description")
    result = operation._get_property_name(property, root_property_name="root", enable_namespacing=False)
    assert result == "child"


def test_get_payload_parameters_with_metadata_and_text_plain():
    properties = [
        RestApiPayloadProperty(name="prop1", type="string", properties=[], description="Property description")
    ]
    request_body = RestApiPayload(
        media_type=RestApiOperation.MEDIA_TYPE_TEXT_PLAIN, properties=properties, description="Test description"
    )
    operation = RestApiOperation(
        id="test", method="POST", servers=["https://example.com/"], path="/resource", request_body=request_body
    )
    result = operation.get_payload_parameters(operation, use_parameters_from_metadata=True, enable_namespacing=True)
    assert len(result) == 1
    assert result[0].name == operation.PAYLOAD_ARGUMENT_NAME


def test_get_payload_parameters_with_metadata_and_json():
    properties = [
        RestApiPayloadProperty(name="prop1", type="string", properties=[], description="Property description")
    ]
    request_body = RestApiPayload(media_type="application/json", properties=properties, description="Test description")
    operation = RestApiOperation(
        id="test", method="POST", servers=["https://example.com/"], path="/resource", request_body=request_body
    )
    result = operation.get_payload_parameters(operation, use_parameters_from_metadata=True, enable_namespacing=True)
    assert len(result) == len(properties)
    assert result[0].name == properties[0].name


def test_get_payload_parameters_without_metadata():
    operation = RestApiOperation(id="test", method="POST", servers=["https://example.com/"], path="/resource")
    result = operation.get_payload_parameters(operation, use_parameters_from_metadata=False, enable_namespacing=False)
    assert len(result) == 2
    assert result[0].name == operation.PAYLOAD_ARGUMENT_NAME
    assert result[1].name == operation.CONTENT_TYPE_ARGUMENT_NAME


def test_get_payload_parameters_raises_exception():
    operation = RestApiOperation(
        id="test",
        method="POST",
        servers=["https://example.com/"],
        path="/resource",
        request_body=None,
    )
    with pytest.raises(
        Exception,
        match="Payload parameters cannot be retrieved from the `test` operation payload metadata because it is missing.",  # noqa: E501
    ):
        operation.get_payload_parameters(operation, use_parameters_from_metadata=True, enable_namespacing=False)


def test_get_default_response():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/resource")
    responses = {
        "200": RestApiExpectedResponse(description="Success", media_type="application/json", schema={"type": "object"}),
        "default": RestApiExpectedResponse(
            description="Default response", media_type="application/json", schema={"type": "object"}
        ),
    }
    preferred_responses = ["200", "default"]
    result = operation.get_default_response(responses, preferred_responses)
    assert result.description == "Success"


def test_get_default_response_with_default():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/resource")
    responses = {
        "default": RestApiExpectedResponse(
            description="Default response", media_type="application/json", schema={"type": "object"}
        )
    }
    preferred_responses = ["200", "default"]
    result = operation.get_default_response(responses, preferred_responses)
    assert result.description == "Default response"


def test_get_default_response_none():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/resource")
    responses = {}
    preferred_responses = ["200", "default"]
    result = operation.get_default_response(responses, preferred_responses)
    assert result is None


def test_get_default_return_parameter_with_response():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/resource")
    responses = {
        "200": RestApiExpectedResponse(description="Success", media_type="application/json", schema={"type": "object"}),
        "default": RestApiExpectedResponse(
            description="Default response", media_type="application/json", schema={"type": "object"}
        ),
    }
    operation.responses = responses
    result = operation.get_default_return_parameter(preferred_responses=["200", "default"])
    assert result.name == "return"
    assert result.description == "Success"
    assert result.type_ == "object"
    assert result.schema_data == {"type": "object"}


def test_get_default_return_parameter_none():
    operation = RestApiOperation(id="test", method="GET", servers=["https://example.com/"], path="/resource")
    responses = {}
    operation.responses = responses
    result = operation.get_default_return_parameter(preferred_responses=["200", "default"])
    assert result is not None
    assert result.name == "return"


@pytest.fixture
def openapi_runner():
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    operations = parser.create_rest_api_operations(parsed_doc)
    runner = OpenApiRunner(parsed_openapi_document=parsed_doc)
    return runner, operations


@pytest.fixture
def openapi_runner_with_url_override():
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    exec_settings = OpenAPIFunctionExecutionParameters(server_url_override="http://urloverride.com")
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=exec_settings)
    runner = OpenApiRunner(parsed_openapi_document=parsed_doc)
    return runner, operations


@pytest.fixture
def openapi_runner_with_auth_callback():
    async def dummy_auth_callback(**kwargs):
        return {"Authorization": "Bearer dummy-token"}

    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    exec_settings = OpenAPIFunctionExecutionParameters(server_url_override="http://urloverride.com")
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=exec_settings)
    runner = OpenApiRunner(
        parsed_openapi_document=parsed_doc,
        auth_callback=dummy_auth_callback,
    )
    return runner, operations


@pytest.fixture
def openapi_runner_with_predicate_callback():
    # Define a dummy predicate callback
    def predicate_callback(context):
        # Skip operations with DELETE method or containing 'internal' in the path
        return context.method != "DELETE" and "internal" not in context.path

    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    exec_settings = OpenAPIFunctionExecutionParameters(
        server_url_override="http://urloverride.com",
        operation_selection_predicate=predicate_callback,
    )
    operations = parser.create_rest_api_operations(parsed_doc, execution_settings=exec_settings)
    runner = OpenApiRunner(parsed_openapi_document=parsed_doc)
    return runner, operations, exec_settings


def test_predicate_callback_applied(openapi_runner_with_predicate_callback):
    _, operations, exec_settings = openapi_runner_with_predicate_callback

    skipped_operations = []
    executed_operations = []

    # Iterate over the operation objects instead of just the keys
    for operation_id, operation in operations.items():
        context = OperationSelectionPredicateContext(
            operation_id=operation_id,
            path=operation.path,
            method=operation.method,
            description=operation.description,
        )
        if not exec_settings.operation_selection_predicate(context):
            skipped_operations.append(operation_id)
        else:
            executed_operations.append(operation_id)

    # Assertions to verify the callback's behavior
    assert len(skipped_operations) > 0, "No operations were skipped, predicate not applied correctly"
    assert len(executed_operations) > 0, "All operations were skipped, predicate not applied correctly"

    # Example specific checks based on the callback logic
    for operation_id in skipped_operations:
        operation = operations[operation_id]
        assert operation.method == "DELETE" or "internal" in operation.path, (
            f"Predicate incorrectly skipped operation {operation_id}"
        )

    for operation_id in executed_operations:
        operation = operations[operation_id]
        assert operation.method != "DELETE" and "internal" not in operation.path, (
            f"Predicate incorrectly executed operation {operation_id}"
        )


@patch("aiohttp.ClientSession.request")
async def test_run_operation_with_invalid_request(mock_request, openapi_runner):
    runner, operations = openapi_runner
    operation = operations["getTodoById"]
    headers = {"Authorization": "Bearer abc123"}
    request_body = {"title": "Buy milk"}
    mock_request.return_value.__aenter__.return_value.text.return_value = 400
    with pytest.raises(Exception):
        await runner.run_operation(operation, headers=headers, request_body=request_body)


@patch("aiohttp.ClientSession.request")
async def test_run_operation_with_error(mock_request, openapi_runner):
    runner, operations = openapi_runner
    operation = operations["addTodo"]
    headers = {"Authorization": "Bearer abc123"}
    request_body = {"title": "Buy milk", "completed": False}
    mock_request.side_effect = Exception("Error")
    with pytest.raises(Exception):
        await runner.run_operation(operation, headers=headers, request_body=request_body)


def test_invalid_server_url_override():
    with pytest.raises(ValueError, match="Invalid server_url_override: invalid_url"):
        params = OpenAPIFunctionExecutionParameters(server_url_override="invalid_url")
        params.model_post_init(None)
