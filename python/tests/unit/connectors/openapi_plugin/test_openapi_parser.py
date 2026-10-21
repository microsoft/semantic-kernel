# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.openapi_manager import OpenApiParser, create_functions_from_openapi
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError
from semantic_kernel.functions import KernelFunctionFromMethod, KernelFunctionMetadata, KernelParameterMetadata

current_dir = os.path.dirname(os.path.abspath(__file__))


def test_parse_parameters_missing_in_field():
    parser = OpenApiParser()
    parameters = [{"name": "param1", "schema": {"type": "string"}}]
    with pytest.raises(PluginInitializationError, match="Parameter param1 is missing 'in' field"):
        parser._parse_parameters(parameters)


def test_parse_parameters_get_query():
    """Verify whether the get request query parameter can be successfully parsed"""
    openapi_fcs: list[KernelFunctionFromMethod] = create_functions_from_openapi(
        plugin_name="todo",
        openapi_document_path=os.path.join(current_dir, "openapi_todo.yaml"),
        execution_settings=None,
    )

    get_todo_list: list[KernelFunctionMetadata] = [
        f.metadata for f in openapi_fcs if f.metadata.name == "get_todo_list"
    ]

    assert get_todo_list

    get_todo_params: list[KernelParameterMetadata] = get_todo_list[0].parameters
    assert get_todo_params
    assert get_todo_params[0].name == "listName"
    assert get_todo_params[0].description == "todo list group name description"
    assert get_todo_params[0].is_required
    assert get_todo_params[0].schema_data
    assert get_todo_params[0].schema_data.get("type") == "string"
    assert get_todo_params[0].schema_data.get("description") == "todo list group name"


def test_parse_parameters_post_request_body():
    """Verify whether the post request body parameter can be successfully parsed"""
    openapi_fcs: list[KernelFunctionFromMethod] = create_functions_from_openapi(
        plugin_name="todo",
        openapi_document_path=os.path.join(current_dir, "openapi_todo.yaml"),
        execution_settings=None,
    )

    add_todo_list: list[KernelFunctionMetadata] = [
        f.metadata for f in openapi_fcs if f.metadata.name == "add_todo_list"
    ]

    assert add_todo_list

    add_todo_params: list[KernelParameterMetadata] = add_todo_list[0].parameters

    assert add_todo_params
    assert add_todo_params[0].name == "task"
    assert add_todo_params[0].description == "task name"
    assert add_todo_params[0].is_required
    assert add_todo_params[0].schema_data
    assert add_todo_params[0].schema_data.get("type") == "string"
    assert add_todo_params[0].schema_data.get("description") == "task name"

    assert add_todo_params[1].name == "listName"
    assert add_todo_params[1].description == "task group name"
    assert not add_todo_params[1].is_required
    assert add_todo_params[1].schema_data
    assert add_todo_params[1].schema_data.get("type") == "string"
    assert add_todo_params[1].schema_data.get("description") == "task group name"


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


def generate_security_member_data():
    return [
        (
            "no-securityV3_0.json",
            {
                "NoSecurity": [],
                "Security": ["apiKey"],
                "SecurityAndScope": ["apiKey"],
            },
        ),
        (
            "apikey-securityV3_0.json",
            {
                "NoSecurity": [],
                "Security": ["apiKey"],
                "SecurityAndScope": ["apiKey"],
            },
        ),
        (
            "oauth-securityV3_0.json",
            {
                "NoSecurity": [],
                "Security": ["oauth2"],
                "SecurityAndScope": ["oauth2"],
            },
        ),
    ]


