# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class TextPlugin(KernelBaseModel):
    """TextPlugin provides a set of functions to manipulate strings.

    Usage:
        kernel.add_plugin(TextPlugin(), plugin_name="text")

    Examples:
        KernelArguments["input"] = "  hello world  "
        {{text.trim $input}} => "hello world"

        KernelArguments["input"] = "  hello world  "
        {{text.trimStart $input}} => "hello world  "

        KernelArguments["input"] = "  hello world  "
        {{text.trimEnd $input}} => "  hello world"

        KernelArguments["input"] = "hello world"
        {{text.uppercase $input}} => "HELLO WORLD"

        KernelArguments["input"] = "HELLO WORLD"
        {{text.lowercase $input}} => "hello world"
    """

    @kernel_function(description="Trim whitespace from the start and end of a string.")
    def trim(self, input: str) -> str:
        """Trim whitespace from the start and end of a string.

        Example:
            KernelArguments["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return input.strip()

    @kernel_function(description="Trim whitespace from the start of a string.")
    def trim_start(self, input: str) -> str:
        """Trim whitespace from the start of a string.

        Example:
             KernelArguments["input"] = "  hello world  "
             {{input.trim $input}} => "hello world  "
        """
        return input.lstrip()

    @kernel_function(description="Trim whitespace from the end of a string.")
    def trim_end(self, input: str) -> str:
        """Trim whitespace from the end of a string.

        Example:
             KernelArguments["input"] = "  hello world  "
             {{input.trim $input}} => "  hello world"
        """
        return input.rstrip()

    @kernel_function(description="Convert a string to uppercase.")
    def uppercase(self, input: str) -> str:
        """Convert a string to uppercase.

        Example:
            KernelArguments["input"] = "hello world"
             {{input.uppercase $input}} => "HELLO WORLD"
        """
        return input.upper()

    @kernel_function(description="Convert a string to lowercase.")
    def lowercase(self, input: str) -> str:
        """Convert a string to lowercase.

        Example:
             KernelArguments["input"] = "HELLO WORLD"
             {{input.lowercase $input}} => "hello world"
        """
        return input.lower()
