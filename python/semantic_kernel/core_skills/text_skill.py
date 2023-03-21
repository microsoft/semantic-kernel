
from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
    sk_function_input,
    sk_function_name,
)


class TextSkill:

    @sk_function("Trim whitespace from the start and end of a string.")
    def trim(text: str) -> str:
        """
        Trim whitespace from the start and end of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return text.strip()

    @sk_function("Trim whitespace from the start of a string.")
    def trim_start(text: str) -> str:
        """
       Trim whitespace from the start of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world  "
        """
        return text.lstrip()

    @sk_function("Trim whitespace from the end of a string.")
    def trim_end(text: str) -> str:
        """
       Trim whitespace from the end of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "  hello world"
        """
        return text.rstrip()
