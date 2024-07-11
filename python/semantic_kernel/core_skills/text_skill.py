# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function


class TextSkill(PydanticField):
    """
    TextSkill provides a set of functions to manipulate strings.

    Usage:
        kernel.import_skill(TextSkill(), skill_name="text")

    Examples:
        SKContext["input"] = "  hello world  "
        {{text.trim $input}} => "hello world"

        SKContext["input"] = "  hello world  "
        {{text.trimStart $input} => "hello world  "

        SKContext["input"] = "  hello world  "
        {{text.trimEnd $input} => "  hello world"

        SKContext["input"] = "hello world"
        {{text.uppercase $input}} => "HELLO WORLD"

        SKContext["input"] = "HELLO WORLD"
        {{text.lowercase $input}} => "hello world"
    """

    @sk_function(description="Trim whitespace from the start and end of a string.")
    def trim(self, text: str) -> str:
        """
        Trim whitespace from the start and end of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return text.strip()

    @sk_function(description="Trim whitespace from the start of a string.")
    def trim_start(self, text: str) -> str:
        """
        Trim whitespace from the start of a string.

         Example:
             SKContext["input"] = "  hello world  "
             {{text.trim $input}} => "hello world  "
        """
        return text.lstrip()

    @sk_function(description="Trim whitespace from the end of a string.")
    def trim_end(self, text: str) -> str:
        """
        Trim whitespace from the end of a string.

         Example:
             SKContext["input"] = "  hello world  "
             {{text.trim $input}} => "  hello world"
        """
        return text.rstrip()

    @sk_function(description="Convert a string to uppercase.")
    def uppercase(self, text: str) -> str:
        """
        Convert a string to uppercase.

        Example:
            SKContext["input"] = "hello world"
             {{text.uppercase $input}} => "HELLO WORLD"
        """
        return text.upper()

    @sk_function(description="Convert a string to lowercase.")
    def lowercase(self, text: str) -> str:
        """
        Convert a string to lowercase.

         Example:
             SKContext["input"] = "HELLO WORLD"
             {{text.lowercase $input}} => "hello world"
        """
        return text.lower()