@pytest.mark.parametrize("document_file_name, security_type_map", generate_security_member_data())
def test_it_adds_security_metadata_to_operation(document_file_name, security_type_map):
    # Arrange
    current_dir = os.path.dirname(__file__)
    openapi_document_path = os.path.join(current_dir, document_file_name)

    # Act
    plugin_functions = create_functions_from_openapi(
        plugin_name="fakePlugin",
        openapi_document_path=openapi_document_path,
        execution_settings=None,
    )

    # Assert
    for function in plugin_functions:
        additional_properties = function.metadata.additional_properties
        assert "operation" in additional_properties

        function_name = function.metadata.name
        security_types = security_type_map.get(function_name, [])

        operation = additional_properties["operation"]
        assert isinstance(operation, RestApiOperation)
        assert operation is not None
        assert operation.security_requirements is not None
        assert len(operation.security_requirements) == len(security_types)

        for security_type in security_types:
            found = False
            for security_requirement in operation.security_requirements:
                for scheme in security_requirement:
                    if scheme.security_scheme_type.lower() == security_type.lower():
                        found = True
                        break
                if found:
                    break
            assert found, f"Security type '{security_type}' not found in operation '{operation.id}'"


def test_no_operationid_raises_error():
    """Test that OpenAPI spec without operationId raises PluginInitializationError."""
    no_op_path = os.path.join(current_dir, "no-operationid-openapi.yaml")
    with pytest.raises(PluginInitializationError, match="operationId missing"):
        create_functions_from_openapi(
            plugin_name="noOpTest",
            openapi_document_path=no_op_path,
            execution_settings=None,
        )


def test_parse_blocks_external_http_refs_by_default():
    """Verify that external HTTP $ref resolution is not enabled by default."""
    from unittest.mock import MagicMock, patch

    from prance.util.resolver import RESOLVE_HTTP, RESOLVE_INTERNAL

    with patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.ResolvingParser") as mock_parser_cls:
        mock_parser_cls.return_value = MagicMock(specification={"openapi": "3.0.0"})
        parser = OpenApiParser()
        parser.parse("dummy_path.yaml")

        mock_parser_cls.assert_called_once()
        call_kwargs = mock_parser_cls.call_args
        resolve_types = call_kwargs.kwargs.get("resolve_types") or call_kwargs[1].get("resolve_types")
        assert resolve_types == RESOLVE_INTERNAL, (
            f"Expected only RESOLVE_INTERNAL ({RESOLVE_INTERNAL}), got {resolve_types}"
        )
        assert not (resolve_types & RESOLVE_HTTP), "RESOLVE_HTTP should not be set by default"


