# Copyright (c) Microsoft. All rights reserved.

from collections import OrderedDict
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.openapi_manager import OpenApiRunner
from semantic_kernel.exceptions import FunctionExecutionException


def test_build_full_url():
    runner = OpenApiRunner({})
    base_url = "http://example.com"
    query_string = "param1=value1&param2=value2"
    expected_url = "http://example.com?param1=value1&param2=value2"
    assert runner.build_full_url(base_url, query_string) == expected_url


def test_build_operation_url():
    runner = OpenApiRunner({})
    operation = MagicMock()
    operation.build_operation_url.return_value = "http://example.com"
    operation.build_query_string.return_value = "param1=value1"
    arguments = {}
    expected_url = "http://example.com?param1=value1"
    assert runner.build_operation_url(operation, arguments) == expected_url


def test_build_json_payload_dynamic_payload():
    runner = OpenApiRunner({}, enable_dynamic_payload=True)

    mock_property1 = Mock()
    mock_property2 = Mock()
    mock_property1.freeze = MagicMock()
    mock_property2.freeze = MagicMock()

    payload_metadata = RestApiPayload(
        media_type="application/json",
        properties=[mock_property1, mock_property2],
        description=None,
        schema=None,
    )
    arguments = {"property1": "value1", "property2": "value2"}

    runner.build_json_object = MagicMock(return_value={"property1": "value1", "property2": "value2"})

    payload_metadata.description = "A dynamic payload"
    assert payload_metadata.description == "A dynamic payload"

    payload_metadata.freeze()

    mock_property1.freeze.assert_called_once()
    mock_property2.freeze.assert_called_once()

    with pytest.raises(
        FunctionExecutionException, match="This `RestApiPayload` instance is frozen and cannot be modified."
    ):
        payload_metadata.description = "Should raise error"

    content, media_type = runner.build_json_payload(payload_metadata, arguments)

    runner.build_json_object.assert_called_once_with(payload_metadata.properties, arguments)
    assert content == '{"property1": "value1", "property2": "value2"}'
    assert media_type == "application/json"


def test_build_json_payload_no_metadata():
    runner = OpenApiRunner({}, enable_dynamic_payload=True)
    arguments = {}

    with pytest.raises(
        FunctionExecutionException, match="Payload can't be built dynamically due to the missing payload metadata."
    ):
        runner.build_json_payload(None, arguments)


def test_build_json_payload_static_payload():
    runner = OpenApiRunner({}, enable_dynamic_payload=False)
    arguments = {runner.payload_argument_name: '{"key": "value"}'}

    content, media_type = runner.build_json_payload(None, arguments)

    assert content == '{"key": "value"}'
    assert media_type == '{"key": "value"}'


def test_build_json_payload_no_payload():
    runner = OpenApiRunner({}, enable_dynamic_payload=False)
    arguments = {}

    with pytest.raises(
        FunctionExecutionException, match=f"No payload is provided by the argument '{runner.payload_argument_name}'."
    ):
        runner.build_json_payload(None, arguments)


def test_build_json_object():
    runner = OpenApiRunner({})
    properties = [MagicMock()]
    properties[0].name = "prop1"
    properties[0].type = "string"
    properties[0].is_required = True
    properties[0].properties = []
    arguments = {"prop1": "value1"}
    result = runner.build_json_object(properties, arguments)
    assert result == {"prop1": "value1"}


def test_build_json_object_missing_required_argument():
    runner = OpenApiRunner({})
    properties = [MagicMock()]
    properties[0].name = "prop1"
    properties[0].type = "string"
    properties[0].is_required = True
    properties[0].properties = []
    arguments = {}
    with pytest.raises(FunctionExecutionException, match="No argument is found for the 'prop1' payload property."):
        runner.build_json_object(properties, arguments)


def test_build_json_object_recursive():
    runner = OpenApiRunner({})

    nested_property1 = Mock()
    nested_property1.name = "property1.nested_property1"
    nested_property1.type = "string"
    nested_property1.is_required = True
    nested_property1.properties = []

    nested_property2 = Mock()
    nested_property2.name = "property2.nested_property2"
    nested_property2.type = "integer"
    nested_property2.is_required = False
    nested_property2.properties = []

    nested_properties = [nested_property1, nested_property2]

    property1 = Mock()
    property1.name = "property1"
    property1.type = "object"
    property1.properties = nested_properties
    property1.is_required = True

    property2 = Mock()
    property2.name = "property2"
    property2.type = "string"
    property2.is_required = False
    property2.properties = []

    properties = [property1, property2]

    arguments = {
        "property1.nested_property1": "nested_value1",
        "property1.nested_property2": 123,
        "property2": "value2",
    }

    result = runner.build_json_object(properties, arguments)

    expected_result = {"property1": {"property1.nested_property1": "nested_value1"}, "property2": "value2"}

    assert result == expected_result


