# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from dataclasses import dataclass
from unittest.mock import ANY, patch

import pytest

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationBase, TIn, TOut
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel_pydantic import KernelBaseModel
from tests.unit.agents.orchestration.conftest import MockRuntime

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        pass


class MockOrchestration(OrchestrationBase[TIn, TOut]):
    """A mock orchestration base for testing purposes."""

    async def _start(self, task, runtime, internal_topic_type, collection_agent_type):
        pass

    async def _prepare(self, runtime, internal_topic_type, result_callback):
        pass


def test_orchestration_init():
    """Test the initialization of the MockOrchestration."""
    agent_a = MockAgent()
    agent_b = MockAgent()
    agent_c = MockAgent()

    orchestration = MockOrchestration(
        members=[agent_a, agent_b, agent_c],
        name="test_orchestration",
        description="Test Orchestration",
    )

    assert orchestration.name == "test_orchestration"
    assert orchestration.description == "Test Orchestration"

    assert len(orchestration._members) == 3
    assert orchestration._input_transform is not None
    assert orchestration._output_transform is not None
    assert orchestration._agent_response_callback is None


def test_orchestration_init_with_default_values():
    """Test the initialization of the MockOrchestration with default values."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration = MockOrchestration(members=[agent_a, agent_b])

    assert orchestration.name
    assert orchestration.description

    assert len(orchestration._members) == 2
    assert orchestration._input_transform is not None
    assert orchestration._output_transform is not None
    assert orchestration._agent_response_callback is None


def test_orchestration_init_with_no_members():
    """Test the initialization of the OrchestrationBase with no members."""
    with pytest.raises(ValueError):
        _ = MockOrchestration(members=[])


def test_orchestration_set_types():
    """Test the set_types method of OrchestrationBase."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    # Test with default types
    orchestration_a = MockOrchestration(members=[agent_a, agent_b])
    orchestration_a._set_types()

    assert orchestration_a.t_in is DefaultTypeAlias
    assert orchestration_a.t_out is DefaultTypeAlias

    # Test with a custom input type and default output type
    orchestration_c = MockOrchestration[int](members=[agent_a, agent_b])
    orchestration_c._set_types()

    assert orchestration_c.t_in is int
    assert orchestration_c.t_out is DefaultTypeAlias

    # Test with a custom input type and custom output type
    orchestration_b = MockOrchestration[str, int](members=[agent_a, agent_b])
    orchestration_b._set_types()

    assert orchestration_b.t_in is str
    assert orchestration_b.t_out is int

    # Test with an incorrect number of types
    with pytest.raises(TypeError):
        orchestration_d = MockOrchestration[str, str, str](members=[agent_a, agent_b])
        orchestration_d._set_types()


async def test_orchestration_invoke_with_str():
    """Test the invoke method of OrchestrationBase with a string input."""
    orchestration = MockOrchestration(members=[MockAgent(), MockAgent()])

    with patch.object(orchestration, "_start") as mock_start:
        await orchestration.invoke("Test message", MockRuntime())
        mock_start.assert_called_once_with(
            ChatMessageContent(role=AuthorRole.USER, content="Test message"), ANY, ANY, ANY
        )