def test_parse_resolves_internal_refs_by_default(tmp_path):
    """Verify that internal $ref references are still resolved by default."""
    openapi_spec = tmp_path / "spec_with_internal_ref.yaml"
    openapi_spec.write_text(
        """
openapi: 3.0.0
info:
  title: Internal Ref Test
  version: 1.0.0
servers:
  - url: http://example.com
paths:
  /test:
    get:
      operationId: testOp
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/TestSchema"
components:
  schemas:
    TestSchema:
      type: object
      properties:
        name:
          type: string
""",
        encoding="utf-8",
    )

    parser = OpenApiParser()
    result = parser.parse(str(openapi_spec))

    # Internal $ref should be resolved
    response_schema = result["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" not in response_schema, "Internal $ref should be resolved"
    assert response_schema["type"] == "object"
    assert "name" in response_schema["properties"]


def test_parse_blocks_file_refs_by_default():
    """Verify that local file $ref resolution is not enabled by default."""
    from unittest.mock import MagicMock, patch

    from prance.util.resolver import RESOLVE_FILES, RESOLVE_INTERNAL

    with patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.ResolvingParser") as mock_parser_cls:
        mock_parser_cls.return_value = MagicMock(specification={"openapi": "3.0.0"})
        parser = OpenApiParser()
        parser.parse("dummy_path.yaml")

        call_kwargs = mock_parser_cls.call_args
        resolve_types = call_kwargs.kwargs.get("resolve_types") or call_kwargs[1].get("resolve_types")
        assert resolve_types == RESOLVE_INTERNAL, (
            f"Expected only RESOLVE_INTERNAL ({RESOLVE_INTERNAL}), got {resolve_types}"
        )
        assert not (resolve_types & RESOLVE_FILES), "RESOLVE_FILES should not be set by default"


def test_parse_enables_file_refs_when_requested():
    """Verify that local file $ref resolution is enabled when explicitly requested."""
    from unittest.mock import MagicMock, patch

    from prance.util.resolver import RESOLVE_FILES, RESOLVE_INTERNAL

    with patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.ResolvingParser") as mock_parser_cls:
        mock_parser_cls.return_value = MagicMock(specification={"openapi": "3.0.0"})
        parser = OpenApiParser()
        parser.parse("dummy_path.yaml", enable_file_ref_resolution=True)

        call_kwargs = mock_parser_cls.call_args
        resolve_types = call_kwargs.kwargs.get("resolve_types") or call_kwargs[1].get("resolve_types")
        assert resolve_types == (RESOLVE_INTERNAL | RESOLVE_FILES), (
            f"Expected RESOLVE_INTERNAL | RESOLVE_FILES, got {resolve_types}"
        )


def test_parse_enables_http_refs_when_requested():
    """Verify that HTTP $ref resolution is enabled when explicitly requested."""
    from unittest.mock import MagicMock, patch

    from prance.util.resolver import RESOLVE_HTTP, RESOLVE_INTERNAL

    with patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.ResolvingParser") as mock_parser_cls:
        mock_parser_cls.return_value = MagicMock(specification={"openapi": "3.0.0"})
        parser = OpenApiParser()
        parser.parse("dummy_path.yaml", enable_http_ref_resolution=True)

        call_kwargs = mock_parser_cls.call_args
        resolve_types = call_kwargs.kwargs.get("resolve_types") or call_kwargs[1].get("resolve_types")
        assert resolve_types == (RESOLVE_INTERNAL | RESOLVE_HTTP), (
            f"Expected RESOLVE_INTERNAL | RESOLVE_HTTP, got {resolve_types}"
        )


def test_parse_enables_both_file_and_http_refs_when_requested():
    """Verify both file and HTTP $ref resolution work together."""
    from unittest.mock import MagicMock, patch

    from prance.util.resolver import RESOLVE_FILES, RESOLVE_HTTP, RESOLVE_INTERNAL

    with patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.ResolvingParser") as mock_parser_cls:
        mock_parser_cls.return_value = MagicMock(specification={"openapi": "3.0.0"})
        parser = OpenApiParser()
        parser.parse("dummy_path.yaml", enable_file_ref_resolution=True, enable_http_ref_resolution=True)

        call_kwargs = mock_parser_cls.call_args
        resolve_types = call_kwargs.kwargs.get("resolve_types") or call_kwargs[1].get("resolve_types")
        assert resolve_types == (RESOLVE_INTERNAL | RESOLVE_FILES | RESOLVE_HTTP), (
            f"Expected RESOLVE_INTERNAL | RESOLVE_FILES | RESOLVE_HTTP, got {resolve_types}"
        )


def test_create_functions_propagates_enable_http_ref_resolution():
    """Verify enable_http_ref_resolution=True is propagated from settings to parser."""
    from unittest.mock import patch

    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }

    settings = OpenAPIFunctionExecutionParameters(enable_http_ref_resolution=True)

    with patch.object(OpenApiParser, "parse", return_value=minimal_spec) as mock_parse:
        create_functions_from_openapi(
            plugin_name="testPlugin",
            openapi_document_path="dummy.yaml",
            execution_settings=settings,
        )
        mock_parse.assert_called_once_with(
            "dummy.yaml",
            enable_file_ref_resolution=False,
            enable_http_ref_resolution=True,
        )


def test_create_functions_propagates_enable_file_ref_resolution():
    """Verify enable_file_ref_resolution=True is propagated from settings to parser."""
    from unittest.mock import patch

    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )

    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }

    settings = OpenAPIFunctionExecutionParameters(enable_file_ref_resolution=True)

    with patch.object(OpenApiParser, "parse", return_value=minimal_spec) as mock_parse:
        create_functions_from_openapi(
            plugin_name="testPlugin",
            openapi_document_path="dummy.yaml",
            execution_settings=settings,
        )
        mock_parse.assert_called_once_with(
            "dummy.yaml",
            enable_file_ref_resolution=True,
            enable_http_ref_resolution=False,
        )
