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
    Description: A skill that provides generated code

    Usage:
        todo

    Examples:
        todo
    """

    _service: ChatCompletionClientBase
    _chat_settings: ChatRequestSettings

    def __init__(
        self, service: Union[AzureChatCompletion, OpenAIChatCompletion]
    ) -> None:
        self._service = service
        self._chat_settings = ChatRequestSettings(temperature=0.0)

    @sk_function(
        description="Returns generated Python code from a query", name="codeAsync"
    )
    @sk_function_context_parameter(
        name="query",
        description="The query to generate code from",
        default_value="None",
    )
    async def code_async(self, query: str) -> str:
        """
        Returns generated Python code from a query

        :param query: code query
        :param context: contains context
        :return: string result of the query
        """
        prompt = f"Generate plain Python code with no extra explanation nor decoration: {query}"

        result = await self._service.complete_chat_async(
            [("user", prompt)], self._chat_settings
        )

        # Parse if there is Markdown syntax
        code_block = re.findall(pattern=CODE_BLOCK_PATTERN, string=result)
        if code_block and len(code_block[0]):
            return code_block[0]
        else:
            return result