def test_build_json_object_recursive_missing_required_argument():
    runner = OpenApiRunner({})

    nested_property1 = MagicMock()
    nested_property1.name = "nested_property1"
    nested_property1.type = "string"
    nested_property1.is_required = True

    nested_property2 = MagicMock()
    nested_property2.name = "nested_property2"
    nested_property2.type = "integer"
    nested_property2.is_required = False

    nested_properties = [nested_property1, nested_property2]

    property1 = MagicMock()
    property1.name = "property1"
    property1.type = "object"
    property1.properties = nested_properties
    property1.is_required = True

    property2 = MagicMock()
    property2.name = "property2"
    property2.type = "string"
    property2.is_required = False

    properties = [property1, property2]

    arguments = {
        "property1.nested_property2": 123,
        "property2": "value2",
    }

    with pytest.raises(
        FunctionExecutionException, match="No argument is found for the 'nested_property1' payload property."
    ):
        runner.build_json_object(properties, arguments)


def test_build_operation_payload_no_request_body():
    runner = OpenApiRunner({})
    operation = MagicMock()
    operation.request_body = None
    arguments = {}
    assert runner.build_operation_payload(operation, arguments) == (None, None)


def test_get_argument_name_for_payload_no_namespacing():
    runner = OpenApiRunner({}, enable_payload_namespacing=False)
    assert runner.get_argument_name_for_payload("prop1") == "prop1"


def test_get_argument_name_for_payload_with_namespacing():
    runner = OpenApiRunner({}, enable_payload_namespacing=True)
    assert runner.get_argument_name_for_payload("prop1", "namespace") == "namespace.prop1"


def test_build_operation_payload_with_request_body():
    runner = OpenApiRunner({})

    request_body = RestApiPayload(
        media_type="application/json",
        properties=["property1", "property2"],
        description=None,
        schema=None,
    )
    operation = Mock(spec=RestApiOperation)
    operation.request_body = request_body

    arguments = {"property1": "value1", "property2": "value2"}

    runner.build_json_payload = MagicMock(
        return_value=('{"property1": "value1", "property2": "value2"}', "application/json")
    )

    payload, media_type = runner.build_operation_payload(operation, arguments)

    runner.build_json_payload.assert_called_once_with(request_body, arguments)
    assert payload == '{"property1": "value1", "property2": "value2"}'
    assert media_type == "application/json"


def test_build_operation_payload_without_request_body():
    runner = OpenApiRunner({})

    operation = Mock(spec=RestApiOperation)
    operation.request_body = None

    arguments = {runner.payload_argument_name: '{"property1": "value1"}'}

    runner.build_json_payload = MagicMock(return_value=('{"property1": "value1"}', "application/json"))

    payload, media_type = runner.build_operation_payload(operation, arguments)

    runner.build_json_payload.assert_not_called()
    assert payload is None
    assert media_type is None


def test_build_operation_payload_no_request_body_no_payload_argument():
    runner = OpenApiRunner({})

    operation = Mock(spec=RestApiOperation)
    operation.request_body = None

    arguments = {}

    payload, media_type = runner.build_operation_payload(operation, arguments)

    assert payload is None
    assert media_type is None


def test_get_first_response_media_type():
    runner = OpenApiRunner({})
    responses = OrderedDict()
    response = MagicMock()
    response.media_type = "application/xml"
    responses["200"] = response
    assert runner._get_first_response_media_type(responses) == "application/xml"


def test_get_first_response_media_type_default():
    runner = OpenApiRunner({})
    responses = OrderedDict()
    assert runner._get_first_response_media_type(responses) == runner.media_type_application_json


async def test_run_operation():
    runner = OpenApiRunner({})
    operation = MagicMock()
    arguments = {}
    options = MagicMock()
    options.server_url_override = None
    options.api_host_url = None
    operation.build_headers.return_value = {"header": "value"}
    operation.method = "GET"
    runner.build_operation_url = MagicMock(return_value="http://example.com")
    runner.build_operation_payload = MagicMock(return_value=('{"key": "value"}', "application/json"))

    response = MagicMock()
    response.media_type = "application/json"
    operation.responses = OrderedDict([("200", response)])

    async def mock_request(*args, **kwargs):
        response = MagicMock()
        response.text = "response text"
        return response

    runner.http_client = AsyncMock()
    runner.http_client.request = mock_request

    runner.auth_callback = AsyncMock(return_value={"Authorization": "Bearer token"})

    runner.http_client.headers = {"header": "client-value"}

    result = await runner.run_operation(operation, arguments, options)
    assert result == "response text"
