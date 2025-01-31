# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.agents.bedrock.bedrock_agent_settings import BedrockAgentSettings
from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.fixture
def bedrock_agent_settings():
    return BedrockAgentSettings(
        agent_resource_role_arn="test_arn",
        foundation_model="test_foundation_model",
    )


@pytest.fixture
def bedrock_agent_model():
    return BedrockAgentModel(
        agent_id="test_agent_id",
        agent_name="test_agent_name",
        foundation_model="test_foundation_model",
    )


@pytest.fixture
def bedrock_agent(bedrock_agent_settings, bedrock_agent_model):
    return BedrockAgent(
        name="test_agent",
        agent_resource_role_arn=bedrock_agent_settings.agent_resource_role_arn,
        foundation_model=bedrock_agent_settings.foundation_model,
        kernel=MagicMock(spec=Kernel),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        arguments=KernelArguments(),
        instructions="test_instructions",
        prompt_template_config=PromptTemplateConfig(template="test_template"),
    )


# Test case to verify the initialization of BedrockAgent
async def test_bedrock_agent_initialization(bedrock_agent_settings, bedrock_agent_model):
    with patch.object(BedrockAgentSettings, "create", return_value=bedrock_agent_settings):
        agent = BedrockAgent(
            name="test_agent",
            agent_resource_role_arn=bedrock_agent_settings.agent_resource_role_arn,
            foundation_model=bedrock_agent_settings.foundation_model,
            kernel=MagicMock(spec=Kernel),
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
            arguments=KernelArguments(),
            instructions="test_instructions",
            prompt_template_config=PromptTemplateConfig(template="test_template"),
        )
        assert agent.name == "test_agent"
        assert agent.agent_model.agent_name == "test_agent"
        assert agent.agent_model.foundation_model == "test_foundation_model"


# Test case to verify error handling during BedrockAgent initialization
async def test_bedrock_agent_initialization_error():
    with patch.object(BedrockAgentSettings, "create", side_effect=ValidationError([])):
        with pytest.raises(AgentInitializationException):
            BedrockAgent(
                name="test_agent",
                agent_resource_role_arn="test_arn",
                foundation_model="test_foundation_model",
                kernel=MagicMock(spec=Kernel),
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
                arguments=KernelArguments(),
                instructions="test_instructions",
                prompt_template_config=PromptTemplateConfig(template="test_template"),
            )


# Test case to verify the creation of BedrockAgent
async def test_bedrock_agent_create(bedrock_agent):
    with patch.object(bedrock_agent, "_create_agent", new_callable=AsyncMock) as mock_create_agent:
        await bedrock_agent.create_agent()
        mock_create_agent.assert_called_once()


# Test case to verify error handling during BedrockAgent creation
async def test_bedrock_agent_create_error(bedrock_agent):
    with patch.object(bedrock_agent, "_create_agent", new_callable=AsyncMock) as mock_create_agent:
        mock_create_agent.side_effect = AgentInitializationException("Error creating agent")
        with pytest.raises(AgentInitializationException):
            await bedrock_agent.create_agent()


