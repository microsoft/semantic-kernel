# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter import (
    RestApiParameter,
    RestApiParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_run_options import RestApiRunOptions
from semantic_kernel.connectors.openapi_plugin.openapi_manager import (
    _create_function_from_operation,
    create_functions_from_openapi,
)
from semantic_kernel.connectors.openapi_plugin.openapi_runner import OpenApiRunner
from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel import Kernel


async def test_run_openapi_operation_success(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiParameter(name="param1", type="string", location=RestApiParameterLocation.QUERY, is_required=True)
    ]

    execution_parameters = MagicMock()
    execution_parameters.server_url_override = "https://override.com"
    execution_parameters.enable_dynamic_payload = True
    execution_parameters.enable_payload_namespacing = False

    plugin_name = "TestPlugin"
    document_uri = "https://document.com"

    run_operation_mock = AsyncMock(return_value="Operation Result")
    runner.run_operation = run_operation_mock

    with patch.object(
        operation,
        "get_default_return_parameter",
        return_value=KernelParameterMetadata(
            name="return",
            description="Return description",
            default_value=None,
            type_="string",
            type_object=None,
            is_required=False,
            schema_data={"type": "string"},
        ),
    ):

        @kernel_function(description=operation.summary, name=operation.id)
        async def run_openapi_operation(kernel, **kwargs):
            return await _create_function_from_operation(
                runner, operation, plugin_name, execution_parameters, document_uri
            )(kernel, **kwargs)

        kwargs = {"param1": "value1"}

        result = await run_openapi_operation(kernel, **kwargs)
        assert str(result) == "Operation Result"
        run_operation_mock.assert_called_once()


async def test_run_openapi_operation_missing_required_param(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiParameter(name="param1", type="string", location=RestApiParameterLocation.QUERY, is_required=True)
    ]

    execution_parameters = MagicMock()
    execution_parameters.server_url_override = "https://override.com"
    execution_parameters.enable_dynamic_payload = True
    execution_parameters.enable_payload_namespacing = False

    plugin_name = "TestPlugin"
    document_uri = "https://document.com"

    with patch.object(
        operation,
        "get_default_return_parameter",
        return_value=KernelParameterMetadata(
            name="return",
            description="Return description",
            default_value=None,
            type_="string",
            type_object=None,
            is_required=False,
            schema_data={"type": "string"},
        ),
    ):

        @kernel_function(description=operation.summary, name=operation.id)
        async def run_openapi_operation(kernel, **kwargs):
            return await _create_function_from_operation(
                runner, operation, plugin_name, execution_parameters, document_uri
            )(kernel, **kwargs)

        kwargs = {}

        with pytest.raises(
            FunctionExecutionException,
            match="Parameter param1 is required but not provided in the arguments",
        ):
            await run_openapi_operation(kernel, **kwargs)


async def test_run_openapi_operation_runner_exception(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiParameter(name="param1", type="string", location=RestApiParameterLocation.QUERY, is_required=True)
    ]

    execution_parameters = MagicMock()
    execution_parameters.server_url_override = "https://override.com"
    execution_parameters.enable_dynamic_payload = True
    execution_parameters.enable_payload_namespacing = False

    plugin_name = "TestPlugin"
    document_uri = "https://document.com"

    run_operation_mock = AsyncMock(side_effect=Exception("Runner Exception"))
    runner.run_operation = run_operation_mock

    with patch.object(
        operation,
        "get_default_return_parameter",
        return_value=KernelParameterMetadata(
            name="return",
            description="Return description",
            default_value=None,
            type_="string",
            type_object=None,
            is_required=False,
            schema_data={"type": "string"},
        ),
    ):

        @kernel_function(description=operation.summary, name=operation.id)
        async def run_openapi_operation(kernel, **kwargs):
            return await _create_function_from_operation(
                runner, operation, plugin_name, execution_parameters, document_uri
            )(kernel, **kwargs)

        kwargs = {"param1": "value1"}

        with pytest.raises(FunctionExecutionException, match="Error running OpenAPI operation: test_operation"):
            await run_openapi_operation(kernel, **kwargs)


async def test_run_openapi_operation_alternative_name(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiParameter(
            name="param1",
            type="string",
            location=RestApiParameterLocation.QUERY,
            is_required=True,
            alternative_name="alt_param1",
        )
    ]

    execution_parameters = MagicMock()
    execution_parameters.server_url_override = "https://override.com"
    execution_parameters.enable_dynamic_payload = True
    execution_parameters.enable_payload_namespacing = False

    plugin_name = "TestPlugin"
    document_uri = "https://document.com"

    run_operation_mock = AsyncMock(return_value="Operation Result")
    runner.run_operation = run_operation_mock

    with patch.object(
        operation,
        "get_default_return_parameter",
        return_value=KernelParameterMetadata(
            name="return",
            description="Return description",
            default_value=None,
            type_="string",
            type_object=None,
            is_required=False,
            schema_data={"type": "string"},
        ),
    ):

        @kernel_function(description=operation.summary, name=operation.id)
        async def run_openapi_operation(kernel, **kwargs):
            return await _create_function_from_operation(
                runner, operation, plugin_name, execution_parameters, document_uri
            )(kernel, **kwargs)

        kwargs = {"alt_param1": "value1"}

        result = await run_openapi_operation(kernel, **kwargs)
        assert str(result) == "Operation Result"
        run_operation_mock.assert_called_once()
        assert runner.run_operation.call_args[0][1]["param1"] == "value1"


@patch("semantic_kernel.connectors.openapi_plugin.openapi_parser.OpenApiParser.parse", return_value=None)
async def test_create_functions_from_openapi_raises_exception(mock_parse):
    """Test that an exception is raised when parsing fails."""
    with pytest.raises(FunctionExecutionException, match="Error parsing OpenAPI document: test_openapi_document_path"):
        create_functions_from_openapi(plugin_name="test_plugin", openapi_document_path="test_openapi_document_path")

    mock_parse.assert_called_once_with("test_openapi_document_path")


async def test_run_operation_uses_timeout_from_run_options():
    minimal_openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }
    runner = OpenApiRunner(parsed_openapi_document=minimal_openapi_spec)
    operation = MagicMock()
    operation.method = "GET"
    operation.build_headers.return_value = {}
    operation.build_operation_payload.return_value = ("{}", None)
    operation.responses = {}
    operation.responses = {}
    operation.operation_id = "test_id"

    desired_timeout = 3.3

    with (
        patch("httpx.AsyncClient.__aenter__", new_callable=AsyncMock) as mock_enter,
        patch("httpx.AsyncClient.__aexit__", new_callable=AsyncMock),
        patch("httpx.AsyncClient.__init__", return_value=None) as mock_init,
    ):
        mock_client = MagicMock()
        mock_enter.return_value = mock_client
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "FAKE_RESPONSE"
        mock_client.request = AsyncMock(return_value=mock_response)

        operation.build_query_string.return_value = ""
        operation.server_url = "https://api.example.com"
        operation.path = "/test"
        operation.build_operation_url.return_value = "https://api.example.com/test"
        result = await runner.run_operation(
            operation=operation, arguments=None, options=RestApiRunOptions(timeout=desired_timeout)
        )

        assert result == "FAKE_RESPONSE"
        found = False
        for call_args in mock_init.call_args_list:
            if "timeout" in call_args.kwargs and call_args.kwargs["timeout"] == desired_timeout:
                found = True
                break
        assert found, f"httpx.AsyncClient was not called with timeout={desired_timeout}"
