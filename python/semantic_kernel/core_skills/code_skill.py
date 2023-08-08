# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Union

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

CODE_BLOCK_PATTERN = r"```(?:.*\n)?([\s\S]*?)(?:```*)"


class CodeSkill:
    """
    Description: A skill to generate and execute Python code. Use with caution.

    Usage:
        code_skill = kernel.import_skill(CodeSkill(OpenAIChatCompletion(...)), "CodeSkill")

    Examples:
        code_async = code_skill["codeAsync"]
        execute_async = code_skill["executeAsync"]
        execute_code_async = code_skill["executeCodeAsync"]

        Way 1: access the generated code
        output_code = await code_async.invoke_async("Solve the FizzBuzz problem up to n = 10")
        await execute_code_async.invoke_async(output_code.result)

        Way 2: generate and execute together
        await execute_async.invoke_async("Solve the FizzBuzz problem up to n = 10")

    """

    _service: ChatCompletionClientBase
    _chat_settings: ChatRequestSettings

    def __init__(
        self, service: Union[AzureChatCompletion, OpenAIChatCompletion]
    ) -> None:
        self._service = service
        self._chat_settings = ChatRequestSettings(temperature=0.1)

    @sk_function(
        description="Returns generated Python code from a query", name="codeAsync"
    )
    @sk_function_context_parameter(
        name="query", description="The query to generate code from"
    )
    async def code_async(self, query: str) -> str:
        """
        Returns generated Python code from a query

        :param query: code query
        :return: string result of the query
        """
        prompt = f"Generate plain Python code with no extra explanation nor decoration: {query}"

        result = await self._service.complete_chat_async(
            [("user", prompt)], self._chat_settings
        )

        # Parse if there is Markdown syntax
        code_block = re.findall(pattern=CODE_BLOCK_PATTERN, string=result)
        if code_block and len(code_block[0]):
            return str(code_block[0])
        else:
            return result

    @sk_function(
        description="Executes generated Python code from a query. WARNING: can be unsafe.",
        name="executeAsync",
    )
    @sk_function_context_parameter(
        name="query", description="The query to generate and execute code from"
    )
    async def execute_async(self, query: str) -> str:
        """
        Executes generated Python code from a query

        :param query: code query
        :param global_vars: Dictionary of global variables, can be obtained from globals()
        :param local_vars: Dictionary of local variables, can be obtained from locals()
        :return: None
        """
        code = await self.code_async(query)
        try:
            exec(code)
            return "SUCCESS"
        except Exception:
            raise Exception(f"Error with executing attempted query: '{query}'")

    @sk_function(
        description="Executes given Python code as a string. WARNING: can be unsafe.",
        name="executeCodeAsync",
    )
    @sk_function_context_parameter(
        name="query", description="The query to generate and execute code from"
    )
    async def execute_code_async(self, code: str) -> str:
        """
        Executes generated Python code from a query

        :param query: code query
        :return: None
        """
        try:
            exec(code)
            return "SUCCESS"
        except Exception as e:
            raise Exception(f"Error with executing code: {e}")