# Test case to verify the invocation of BedrockAgent
async def test_bedrock_agent_invoke(bedrock_agent):
    with patch.object(bedrock_agent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        mock_invoke_agent.return_value = {"completion": [{"chunk": {"bytes": b"test_response"}}]}
        async for message in bedrock_agent.invoke("test_session_id", "test_input_text"):
            assert message.content == "test_response"


# Test case to verify error handling during BedrockAgent invocation
async def test_bedrock_agent_invoke_error(bedrock_agent):
    with patch.object(bedrock_agent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        mock_invoke_agent.side_effect = AgentInvokeException("Error invoking agent")
        with pytest.raises(AgentInvokeException):
            async for _ in bedrock_agent.invoke("test_session_id", "test_input_text"):
                pass


# Test case to verify the streaming invocation of BedrockAgent
async def test_bedrock_agent_invoke_stream(bedrock_agent):
    with patch.object(bedrock_agent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        mock_invoke_agent.return_value = {"completion": [{"chunk": {"bytes": b"test_response"}}]}
        async for message in bedrock_agent.invoke_stream("test_session_id", "test_input_text"):
            assert message.content == "test_response"


# Test case to verify error handling during BedrockAgent streaming invocation
async def test_bedrock_agent_invoke_stream_error(bedrock_agent):
    with patch.object(bedrock_agent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        mock_invoke_agent.side_effect = AgentInvokeException("Error invoking agent")
        with pytest.raises(AgentInvokeException):
            async for _ in bedrock_agent.invoke_stream("test_session_id", "test_input_text"):
                pass


# Test case to verify handling of chunk event in BedrockAgent
async def test_bedrock_agent_handle_chunk_event(bedrock_agent):
    event = {BedrockAgentEventType.CHUNK: {"bytes": b"test_response"}}
    message = bedrock_agent._handle_chunk_event(event)
    assert message.content == "test_response"


# Test case to verify handling of return control event in BedrockAgent
async def test_bedrock_agent_handle_return_control_event(bedrock_agent):
    event = {BedrockAgentEventType.RETURN_CONTROL: {"functionCalls": [{"id": "test_id"}]}}
    with patch.object(bedrock_agent, "_handle_return_control_event", new_callable=AsyncMock) as mock_handle_event:
        mock_handle_event.return_value = {"invocationId": "test_id"}
        result = await bedrock_agent._handle_return_control_event(event, MagicMock(spec=Kernel), KernelArguments())
        assert result["invocationId"] == "test_id"


# Test case to verify handling of files event in BedrockAgent
async def test_bedrock_agent_handle_files_event(bedrock_agent):
    event = {BedrockAgentEventType.FILES: {"files": [{"bytes": b"test_file", "type": "text/plain", "name": "test.txt"}]}}
    files = bedrock_agent._handle_files_event(event)
    assert len(files) == 1
    assert files[0].data == b"test_file"
    assert files[0].mime_type == "text/plain"
    assert files[0].metadata["name"] == "test.txt"


# Test case to verify handling of trace event in BedrockAgent
async def test_bedrock_agent_handle_trace_event(bedrock_agent):
    event = {BedrockAgentEventType.TRACE: {"trace": "test_trace"}}
    trace = bedrock_agent._handle_trace_event(event)
    assert trace["trace"] == "test_trace"


# Test case to verify handling of streaming chunk event in BedrockAgent
async def test_bedrock_agent_handle_streaming_chunk_event(bedrock_agent):
    event = {BedrockAgentEventType.CHUNK: {"bytes": b"test_response"}}
    message = bedrock_agent._handle_streaming_chunk_event(event)
    assert message.content == "test_response"


# Test case to verify handling of streaming return control event in BedrockAgent
async def test_bedrock_agent_handle_streaming_return_control_event(bedrock_agent):
    event = {BedrockAgentEventType.RETURN_CONTROL: {"functionCalls": [{"id": "test_id"}]}}
    message = bedrock_agent._handle_streaming_return_control_event(event)
    assert len(message.items) == 1
    assert isinstance(message.items[0], FunctionCallContent)
    assert message.items[0].id == "test_id"


# Test case to verify handling of streaming files event in BedrockAgent
async def test_bedrock_agent_handle_streaming_files_event(bedrock_agent):
    event = {BedrockAgentEventType.FILES: {"files": [{"bytes": b"test_file", "type": "text/plain", "name": "test.txt"}]}}
    message = bedrock_agent._handle_streaming_files_event(event)
    assert len(message.items) == 1
    assert message.items[0].data == b"test_file"
    assert message.items[0].mime_type == "text/plain"
    assert message.items[0].metadata["name"] == "test.txt"


# Test case to verify handling of streaming trace event in BedrockAgent
async def test_bedrock_agent_handle_streaming_trace_event(bedrock_agent):
    event = {BedrockAgentEventType.TRACE: {"trace": "test_trace"}}
    message = bedrock_agent._handle_streaming_trace_event(event)
    assert message.metadata["trace"] == "test_trace"
