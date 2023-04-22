from semantic_kernel.skill_definition import sk_function


class TestNativeEchoBotSkill:
    """
    Description: Test Native Skill for testing purposes
    """

    @sk_function(
        description="Echo for input text",
        name="echoAsync",
        input_description="The text to echo",
    )
    async def echo(self, text: str) -> str:
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
