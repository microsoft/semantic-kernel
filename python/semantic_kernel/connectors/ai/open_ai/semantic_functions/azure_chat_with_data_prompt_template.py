# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.semantic_functions.chat_with_data_prompt_template import (
    ChatWithDataPromptTemplate,
)


class AzureChatWithDataPromptTemplate(
    OpenAIChatPromptTemplate, ChatWithDataPromptTemplate
):
    def add_tool_message(self, message: str) -> None:
        """Add a tool message to the chat template."""
        super().add_message("tool", message)
