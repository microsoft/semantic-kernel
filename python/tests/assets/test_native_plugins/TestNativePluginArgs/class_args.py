import sys
from typing import Optional

from semantic_kernel.functions.kernel_function_decorator import kernel_function

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


class TestNativeEchoBotPlugin:
    """
    Description: Test Native Plugin for testing purposes
    """

    def __init__(self, static_input: Optional[str] = None):
        self.static_input = static_input or ""

    @kernel_function(
        description="Echo for input text with static",
        name="echo",
    )
    def echo(self, text: Annotated[str, "The text to echo"]) -> str:
        """
        Echo for input text with a static input

        Example:
            "hello world" => "hello world"
        Args:
            text -- The text to echo

        Returns:
            input text
        """
        return self.static_input + text
