# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter import (
    RestApiOperationParameter,
    RestApiOperationParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.openapi_manager import (
    _create_function_from_operation,
)
from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
async def test_run_openapi_operation_success(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiOperationParameter(
            name="param1", type="string", location=RestApiOperationParameterLocation.QUERY, is_required=True
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

        kwargs = {"param1": "value1"}

        result = await run_openapi_operation(kernel, **kwargs)
        assert str(result) == "Operation Result"
        run_operation_mock.assert_called_once()


@pytest.mark.asyncio
async def test_run_openapi_operation_missing_required_param(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiOperationParameter(
            name="param1", type="string", location=RestApiOperationParameterLocation.QUERY, is_required=True
        )
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


@pytest.mark.asyncio
async def test_run_openapi_operation_runner_exception(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiOperationParameter(
            name="param1", type="string", location=RestApiOperationParameterLocation.QUERY, is_required=True
        )
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


@pytest.mark.asyncio
async def test_run_openapi_operation_alternative_name(kernel: Kernel):
    runner = AsyncMock()
    operation = MagicMock()
    operation.id = "test_operation"
    operation.summary = "Test Summary"
    operation.description = "Test Description"
    operation.get_parameters.return_value = [
        RestApiOperationParameter(
            name="param1",
            type="string",
            location=RestApiOperationParameterLocation.QUERY,
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
