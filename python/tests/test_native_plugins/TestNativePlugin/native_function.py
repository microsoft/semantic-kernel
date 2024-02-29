import sys

from semantic_kernel.functions.kernel_function_decorator import kernel_function

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


class TestNativeEchoBotPlugin:
    """
    Description: Test Native Plugin for testing purposes
    """

    @kernel_function(
        description="Echo for input text",
        name="echoAsync",
    )
    async def echo(self, text: Annotated[str, "The text to echo"]) -> str:
        """
        Echo for input text

        Example:
            "hello world" => "hello world"
        Args:
            text -- The text to echo

        Returns:
            input text
        """
        return text
