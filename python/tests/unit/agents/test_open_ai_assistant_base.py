# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.beta.threads.runs.runs import Run
from openai.types.beta.assistant import Assistant, ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from openai.types.beta.assistant_response_format import AssistantResponseFormat
from openai.types.beta.assistant_tool import CodeInterpreterTool, FileSearchTool
from openai.types.beta.threads.annotation import FileCitationAnnotation, FilePathAnnotation
from openai.types.beta.threads.file_citation_annotation import FileCitation
from openai.types.beta.threads.file_path_annotation import FilePath
from openai.types.beta.threads.required_action_function_tool_call import Function
from openai.types.beta.threads.required_action_function_tool_call import Function as RequiredActionFunction
from openai.types.beta.threads.run import (
    RequiredAction,
    RequiredActionFunctionToolCall,
    RequiredActionSubmitToolOutputs,
)
from openai.types.beta.threads.runs import RunStep
from openai.types.beta.threads.runs.code_interpreter_tool_call import (
    CodeInterpreter,
    CodeInterpreterToolCall,
)
from openai.types.beta.threads.runs.function_tool_call import Function as RunsFunction
from openai.types.beta.threads.runs.function_tool_call import FunctionToolCall
from openai.types.beta.threads.runs.message_creation_step_details import MessageCreation, MessageCreationStepDetails
from openai.types.beta.threads.runs.tool_calls_step_details import ToolCallsStepDetails

from semantic_kernel.agents.open_ai.azure_open_ai_assistant_agent import AzureOpenAIAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.open_ai.open_ai_service_configuration import AzureOpenAIServiceConfiguration
from semantic_kernel.agents.open_ai.open_ai_thread_creation_options import OpenAIThreadCreationOptions
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentExecutionError,
    AgentFileNotFoundException,
    AgentInitializationError,
    AgentInvokeError,
)

# region Test Fixtures


@pytest.fixture
def configuration():
    return AzureOpenAIServiceConfiguration(
        ai_model_id="test_model",
        service_id="test_service",
        api_key="test_api_key",
        endpoint="https://test.endpoint",
        api_version="v1",
        default_headers={"User-Agent": "test-agent"},
    )


@pytest.fixture
def definition():
    return OpenAIAssistantDefinition(
        ai_model_id="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        enable_code_interpreter=True,
        enable_file_search=True,
        enable_json_response=True,
        file_ids=["file1", "file2"],
        temperature=0.7,
        top_p=0.9,
        vector_store_ids=["vector_store1"],
        metadata={"key": "value"},
        execution_settings=None,
    )


