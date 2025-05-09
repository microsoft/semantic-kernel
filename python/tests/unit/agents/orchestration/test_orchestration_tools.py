# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Callable
from typing import Any, Literal
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from semantic_kernel.agents.orchestration.tools import structure_output_transform
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class MockPromptExecutionSettings(PromptExecutionSettings):
    """A mock prompt execution settings class for testing purposes."""

    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None


class MockChatCompletionService(ChatCompletionClientBase):
    """A mock chat completion service for testing purposes."""

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return MockPromptExecutionSettings


class MockModel(KernelBaseModel):
    name: str
    age: int


def test_structure_output_transform():
    """Test the structure_output_transform function."""

    service = MockChatCompletionService(ai_model_id="test_model")
    prompt_execution_settings = PromptExecutionSettings()

    transform = structure_output_transform(
        target_structure=MockModel,
        service=service,
        prompt_execution_settings=prompt_execution_settings,
    )

    assert isinstance(transform, Callable)


def test_structure_output_transform_original_settings_not_changed():
    """Test the structure_output_transform function with original settings not changed."""

    service = MockChatCompletionService(ai_model_id="test_model")
    prompt_execution_settings = PromptExecutionSettings(
        extension_data={"test_key": "test_value"},
    )

    _ = structure_output_transform(
        target_structure=MockModel,
        service=service,
        prompt_execution_settings=prompt_execution_settings,
    )

    assert not hasattr(prompt_execution_settings, "response_format")
    assert prompt_execution_settings.extension_data["test_key"] == "test_value"


def test_structure_output_transform_unsupported_service():
    """Test the structure_output_transform function with unsupported service."""

    with (
        patch.object(
            MockChatCompletionService, "get_prompt_execution_settings_class"
        ) as mock_get_prompt_execution_settings_class,
        pytest.raises(ValueError),
    ):
        mock_get_prompt_execution_settings_class.return_value = PromptExecutionSettings

        service = MockChatCompletionService(ai_model_id="test_model")
        prompt_execution_settings = PromptExecutionSettings()

        _ = structure_output_transform(MockModel, service, prompt_execution_settings)


async def test_structure_output_transform_invoke():
    """Test the structure_output_transform function and invoke the transform."""
    mock_model = MockModel(name="John Doe", age=30)

    with (
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(
            role="assistant", content=mock_model.model_dump_json()
        )

        service = MockChatCompletionService(ai_model_id="test_model")
        prompt_execution_settings = PromptExecutionSettings()

        transform = structure_output_transform(
            target_structure=MockModel,
            service=service,
            prompt_execution_settings=prompt_execution_settings,
        )

        result = await transform(ChatMessageContent(role="user", content="name is John Doe and age is 30"))

        assert isinstance(result, MockModel)
        assert result == mock_model

        mock_get_chat_message_content.assert_called_once()
        assert len(mock_get_chat_message_content.call_args[0][0].messages) == 2


async def test_structure_output_transform_invoke_with_messages():
    """Test the structure_output_transform function and invoke the transform with messages."""
    mock_model = MockModel(name="John Doe", age=30)

    with (
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(
            role="assistant", content=mock_model.model_dump_json()
        )

        service = MockChatCompletionService(ai_model_id="test_model")
        prompt_execution_settings = PromptExecutionSettings()

        transform = structure_output_transform(
            target_structure=MockModel,
            service=service,
            prompt_execution_settings=prompt_execution_settings,
        )

        result = await transform([
            ChatMessageContent(role="user", content="name is John Doe"),
            ChatMessageContent(role="user", content="age is 30"),
        ])

        assert isinstance(result, MockModel)
        assert result == mock_model

        mock_get_chat_message_content.assert_called_once()
        assert len(mock_get_chat_message_content.call_args[0][0].messages) == 3


async def test_structure_output_transform_invoke_unsupported_type():
    """Test the structure_output_transform function and invoke the transform with messages of unsupported type."""

    service = MockChatCompletionService(ai_model_id="test_model")
    prompt_execution_settings = PromptExecutionSettings()

    transform = structure_output_transform(
        target_structure=MockModel,
        service=service,
        prompt_execution_settings=prompt_execution_settings,
    )

    with pytest.raises(ValueError):
        _ = await transform("unsupported type")
