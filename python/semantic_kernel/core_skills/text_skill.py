
from semantic_kernel.skill_definition import sk_function


class TextSkill:

    @sk_function("Trim whitespace from the start and end of a string.")
    def trim(self, text: str) -> str:
        """
        Trim whitespace from the start and end of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world"
        """
        return text.strip()

    @sk_function("Trim whitespace from the start of a string.")
    def trim_start(self, text: str) -> str:
        """
       Trim whitespace from the start of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "hello world  "
        """
        return text.lstrip()

    @sk_function("Trim whitespace from the end of a string.")
    def trim_end(self, text: str) -> str:
        """
       Trim whitespace from the end of a string.

        Example:
            SKContext["input"] = "  hello world  "
            {{text.trim $input}} => "  hello world"
        """
        return text.rstrip()