async def test_orchestration_invoke_with_chat_message_content():
    """Test the invoke method of OrchestrationBase with a ChatMessageContent input."""
    orchestration = MockOrchestration(members=[MockAgent(), MockAgent()])

    chat_message_content = ChatMessageContent(role=AuthorRole.USER, content="Test message")
    with patch.object(orchestration, "_start") as mock_start:
        await orchestration.invoke(chat_message_content, MockRuntime())
        mock_start.assert_called_once_with(chat_message_content, ANY, ANY, ANY)

    chat_message_content_list = [
        ChatMessageContent(role=AuthorRole.USER, content="Test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="Test message 2"),
    ]
    with patch.object(orchestration, "_start") as mock_start:
        await orchestration.invoke(chat_message_content_list, MockRuntime())
        mock_start.assert_called_once_with(chat_message_content_list, ANY, ANY, ANY)


async def test_orchestration_invoke_with_custom_type():
    """Test the invoke method of OrchestrationBase with a custom type."""

    @dataclass
    class CustomType:
        value: str
        number: int

    orchestration = MockOrchestration[CustomType, TOut](members=[MockAgent(), MockAgent()])

    custom_type_instance = CustomType(value="Test message", number=42)
    with patch.object(orchestration, "_start") as mock_start:
        await orchestration.invoke(custom_type_instance, MockRuntime())
        mock_start.assert_called_once_with(
            ChatMessageContent(role=AuthorRole.USER, content=json.dumps(custom_type_instance.__dict__)), ANY, ANY, ANY
        )


async def test_orchestration_invoke_with_custom_type_async_input_transform():
    """Test the invoke method of OrchestrationBase with a custom type and async input transform."""

    @dataclass
    class CustomType:
        value: str
        number: int

    async def async_input_transform(input_data: CustomType) -> ChatMessageContent:
        await asyncio.sleep(0.1)  # Simulate async processing
        return ChatMessageContent(role=AuthorRole.USER, content="Test message")

    orchestration = MockOrchestration[CustomType, TOut](
        members=[MockAgent(), MockAgent()],
        input_transform=async_input_transform,
    )

    custom_type_instance = CustomType(value="Test message", number=42)
    with patch.object(orchestration, "_start") as mock_start:
        await orchestration.invoke(custom_type_instance, MockRuntime())
        mock_start.assert_called_once_with(
            ChatMessageContent(role=AuthorRole.USER, content="Test message"), ANY, ANY, ANY
        )


def test_default_input_transform_default_type_alias():
    """Test the default_input_transform method of OrchestrationBase."""
    orchestration = MockOrchestration(members=[MockAgent(), MockAgent()])
    orchestration._set_types()

    chat_message_content = ChatMessageContent(role=AuthorRole.USER, content="Test message")
    transformed_input = orchestration._default_input_transform(chat_message_content)

    assert isinstance(transformed_input, ChatMessageContent)

    chat_message_content_list = [
        ChatMessageContent(role=AuthorRole.USER, content="Test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="Test message 2"),
    ]
    transformed_input_list = orchestration._default_input_transform(chat_message_content_list)

    assert isinstance(transformed_input_list, list) and all(
        isinstance(item, ChatMessageContent) for item in transformed_input_list
    )


def test_default_input_transform_custom_type():
    """Test the default_input_transform method of OrchestrationBase with a custom type."""

    @dataclass
    class CustomType:
        value: str
        number: int

    orchestration_a = MockOrchestration[CustomType, TOut](members=[MockAgent(), MockAgent()])
    orchestration_a._set_types()

    custom_type_instance = CustomType(value="Test message", number=42)
    transformed_input_a = orchestration_a._default_input_transform(custom_type_instance)

    assert isinstance(transformed_input_a, ChatMessageContent)
    assert CustomType(**json.loads(transformed_input_a.content)) == custom_type_instance
    assert transformed_input_a.role == AuthorRole.USER

    class CustomModel(KernelBaseModel):
        value: str
        number: int

    orchestration_b = MockOrchestration[CustomModel, TOut](members=[MockAgent(), MockAgent()])
    orchestration_b._set_types()

    custom_model_instance = CustomModel(value="Test message", number=42)
    transformed_input_b = orchestration_b._default_input_transform(custom_model_instance)

    assert isinstance(transformed_input_b, ChatMessageContent)
    assert CustomModel.model_validate_json(transformed_input_b.content) == custom_model_instance
    assert transformed_input_b.role == AuthorRole.USER


def test_default_input_transform_custom_type_error():
    """Test the default_input_transform method of OrchestrationBase with an incorrect type."""

    @dataclass
    class CustomType:
        value: str
        number: int

    class CustomModel(KernelBaseModel):
        value: str
        number: int

    orchestration = MockOrchestration[CustomModel, TOut](members=[MockAgent(), MockAgent()])
    orchestration._set_types()

    with pytest.raises(TypeError):
        custom_type_instance = CustomType(value="Test message", number=42)
        orchestration._default_input_transform(custom_type_instance)


def test_default_output_transform_default_type_alias():
    """Test the default_output_transform method of OrchestrationBase."""
    orchestration = MockOrchestration(members=[MockAgent(), MockAgent()])
    orchestration._set_types()

    chat_message_content = ChatMessageContent(role=AuthorRole.USER, content="Test message")
    transformed_output = orchestration._default_output_transform(chat_message_content)

    assert isinstance(transformed_output, ChatMessageContent)

    chat_message_content_list = [
        ChatMessageContent(role=AuthorRole.USER, content="Test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="Test message 2"),
    ]
    transformed_output_list = orchestration._default_output_transform(chat_message_content_list)

    assert isinstance(transformed_output_list, list) and all(
        isinstance(item, ChatMessageContent) for item in transformed_output_list
    )

    with pytest.raises(TypeError, match="Invalid output message type"):
        orchestration._default_output_transform("Invalid type")


def test_default_output_transform_custom_type():
    """Test the default_output_transform method of OrchestrationBase with a custom type."""

    @dataclass
    class CustomType:
        value: str
        number: int

    orchestration_a = MockOrchestration[TIn, CustomType](members=[MockAgent(), MockAgent()])
    orchestration_a._set_types()

    custom_type_instance = CustomType(value="Test message", number=42)
    chat_message_content = ChatMessageContent(role=AuthorRole.USER, content=json.dumps(custom_type_instance.__dict__))

    transformed_output_a = orchestration_a._default_output_transform(chat_message_content)

    assert isinstance(transformed_output_a, CustomType)
    assert transformed_output_a == custom_type_instance

    class CustomModel(KernelBaseModel):
        value: str
        number: int

    orchestration_b = MockOrchestration[TIn, CustomModel](members=[MockAgent(), MockAgent()])
    orchestration_b._set_types()

    custom_model_instance = CustomModel(value="Test message", number=42)
    chat_message_content = ChatMessageContent(role=AuthorRole.USER, content=custom_model_instance.model_dump_json())

    transformed_output_b = orchestration_b._default_output_transform(chat_message_content)

    assert isinstance(transformed_output_b, CustomModel)
    assert transformed_output_b == custom_model_instance


def test_default_output_transform_custom_type_error():
    """Test the default_output_transform method of OrchestrationBase with an incorrect type."""

    @dataclass
    class CustomType:
        value: str
        number: int

    class CustomModel(KernelBaseModel):
        value: str
        number: int

    orchestration = MockOrchestration[TIn, CustomModel](members=[MockAgent(), MockAgent()])
    orchestration._set_types()

    with pytest.raises(TypeError, match="Unable to transform output message"):
        custom_type_instance = CustomType(value="Test message", number=42)
        orchestration._default_output_transform(custom_type_instance)


async def test_invoke_with_timeout_error():
    """Test the invoke method of the MockOrchestration with a timeout error."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration = MockOrchestration(members=[agent_a, agent_b])
    # The orchestration_result will never be set by the MockOrchestration
    orchestration_result = await orchestration.invoke(
        task="test_message",
        runtime=MockRuntime(),
    )

    with pytest.raises(asyncio.TimeoutError):
        await orchestration_result.get(timeout=0.1)


async def test_invoke_cancel_before_completion():
    """Test the invoke method of the MockOrchestration with cancellation before completion."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration = MockOrchestration(members=[agent_a, agent_b])
    # The orchestration_result will never be set by the MockOrchestration
    orchestration_result = await orchestration.invoke(
        task="test_message",
        runtime=MockRuntime(),
    )

    # Cancel the orchestration before completion
    orchestration_result.cancel()

    with pytest.raises(RuntimeError, match="The invocation was canceled before it could complete."):
        await orchestration_result.get()


async def test_invoke_with_double_cancel():
    """Test the invoke method of the MockOrchestration with double cancel."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration = MockOrchestration(members=[agent_a, agent_b])
    # The orchestration_result will never be set by the MockOrchestration
    orchestration_result = await orchestration.invoke(
        task="test_message",
        runtime=MockRuntime(),
    )

    orchestration_result.cancel()
    # Cancelling again should raise an error
    with pytest.raises(RuntimeError, match="The invocation has already been canceled."):
        orchestration_result.cancel()
