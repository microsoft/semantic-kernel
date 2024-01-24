# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition import kernel_function


class TextPlugin(KernelBaseModel):
    """
    TextPlugin provides a set of functions to manipulate strings.

    Usage:
        kernel.import_plugin(TextPlugin(), plugin_name="text")

    Examples:
        KernelContext["input"] = "  hello world  "
        {{text.trim $input}} => "hello world"

        KernelContext["input"] = "  hello world  "
        {{text.trimStart $input} => "hello world  "

        KernelContext["input"] = "  hello world  "
        {{text.trimEnd $input} => "  hello world"

        KernelContext["input"] = "hello world"
        {{text.uppercase $input}} => "HELLO WORLD"

        KernelContext["input"] = "HELLO WORLD"
        {{text.lowercase $input}} => "hello world"
    """

    @kernel_function(description="Trim whitespace from the start and end of a string.")
    def trim(self, text: str) -> str:
        """
        Trim whitespace from the start and end of a string.

        Example:
            KernelContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return text.strip()

    @kernel_function(description="Trim whitespace from the start of a string.")
    def trim_start(self, text: str) -> str:
        """
        Trim whitespace from the start of a string.

         Example:
             KernelContext["input"] = "  hello world  "
             {{text.trim $input}} => "hello world  "
        """
        return text.lstrip()

    @kernel_function(description="Trim whitespace from the end of a string.")
    def trim_end(self, text: str) -> str:
        """
        Trim whitespace from the end of a string.

         Example:
             KernelContext["input"] = "  hello world  "
             {{text.trim $input}} => "  hello world"
        """
        return text.rstrip()

    @kernel_function(description="Convert a string to uppercase.")
    def uppercase(self, text: str) -> str:
        """
        Convert a string to uppercase.

        Example:
            KernelContext["input"] = "hello world"
             {{text.uppercase $input}} => "HELLO WORLD"
        """
        return text.upper()

    @kernel_function(description="Convert a string to lowercase.")
    def lowercase(self, text: str) -> str:
        """
        Convert a string to lowercase.

         Example:
             KernelContext["input"] = "HELLO WORLD"
             {{text.lowercase $input}} => "hello world"
        """
        return text.lower()
