# Copyright (c) Microsoft. All rights reserved.

import re
from typing import Any, Dict, Union

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
DEFAULT_PROMPT = "Generate plain Python code with no extra explanation nor decoration: "


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

        full_prompt = f"{DEFAULT_PROMPT}{query}"
        return await self.custom_code_async(full_prompt)

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
        return await self.custom_execute_async(code)

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

        :param code: Python code to execute
        :return: None
        """

        return await self.custom_execute_async(code)

    async def custom_code_async(self, prompt: str) -> str:
        """
        Returns generated Python code from a prompt

        :param prompt: Prompt to request
        :return: string result of the query
        """

        result = await self._service.complete_chat_async(
            [("user", prompt)], self._chat_settings
        )

        # Parse if there is Markdown syntax
        code_block = re.findall(pattern=CODE_BLOCK_PATTERN, string=result)
        if code_block and len(code_block[0]):
            return str(code_block[0]).lstrip("python\n")
        else:
            return result

    async def custom_execute_async(
        self,
        code: str,
        global_vars: Dict[str, Any] = None,
        local_vars: Dict[str, Any] = None,
    ) -> str:
        """
        Executes code using scoped variables

        :param code: Python code to execute
        :param global_vars: Dictionary of global variable names and values
        :param local_vars: Dictionary of local variable names and values
        :return: None
        """

        try:
            exec(code, global_vars, local_vars)
            return "SUCCESS"
        except Exception as e:
            raise Exception(f"Error with attempting code execution: '{e}'")