@pytest.fixture
def mock_assistant():
    return Assistant(
        created_at=123456789,
        object="assistant",
        metadata={
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        model="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        temperature=0.7,
        top_p=0.9,
        response_format={"type": "json_object"},
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
    )


@pytest.fixture
def mock_thread_creation_settings():
    return OpenAIThreadCreationOptions(
        code_interpreter_file_ids=["file1", "file2"],
        vector_store_id="vector_store1",
        messages=[ChatMessageContent(role=AuthorRole.USER, content="test message")],
        metadata={"key": "value"},
    )


@pytest.fixture
def mock_thread_creation_settings_invalid_role():
    return OpenAIThreadCreationOptions(
        code_interpreter_file_ids=["file1", "file2"],
        vector_store_id="vector_store1",
        messages=[ChatMessageContent(role=AuthorRole.TOOL, content="test message")],
        metadata={"key": "value"},
    )


@pytest.fixture
def mock_thread():
    class MockThread:
        id = "test_thread_id"

    return MockThread()


@pytest.fixture
def mock_chat_message_content():
    return ChatMessageContent(role=AuthorRole.USER, content="test message", metadata={"key": "value"})


@pytest.fixture
def mock_message():
    class MockMessage:
        id = "test_message_id"

    return MockMessage()


@pytest.fixture
def mock_thread_messages():
    class MockMessage:
        def __init__(self, role, content, assistant_id=None):
            self.role = role
            self.content = content
            self.assistant_id = assistant_id

    class MockTextContent:
        def __init__(self, value, annotations=[]):
            self.type = "text"
            self.text = MagicMock(value=value, annotations=annotations)

    class MockImageContent:
        def __init__(self, url):
            self.type = "image"
            self.image = MagicMock(url=url)

    return [
        MockMessage(
            role="user",
            content=[
                MockTextContent(
                    value="Hello",
                    annotations=[
                        FilePathAnnotation(
                            type="file_path",
                            file_path=FilePath(file_id="test_file_id"),
                            end_index=5,
                            start_index=0,
                            text="Hello",
                        ),
                        FileCitationAnnotation(
                            type="file_citation",
                            file_citation=FileCitation(file_id="test_file_id", quote="test quote"),
                            text="Hello",
                            start_index=0,
                            end_index=5,
                        ),
                    ],
                )
            ],
        ),
        MockMessage(role="assistant", content=[MockImageContent(url="http://image.url")], assistant_id="assistant_1"),
    ]


@pytest.fixture
def mock_run_failed():
    return Run(
        id="run_id",
        status="failed",
        assistant_id="assistant_id",
        created_at=123456789,
        instructions="instructions",
        model="model",
        object="thread.run",
        thread_id="thread_id",
        tools=[],
    )


@pytest.fixture
def mock_run_required_action():
    return Run(
        id="run_id",
        status="requires_action",
        assistant_id="assistant_id",
        created_at=123456789,
        instructions="instructions",
        model="model",
        object="thread.run",
        thread_id="thread_id",
        tools=[],
        required_action=RequiredAction(
            type="submit_tool_outputs",
            submit_tool_outputs=RequiredActionSubmitToolOutputs(
                tool_calls=[
                    RequiredActionFunctionToolCall(
                        id="tool_call_id",
                        type="function",
                        function=RequiredActionFunction(arguments="{}", name="function_name"),
                    )
                ]
            ),
        ),
    )


@pytest.fixture
def mock_run_completed():
    return Run(
        id="run_id",
        status="completed",
        assistant_id="assistant_id",
        created_at=123456789,
        instructions="instructions",
        model="model",
        object="thread.run",
        thread_id="thread_id",
        tools=[],
        required_action=RequiredAction(
            type="submit_tool_outputs",
            submit_tool_outputs=RequiredActionSubmitToolOutputs(
                tool_calls=[
                    RequiredActionFunctionToolCall(
                        id="tool_call_id", type="function", function=Function(arguments="{}", name="function_name")
                    )
                ]
            ),
        ),
    )


@pytest.fixture
def mock_function_call_content():
    return FunctionCallContent(id="function_call_id", name="function_name", arguments={})


@pytest.fixture
def mock_run_in_progress():
    class MockRun:
        def __init__(self):
            self.id = "run_id"
            self.status = "requires_action"
            self.assistant_id = "assistant_id"
            self.created_at = int(datetime.utcnow().timestamp())
            self.instructions = "instructions"
            self.model = "model"
            self.object = "run"
            self.thread_id = "thread_id"
            self.tools = []
            self.poll_count = 0

        def update_status(self):
            self.poll_count += 1
            if self.poll_count > 2:  # Change the status to completed after 3 polls
                self.status = "completed"

    return MockRun()


@pytest.fixture
def mock_run_step_tool_call():
    class MockToolCall:
        def __init__(self):
            self.type = "code_interpreter"
            self.code_interpreter = MagicMock(input="print('Hello, world!')")

    return RunStep(
        id="step_id_1",
        type="tool_calls",
        completed_at=int(datetime.utcnow().timestamp()),
        created_at=int((datetime.utcnow() - timedelta(minutes=1)).timestamp()),
        step_details=ToolCallsStepDetails(
            tool_calls=[
                CodeInterpreterToolCall(
                    type="code_interpreter", id="test", code_interpreter=CodeInterpreter(input="test code", outputs=[])
                ),
                FunctionToolCall(
                    type="function",
                    id="test",
                    function=RunsFunction(arguments="{}", name="function_name", outpt="test output"),
                ),
            ],
            type="tool_calls",
        ),
        assistant_id="assistant_id",
        object="thread.run.step",
        run_id="run_id",
        status="completed",
        thread_id="thread_id",
    )


@pytest.fixture
def mock_run_step_message_creation():
    class MockMessageCreation:
        def __init__(self):
            self.message_id = "message_id"

    class MockStepDetails:
        def __init__(self):
            self.message_creation = MockMessageCreation()

    return RunStep(
        id="step_id_2",
        type="message_creation",
        completed_at=int(datetime.utcnow().timestamp()),
        created_at=int((datetime.utcnow() - timedelta(minutes=2)).timestamp()),
        step_details=MessageCreationStepDetails(
            type="message_creation", message_creation=MessageCreation(message_id="test")
        ),
        assistant_id="assistant_id",
        object="thread.run.step",
        run_id="run_id",
        status="completed",
        thread_id="thread_id",
    )


# endregion

# region Tests


@pytest.mark.asyncio
async def test_create_assistant(configuration, definition, kernel, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await agent.create_assistant()

        # Assertions to check if the assistant is created correctly
        assert assistant.model == "test_model"
        assert assistant.description == "test_description"
        assert assistant.id == "test_id"
        assert assistant.instructions == "test_instructions"
        assert assistant.name == "test_name"
        assert assistant.tools == [CodeInterpreterTool(type="code_interpreter"), FileSearchTool(type="file_search")]
        assert assistant.temperature == 0.7
        assert assistant.top_p == 0.9
        assert assistant.response_format == AssistantResponseFormat(type="json_object")
        assert assistant.tool_resources == ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        )


@pytest.mark.asyncio
async def test_get_assistant_metadata(configuration, definition, kernel, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await agent.create_assistant()

        metadata = agent.metadata
        assert metadata is not None
        assert assistant.metadata == metadata


@pytest.mark.asyncio
async def test_get_assistant_metadata_malformed_returns_empty_dict(configuration, definition, kernel, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await agent.create_assistant()
        assistant.metadata = "malformed"

        metadata = agent.metadata
        assert metadata == {}


def test_get_assistant_metadata_throws_when_no_assistant(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with pytest.raises(AgentInitializationError, match="The assistant has not been created."):
        _ = agent.metadata


@pytest.mark.asyncio
async def test_get_assistant_tools(configuration, definition, kernel, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await agent.create_assistant()

        tools = agent.tools
        assert tools is not None
        assert assistant.tools == tools


@pytest.mark.asyncio
async def test_get_assistant_tools_throws_when_no_assistant(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
    with pytest.raises(AgentInitializationError, match="The assistant has not been created."):
        _ = agent.tools


@pytest.mark.asyncio
async def test_create_thread(configuration, definition, kernel, mock_thread_creation_settings, mock_thread):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.create = AsyncMock(return_value=mock_thread)

        thread_id = await agent.create_thread(thread_creation_settings=mock_thread_creation_settings)

        # Assertions to check if the thread is created correctly
        assert thread_id == "test_thread_id"
        mock_client.beta.threads.create.assert_called_once()
        _, called_kwargs = mock_client.beta.threads.create.call_args
        assert "tool_resources" in called_kwargs
        assert called_kwargs["tool_resources"] == {
            "code_interpreter": {"file_ids": ["file1", "file2"]},
            "file_search": {"vector_store_ids": ["vector_store1"]},
        }
        assert "messages" in called_kwargs
        assert called_kwargs["messages"] == [{"role": "user", "content": {"type": "text", "text": "test message"}}]
        assert "metadata" in called_kwargs
        assert called_kwargs["metadata"] == {"key": "value"}


@pytest.mark.asyncio
async def test_create_thread_throws_with_invalid_role(
    configuration, definition, kernel, mock_thread_creation_settings_invalid_role, mock_thread
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.create = AsyncMock(return_value=mock_thread)

        with pytest.raises(
            AgentExecutionError,
            match="Invalid message role `tool`",
        ):
            _ = await agent.create_thread(thread_creation_settings=mock_thread_creation_settings_invalid_role)


@pytest.mark.asyncio
async def test_delete_thread(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.delete = AsyncMock()

        await agent.delete_thread("test_thread_id")

        mock_client.beta.threads.delete.assert_called_once_with("test_thread_id")


@pytest.mark.asyncio
async def test_delete(configuration, definition, kernel, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
    agent.assistant = mock_assistant

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.delete = AsyncMock()

        agent._is_deleted = False
        result = await agent.delete()

        assert result == agent._is_deleted
        mock_client.beta.assistants.delete.assert_called_once_with(mock_assistant.id)


@pytest.mark.asyncio
async def test_add_file(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()
        mock_client.files.create = AsyncMock(return_value=MagicMock(id="test_file_id"))

        mock_open_file = mock_open(read_data="file_content")
        with patch("builtins.open", mock_open_file):
            file_id = await agent.add_file("test_file_path", "assistants")

            assert file_id == "test_file_id"
            mock_open_file.assert_called_once_with("test_file_path", "rb")
            mock_client.files.create.assert_called_once()


@pytest.mark.asyncio
async def test_add_file_not_found(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()

        with patch("builtins.open", mock_open(read_data="file_content")) as mock_open_file:
            mock_open_file.side_effect = FileNotFoundError

            with pytest.raises(AgentFileNotFoundException, match="File not found: test_file_path"):
                await agent.add_file("test_file_path", "assistants")


@pytest.mark.asyncio
async def test_add_chat_message(configuration, definition, kernel, mock_chat_message_content, mock_message):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.messages = MagicMock()
        mock_client.beta.threads.messages.create = AsyncMock(return_value=mock_message)

        result = await agent.add_chat_message("test_thread_id", mock_chat_message_content)

        assert result.id == "test_message_id"
        mock_client.beta.threads.messages.create.assert_called_once_with(
            thread_id="test_thread_id",
            role="user",
            content=[{"type": "text", "text": "test message"}],
            metadata={"key": "value"},
        )


@pytest.mark.asyncio
async def test_add_chat_message_invalid_role(configuration, definition, kernel, mock_chat_message_content):
    mock_chat_message_content.role = AuthorRole.TOOL
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with pytest.raises(AgentExecutionError, match="Invalid message role `tool`"):
        await agent.add_chat_message("test_thread_id", mock_chat_message_content)


@pytest.mark.asyncio
async def test_get_thread_messages(configuration, definition, kernel, mock_thread_messages, mock_assistant):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    async def mock_list_messages(*args, **kwargs) -> Any:
        return MagicMock(data=mock_thread_messages)

    async def mock_retrieve_assistant(*args, **kwargs) -> Any:
        return mock_assistant

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.messages = MagicMock()
        mock_client.beta.threads.messages.list = AsyncMock(side_effect=mock_list_messages)
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.retrieve = AsyncMock(side_effect=mock_retrieve_assistant)

        messages = [message async for message in agent.get_thread_messages("test_thread_id")]

        assert len(messages) == 2
        assert len(messages[0]) == 3
        assert isinstance(messages[0][0], ChatMessageContent)
        assert isinstance(messages[0][1], AnnotationContent)
        assert isinstance(messages[0][2], AnnotationContent)
        assert messages[0][0].content == "Hello"

        assert len(messages[1]) == 1
        assert isinstance(messages[1][0], ImageContent)
        assert str(messages[1][0].uri) == "http://image.url/"


@pytest.mark.asyncio
async def test_invoke(
    configuration,
    definition,
    kernel,
    mock_assistant,
    mock_run_in_progress,
    mock_chat_message_content,
    mock_run_step_tool_call,
    mock_run_step_message_creation,
    mock_message,
    mock_function_call_content,
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    async def mock_poll_run_status(run, thread_id):
        run.update_status()
        return run

    def mock_get_function_call_contents(run, function_steps):
        function_steps["test"] = mock_function_call_content
        return [mock_function_call_content]

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)
        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.create = AsyncMock(return_value=mock_run_in_progress)
        mock_client.beta.threads.runs.submit_tool_outputs = AsyncMock()
        mock_client.beta.threads.runs.steps = MagicMock()
        mock_client.beta.threads.runs.steps.list = AsyncMock(
            return_value=MagicMock(data=[mock_run_step_tool_call, mock_run_step_message_creation])
        )

        agent.assistant = await agent.create_assistant()
        agent._get_tools = MagicMock(return_value=["tool"])
        agent._poll_run_status = AsyncMock(side_effect=mock_poll_run_status)
        agent._invoke_function_calls = AsyncMock()
        agent._format_tool_outputs = MagicMock(return_value=[{"tool_call_id": "id", "output": "output"}])
        agent._generate_function_call_content = MagicMock(return_value=mock_chat_message_content)
        agent._generate_message_content = MagicMock(return_value=mock_chat_message_content)
        agent._retrieve_message = AsyncMock(return_value=mock_message)
        agent._get_function_call_contents = MagicMock(side_effect=mock_get_function_call_contents)

        messages = [message async for message in agent.invoke("thread_id")]

        assert len(messages) == 2
        assert messages[0].content == "test message"
        assert messages[1].content == "test code"


@pytest.mark.asyncio
async def test_invoke_assistant_not_initialized_throws(
    configuration,
    definition,
    kernel,
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with pytest.raises(AgentInitializationError, match="The assistant has not been created."):
        _ = [message async for message in agent.invoke("thread_id")]


@pytest.mark.asyncio
async def test_invoke_agent_deleted_throws(
    configuration,
    definition,
    kernel,
    mock_assistant,
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        agent.assistant = await agent.create_assistant()
        agent._is_deleted = True

        with pytest.raises(AgentInitializationError, match="The assistant has been deleted."):
            _ = [message async for message in agent.invoke("thread_id")]


@pytest.mark.asyncio
async def test_invoke_raises_error(
    configuration,
    definition,
    kernel,
    mock_assistant,
    mock_run_in_progress,
    mock_run_step_tool_call,
    mock_run_step_message_creation,
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    async def mock_poll_run_status(run, thread_id):
        run.status = "failed"
        return run

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)
        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.create = AsyncMock(return_value=mock_run_in_progress)
        mock_client.beta.threads.runs.submit_tool_outputs = AsyncMock()
        mock_client.beta.threads.runs.steps = MagicMock()
        mock_client.beta.threads.runs.steps.list = AsyncMock(
            return_value=MagicMock(data=[mock_run_step_tool_call, mock_run_step_message_creation])
        )

        agent.assistant = await agent.create_assistant()
        agent._get_tools = MagicMock(return_value=["tool"])
        agent._poll_run_status = AsyncMock(side_effect=mock_poll_run_status)

        with pytest.raises(
            AgentInvokeError, match="Run failed with status: `failed` for agent `test_name` and thread `thread_id`"
        ):
            _ = [message async for message in agent.invoke("thread_id")]


def test_format_tool_outputs(
    configuration,
    definition,
    kernel,
):
    chat_history = ChatHistory()
    fcc = FunctionCallContent(
        id="test", name="test-function", arguments='{"input": "world"}', metadata={"test": "test"}
    )
    frc = FunctionResultContent.from_function_call_content_and_result(fcc, 123, {"test2": "test2"})
    chat_history.add_message(message=frc.to_chat_message_content())

    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    tool_outputs = agent._format_tool_outputs(chat_history)
    assert tool_outputs[0] == {"tool_call_id": "test", "output": 123}


@pytest.mark.asyncio
async def test_invoke_function_calls(
    configuration,
    definition,
    kernel,
):
    chat_history = ChatHistory()
    fcc = FunctionCallContent(
        id="test", name="test-function", arguments='{"input": "world"}', metadata={"test": "test"}
    )

    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch(
        "semantic_kernel.kernel.Kernel.invoke_function_call", new_callable=AsyncMock
    ) as mock_invoke_function_call:
        mock_invoke_function_call.return_value = "mocked_result"
        results = await agent._invoke_function_calls([fcc], chat_history)
        assert results == ["mocked_result"]
        mock_invoke_function_call.assert_called_once_with(function_call=fcc, chat_history=chat_history)


def test_get_function_call_contents(configuration, definition, kernel, mock_run_required_action):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    result = agent._get_function_call_contents(run=mock_run_required_action, function_steps={})
    assert result is not None


def test_get_function_call_contents_no_action_required(configuration, definition, kernel, mock_run_required_action):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    mock_run_required_action.required_action = None
    result = agent._get_function_call_contents(run=mock_run_required_action, function_steps={})
    assert result == []


def test_get_tools(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
    tools = agent._get_tools()
    assert tools is not None


def test_generate_message_content(configuration, definition, kernel, mock_thread_messages):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    for message in mock_thread_messages:
        result = agent._generate_message_content(assistant_name="test", message=message)
        assert result is not None


def test_check_if_deleted_throws(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
    agent._is_deleted = True
    with pytest.raises(AgentInitializationError, match="The assistant has been deleted."):
        agent._check_if_deleted()


def test_get_message_contents(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    message = ChatMessageContent(role=AuthorRole.USER, content="test message")
    message.items = [
        ImageContent(role=AuthorRole.ASSISTANT, content="test message", uri="http://image.url"),
        TextContent(role=AuthorRole.ASSISTANT, text="test message"),
    ]

    result = agent._get_message_contents(message)
    assert result is not None


@pytest.mark.asyncio
async def test_retrieve_message(configuration, definition, kernel, mock_thread_messages):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        message = await agent._retrieve_message(thread_id="test_thread_id", message_id="test_message_id")
        assert message is not None


@pytest.mark.asyncio
async def test_retrieve_message_fails_polls_again(configuration, definition, kernel):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with (
        patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client,
        patch("semantic_kernel.agents.open_ai.open_ai_assistant_agent.logger", autospec=True),
    ):
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=Exception("Unable to retrieve message"))

        message = await agent._retrieve_message(thread_id="test_thread_id", message_id="test_message_id")
        assert message is None


@pytest.mark.asyncio
async def test_poll_run_status(configuration, definition, kernel, mock_run_required_action, mock_run_completed):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(return_value=mock_run_completed)

        run = await agent._poll_run_status(run=mock_run_required_action, thread_id="test_thread_id")
        assert run.status == "completed"


@pytest.mark.asyncio
async def test_poll_run_status_exception_polls_again(
    configuration, definition, kernel, mock_run_required_action, mock_run_completed
):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(
            side_effect=[Exception("Failed to retrieve message"), mock_run_completed]
        )

        run = await agent._poll_run_status(run=mock_run_required_action, thread_id="test_thread_id")
        assert run.status == "requires_action"


def test_generate_function_result_content(configuration, definition, kernel, mock_function_call_content):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    mock_tool_call = RequiredActionFunctionToolCall(
        id="tool_call_id", type="function", function=Function(arguments="{}", name="function_name", output="result")
    )

    message = agent._generate_function_result_content(
        agent_name="test", function_step=mock_function_call_content, tool_call=mock_tool_call
    )
    assert message is not None
    assert isinstance(message.items[0], FunctionResultContent)


def test_generate_function_call_content(configuration, definition, kernel, mock_function_call_content):
    agent = AzureOpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    message = agent._generate_function_call_content(agent_name="test", fccs=[mock_function_call_content])
    assert message is not None
    assert isinstance(message, ChatMessageContent)
    assert isinstance(message.items[0], FunctionCallContent)


# endregion
