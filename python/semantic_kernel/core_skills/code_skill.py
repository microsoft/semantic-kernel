# Copyright (c) Microsoft. All rights reserved.

import openai

from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class CodeSkill:
    """
    Description: A skill that provides generated code

    Usage:
        todo

    Examples:
        todo
    """


    @sk_function(
        description="Returns generated Python code from a query", name="codeAsync"
    )
    @sk_function_context_parameter(
        name="query",
        description="The query to generate code from",
        default_value="None",
    )
    async def code_async(self, query: str) -> str:
        pass