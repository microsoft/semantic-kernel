# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.models.ai.chat_completion.chat_message import ChatMessage
from semantic_kernel.prompt_template.prompt_template import PromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import (
    PromptTemplateConfig,
)


def test_chat_message():
    # Test initialization with default values
    message = ChatMessage()
    assert message.role == "assistant"
    assert message.fixed_content is None
    assert message.content is None
    assert message.content_template is None
