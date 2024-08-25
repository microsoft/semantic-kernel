# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function


@kernel_function(
    description="Echo for input text",
    name="echoAsync",
)
async def echo(text: Annotated[str, "The text to echo"]) -> str:
    """Echo for input text

    Example:
        "hello world" => "hello world"
    Args:
        text -- The text to echo

    Returns:
        input text
    """
    return text
