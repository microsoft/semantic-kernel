# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, create_autospec

import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel


@pytest.fixture
def kernel_with_ai_service():
    kernel = create_autospec(Kernel)
    mock_ai_service_client = create_autospec(ChatCompletionClientBase)
    mock_prompt_execution_settings = create_autospec(PromptExecutionSettings)
    mock_prompt_execution_settings.function_choice_behavior = None
    kernel.select_ai_service.return_value = (mock_ai_service_client, mock_prompt_execution_settings)
    mock_ai_service_client.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )

    return kernel, mock_ai_service_client
