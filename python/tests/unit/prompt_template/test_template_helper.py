# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.const import JINJA2_TEMPLATE_FORMAT_NAME
from semantic_kernel.prompt_template.utils.template_function_helpers import create_template_helper_from_function


def test_create_helpers(kernel: Kernel):
    # Arrange
    function = KernelFunctionFromMethod(kernel_function(lambda x: x + 1, name="test"), plugin_name="test")
    base_arguments = {}
    template_format = JINJA2_TEMPLATE_FORMAT_NAME
    allow_dangerously_set_content = False
    enable_async = False

    # Act
    result = create_template_helper_from_function(
        function, kernel, base_arguments, template_format, allow_dangerously_set_content, enable_async
    )

    # Assert
    assert int(str(result(x=1))) == 2


@pytest.mark.parametrize(
    "template_format, enable_async, exception",
    [
        ("jinja2", True, False),
        ("jinja2", False, False),
        ("handlebars", True, True),
        ("handlebars", False, False),
        ("semantic-kernel", False, True),
        ("semantic-kernel", True, True),
    ],
)
async def test_create_helpers_fail(kernel: Kernel, template_format: str, enable_async: bool, exception: bool):
    # Arrange
    function = KernelFunctionFromMethod(kernel_function(lambda x: x + 1, name="test"), plugin_name="test")

    if exception:
        with pytest.raises(ValueError):
            create_template_helper_from_function(function, kernel, {}, template_format, False, enable_async)
        return
    result = create_template_helper_from_function(function, kernel, {}, template_format, False, enable_async)
    if enable_async:
        res = await result(x=1)
        assert int(str(res)) == 2
    else:
        assert int(str(result(x=1))) == 2
