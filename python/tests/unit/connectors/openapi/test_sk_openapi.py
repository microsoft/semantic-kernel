import os
from unittest.mock import patch

import pytest
import yaml
from openapi_core import Spec

from semantic_kernel.connectors.openapi.sk_openapi import (
    OpenApiParser,
    OpenApiRunner,
    PreparedRestApiRequest,
    RestApiOperation,
)

directory = os.path.dirname(os.path.realpath(__file__))
openapi_document = directory + "/openapi.yaml"
invalid_openapi_document = directory + "/invalid_openapi.yaml"
with open(openapi_document, "r") as f:
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
    server_url="http://example.com",
    path="/todos/{id}",
    summary="Update a todo by ID",
    parameters=[
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
    responses={"200": {"description": "OK"}},
)

"""RestApiOperation tests"""


def test_prepare_request_with_path_params():
    path_params = {"id": 1}
    query_params = {"completed": False}
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk", "completed": False}
    expected_request = PreparedRestApiRequest(
        method="PUT",
        url="http://example.com/todos/1",
        params={"completed": False},
        headers={"Authorization": "Bearer abc123", "Content-Type": "application/json"},
        payload={"title": "Buy milk", "completed": False},
    )
    actual_request = put_operation.prepare_request(
        path_params=path_params,
        query_params=query_params,
        headers=headers,
        payload=payload,
    )
    assert str(actual_request) == str(expected_request)


def test_prepare_request_with_missing_path_param():
    path_params = {}
    query_params = {"completed": False}
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk", "completed": False}
    with pytest.raises(ValueError):
        put_operation.prepare_request(
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            payload=payload,
        )


def test_prepare_request_with_default_query_param():
    path_params = {"id": 1}
    query_params = {}
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk", "completed": False}
    expected_request = PreparedRestApiRequest(
        method="PUT",
        url="http://example.com/todos/1",
        params={},
        headers={"Authorization": "Bearer abc123", "Content-Type": "application/json"},
        payload={"title": "Buy milk", "completed": False},
    )
    actual_request = put_operation.prepare_request(
        path_params=path_params,
        query_params=query_params,
        headers=headers,
        payload=payload,
    )
    assert str(actual_request) == str(expected_request)


def test_prepare_request_with_default_header():
    path_params = {"id": 1}
    query_params = {"completed": False}
    headers = {}
    payload = {"title": "Buy milk", "completed": False}
    expected_request = PreparedRestApiRequest(
        method="PUT",
        url="http://example.com/todos/1",
        params={"completed": False},
        headers={"Content-Type": "application/json"},
        payload={"title": "Buy milk", "completed": False},
    )
    actual_request = put_operation.prepare_request(
        path_params=path_params,
        query_params=query_params,
        headers=headers,
        payload=payload,
    )
    assert str(actual_request) == str(expected_request)


def test_prepare_request_with_no_payload():
    path_params = {"id": 1}
    query_params = {"completed": False}
    headers = {"Authorization": "Bearer abc123"}
    payload = None
    with pytest.raises(ValueError):
        put_operation.prepare_request(
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            payload=payload,
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


def test_create_rest_api_operations():
    parser = OpenApiParser()
    result = parser.create_rest_api_operations(parser.parse(openapi_document))
    assert all([operation in result for operation in operation_names])

    get_todos_rest_api_operation = result["getTodos"]
    assert get_todos_rest_api_operation.method.lower() == "get"
    assert get_todos_rest_api_operation.path == "/todos"
    assert get_todos_rest_api_operation.parameters == [
        {
            "name": "Authorization",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "description": "The authorization token"},
        }
    ]
    assert get_todos_rest_api_operation.id == "getTodos"
    assert get_todos_rest_api_operation.request_body is None

    add_todo_rest_api_operation = result["addTodo"]
    assert add_todo_rest_api_operation.method.lower() == "post"
    assert add_todo_rest_api_operation.path == "/todos"
    assert add_todo_rest_api_operation.parameters == [
        {
            "name": "Authorization",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "description": "The authorization token"},
        }
    ]
    assert add_todo_rest_api_operation.id == "addTodo"
    assert add_todo_rest_api_operation.request_body == {
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
    }


@pytest.fixture
def openapi_runner():
    parser = OpenApiParser()
    parsed_doc = parser.parse(openapi_document)
    operations = parser.create_rest_api_operations(parsed_doc)
    runner = OpenApiRunner(parsed_openapi_document=parsed_doc)
    return runner, operations


@patch("aiohttp.ClientSession.request")
@pytest.mark.asyncio
async def test_run_operation_with_valid_request(mock_request, openapi_runner):
    runner, operations = openapi_runner
    operation = operations["addTodo"]
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk", "completed": False}
    mock_request.return_value.__aenter__.return_value.text.return_value = 200
    response = await runner.run_operation(operation, headers=headers, payload=payload)
    assert response == 200


@patch("aiohttp.ClientSession.request")
@pytest.mark.asyncio
async def test_run_operation_with_invalid_request(mock_request, openapi_runner):
    runner, operations = openapi_runner
    operation = operations["getTodoById"]
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk"}
    mock_request.return_value.__aenter__.return_value.text.return_value = 400
    with pytest.raises(Exception):
        await runner.run_operation(operation, headers=headers, payload=payload)


@patch("aiohttp.ClientSession.request")
@pytest.mark.asyncio
async def test_run_operation_with_error(mock_request, openapi_runner):
    runner, operations = openapi_runner
    operation = operations["addTodo"]
    headers = {"Authorization": "Bearer abc123"}
    payload = {"title": "Buy milk", "completed": False}
    mock_request.side_effect = Exception("Error")
    with pytest.raises(Exception):
        await runner.run_operation(operation, headers=headers, payload=payload)
