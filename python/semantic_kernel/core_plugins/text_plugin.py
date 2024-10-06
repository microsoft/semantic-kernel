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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        {{text.trimStart $input}} => "hello world  "

        KernelArguments["input"] = "  hello world  "
        {{text.trimEnd $input}} => "  hello world"
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
        {{text.trimStart $input} => "hello world  "

        KernelArguments["input"] = "  hello world  "
        {{text.trimEnd $input} => "  hello world"
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        KernelArguments["input"] = "hello world"
        {{text.uppercase $input}} => "HELLO WORLD"

        KernelArguments["input"] = "HELLO WORLD"
        {{text.lowercase $input}} => "hello world"
    """

    @kernel_function(description="Trim whitespace from the start and end of a string.")
    def trim(self, input: str) -> str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Trim whitespace from the start and end of a string.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Trim whitespace from the start and end of a string.
=======
<<<<<<< main
        """Trim whitespace from the start and end of a string.
=======
        """
        Trim whitespace from the start and end of a string.
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        Example:
            KernelArguments["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return input.strip()

    @kernel_function(description="Trim whitespace from the start of a string.")
    def trim_start(self, input: str) -> str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Trim whitespace from the start of a string.

        Example:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Trim whitespace from the start of a string.

        Example:
=======
<<<<<<< main
        """Trim whitespace from the start of a string.

        Example:
=======
        """
        Trim whitespace from the start of a string.

         Example:
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
             KernelArguments["input"] = "  hello world  "
             {{input.trim $input}} => "hello world  "
        """
        return input.lstrip()

    @kernel_function(description="Trim whitespace from the end of a string.")
    def trim_end(self, input: str) -> str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Trim whitespace from the end of a string.

        Example:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Trim whitespace from the end of a string.

        Example:
=======
<<<<<<< main
        """Trim whitespace from the end of a string.

        Example:
=======
        """
        Trim whitespace from the end of a string.

         Example:
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
             KernelArguments["input"] = "  hello world  "
             {{input.trim $input}} => "  hello world"
        """
        return input.rstrip()

    @kernel_function(description="Convert a string to uppercase.")
    def uppercase(self, input: str) -> str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Convert a string to uppercase.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Convert a string to uppercase.
=======
<<<<<<< main
        """Convert a string to uppercase.
=======
        """
        Convert a string to uppercase.
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        Example:
            KernelArguments["input"] = "hello world"
             {{input.uppercase $input}} => "HELLO WORLD"
        """
        return input.upper()

    @kernel_function(description="Convert a string to lowercase.")
    def lowercase(self, input: str) -> str:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Convert a string to lowercase.

        Example:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Convert a string to lowercase.

        Example:
=======
<<<<<<< main
        """Convert a string to lowercase.

        Example:
=======
        """
        Convert a string to lowercase.

         Example:
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
             KernelArguments["input"] = "HELLO WORLD"
             {{input.lowercase $input}} => "hello world"
        """
        return input.lower()
