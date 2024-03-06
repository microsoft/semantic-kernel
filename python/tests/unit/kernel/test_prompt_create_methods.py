# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock, Mock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.exceptions.template_engine_exceptions import TemplateSyntaxError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


def create_mock_function(name) -> KernelFunction:
    kernel_function_metadata = KernelFunctionMetadata(
        name=name,
        plugin_name="TestPlugin",
        description="Test",
        parameters=[],
        is_prompt=True,
        is_asynchronous=True,
    )
    mock_function = Mock(spec=KernelFunction)
    mock_function.metadata = kernel_function_metadata
    mock_function.name = kernel_function_metadata.name
    mock_function.plugin_name = kernel_function_metadata.plugin_name
    mock_function.description = kernel_function_metadata.description

    return mock_function


@pytest.mark.asyncio
async def test_invoke_prompt_success():
    mock_function = create_mock_function("test_function")
    with patch(
        "semantic_kernel.kernel.KernelFunction.from_prompt", return_value=MagicMock()
    ) as mock_from_prompt, patch(
        "semantic_kernel.kernel.Kernel.invoke",
        return_value=FunctionResult(function=mock_function.metadata, value="test", metadata={}),
    ) as mock_invoke:
        kernel = Kernel()
        result = await kernel.invoke_prompt(
            function_name="test_function",
            plugin_name="test_plugin",
            prompt="test_prompt",
            template_format="test_format",
            arg1="val1",
        )
        mock_from_prompt.assert_called_once_with(
            function_name="test_function",
            plugin_name="test_plugin",
            prompt="test_prompt",
            template_format="test_format",
        )
        assert mock_invoke.called
        assert isinstance(result, FunctionResult)


@pytest.mark.asyncio
async def test_invoke_prompt_no_prompt_error():
    kernel = Kernel()
    with pytest.raises(TemplateSyntaxError):
        await kernel.invoke_prompt(
            function_name="test_function",
            plugin_name="test_plugin",
            prompt="",
        )
