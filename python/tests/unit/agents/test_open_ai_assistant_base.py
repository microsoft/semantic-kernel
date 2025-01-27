# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.lib.streaming._assistants import AsyncAssistantEventHandler, AsyncAssistantStreamManager
from openai.resources.beta.threads.runs.runs import Run
from openai.types.beta.assistant import Assistant, ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from openai.types.beta.assistant_stream_event import (
    MessageDeltaEvent,
    ThreadMessageDelta,
    ThreadRunFailed,
    ThreadRunRequiresAction,
    ThreadRunStepCompleted,
    ThreadRunStepDelta,
)
from openai.types.beta.assistant_tool import CodeInterpreterTool, FileSearchTool
from openai.types.beta.function_tool import FunctionDefinition, FunctionTool
from openai.types.beta.threads import ImageFileDelta, ImageFileDeltaBlock, MessageDelta, TextDelta, TextDeltaBlock
from openai.types.beta.threads.annotation import FileCitationAnnotation, FilePathAnnotation
from openai.types.beta.threads.file_citation_annotation import FileCitation
from openai.types.beta.threads.file_citation_delta_annotation import FileCitationDeltaAnnotation
from openai.types.beta.threads.file_path_annotation import FilePath
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.required_action_function_tool_call import Function
from openai.types.beta.threads.required_action_function_tool_call import Function as RequiredActionFunction
from openai.types.beta.threads.run import (
    LastError,
    RequiredAction,
    RequiredActionFunctionToolCall,
    RequiredActionSubmitToolOutputs,
    TruncationStrategy,
)
from openai.types.beta.threads.runs import (
    FunctionToolCallDelta,
    RunStep,
    RunStepDelta,
    RunStepDeltaEvent,
    ToolCallDeltaObject,
    ToolCallsStepDetails,
)
from openai.types.beta.threads.runs.code_interpreter_tool_call import (
    CodeInterpreter,
    CodeInterpreterToolCall,
)
from openai.types.beta.threads.runs.code_interpreter_tool_call_delta import CodeInterpreter as CodeInterpreterDelta
from openai.types.beta.threads.runs.code_interpreter_tool_call_delta import CodeInterpreterToolCallDelta
from openai.types.beta.threads.runs.function_tool_call import Function as RunsFunction
from openai.types.beta.threads.runs.function_tool_call import FunctionToolCall
from openai.types.beta.threads.runs.function_tool_call_delta import Function as FunctionForToolCallDelta
from openai.types.beta.threads.runs.message_creation_step_details import MessageCreation, MessageCreationStepDetails
from openai.types.beta.threads.runs.run_step import Usage
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.shared.response_format_json_object import ResponseFormatJSONObject

from semantic_kernel.agents.open_ai.assistant_content_generation import (
    generate_function_call_content,
    generate_function_result_content,
    generate_message_content,
    get_function_call_contents,
    get_message_contents,
)
from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import (
    AgentExecutionException,
    AgentFileNotFoundException,
    AgentInitializationException,
    AgentInvokeException,
)
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.kernel import Kernel

# region Test Fixtures


@pytest.fixture
def azure_openai_assistant_agent(kernel: Kernel, azure_openai_unit_test_env):
    return AzureAssistantAgent(
        kernel=kernel,
        service_id="test_service",
        name="test_name",
        instructions="test_instructions",
        api_key="test",
        metadata={"key": "value"},
        api_version="2024-05-01",
        description="test_description",
        ai_model_id="test_model",
        enable_code_interpreter=True,
        enable_file_search=True,
        vector_store_id="vector_store1",
        file_ids=["file1", "file2"],
        temperature=0.7,
        top_p=0.9,
        enable_json_response=True,
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
        role = "user"

    return MockMessage()


@pytest.fixture
def mock_thread_messages():
    class MockMessage:
        def __init__(self, id, role, content, assistant_id=None):
            self.id = id
            self.role = role
            self.content = content
            self.assistant_id = assistant_id

    return [
        MockMessage(
            id="test_message_id_1",
            role="user",
            content=[
                TextContentBlock(
                    type="text",
                    text=Text(
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
                    ),
                )
            ],
        ),
        MockMessage(
            id="test_message_id_2",
            role="assistant",
            content=[
                ImageFileContentBlock(type="image_file", image_file=ImageFile(file_id="test_file_id", detail="auto"))
            ],
            assistant_id="assistant_1",
        ),
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
        parallel_tool_calls=True,
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
        parallel_tool_calls=True,
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
        parallel_tool_calls=True,
    )


@pytest.fixture
def mock_run_incomplete():
    return Run(
        id="run_id",
        status="incomplete",
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
        parallel_tool_calls=True,
    )


@pytest.fixture
def mock_run_cancelled():
    return Run(
        id="run_id",
        status="cancelled",
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
        parallel_tool_calls=True,
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
            self.created_at = int(datetime.now(timezone.utc).timestamp())
            self.instructions = "instructions"
            self.model = "model"
            self.object = "run"
            self.thread_id = "thread_id"
            self.tools = []
            self.poll_count = 0
            self.required_action = RequiredAction(
                type="submit_tool_outputs",
                submit_tool_outputs=RequiredActionSubmitToolOutputs(
                    tool_calls=[
                        RequiredActionFunctionToolCall(
                            id="tool_call_id",
                            type="function",
                            function=Function(arguments="{}", name="function_name"),
                        )
                    ]
                ),
            )
            self.last_error = None

        def update_status(self):
            self.poll_count += 1
            if self.poll_count > 2:
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
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        created_at=int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
        step_details=ToolCallsStepDetails(
            tool_calls=[
                CodeInterpreterToolCall(
                    type="code_interpreter",
                    id="tool_call_id",
                    code_interpreter=CodeInterpreter(input="test code", outputs=[]),
                ),
                FunctionToolCall(
                    type="function",
                    id="tool_call_id",
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
def mock_run_step_function_tool_call():
    class MockToolCall:
        def __init__(self):
            self.type = "function"

    return RunStep(
        id="step_id_1",
        type="tool_calls",
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        created_at=int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
        step_details=ToolCallsStepDetails(
            tool_calls=[
                FunctionToolCall(
                    type="function",
                    id="tool_call_id",
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
        completed_at=int(datetime.now(timezone.utc).timestamp()),
        created_at=int((datetime.now(timezone.utc) - timedelta(minutes=2)).timestamp()),
        step_details=MessageCreationStepDetails(
            type="message_creation", message_creation=MessageCreation(message_id="test")
        ),
        assistant_id="assistant_id",
        object="thread.run.step",
        run_id="run_id",
        status="completed",
        thread_id="thread_id",
    )


class MockEvent:
    def __init__(self, event, data):
        self.event = event
        self.data = data


class MockRunData:
    def __init__(self, id, status):
        self.id = id
        self.status = status
        # Add other attributes as needed


def create_thread_message_delta_mock():
    return ThreadMessageDelta(
        data=MessageDeltaEvent(
            id="mock_msg_id",
            delta=MessageDelta(
                content=[
                    TextDeltaBlock(
                        index=0,
                        type="text",
                        text=TextDelta(
                            annotations=[
                                FileCitationDeltaAnnotation(
                                    index=0,
                                    type="file_citation",
                                    start_index=1,
                                    end_index=3,
                                    text="annotation",
                                )
                            ],
                            value="Hello",
                        ),
                    ),
                    ImageFileDeltaBlock(
                        index=0,
                        type="image_file",
                        image_file=ImageFileDelta(
                            file_id="test_file_id",
                            detail="auto",
                        ),
                    ),
                ],
                role=None,
            ),
            object="thread.message.delta",
        ),
        event="thread.message.delta",
    )


def create_thread_run_step_delta_mock():
    function = FunctionForToolCallDelta(name="math-Add", arguments="", output=None)
    function_tool_call = FunctionToolCallDelta(
        index=0, type="function", id="call_RcvYVzsppjjnUZcC47fAlwTW", function=function
    )
    code = CodeInterpreterDelta(input="import os")
    code_tool_call = CodeInterpreterToolCallDelta(
        index=1, type="code_interpreter", id="call_RcvYVzsppjjnUZcC47fAlwTW", code_interpreter=code
    )

    step_details = ToolCallDeltaObject(type="tool_calls", tool_calls=[function_tool_call, code_tool_call])
    delta = RunStepDelta(step_details=step_details)
    run_step_delta_event = RunStepDeltaEvent(
        id="step_FXzQ44kRmoeHOPUstkEI1UL5", delta=delta, object="thread.run.step.delta"
    )
    return ThreadRunStepDelta(data=run_step_delta_event, event="thread.run.step.delta")


def mock_thread_requires_action_run():
    return ThreadRunRequiresAction(
        data=Run(
            id="run_00OwjJnEg2SGJy8sky7ip35P",
            assistant_id="asst_wMMAX5F59szE7YHrCKSSgJlE",
            cancelled_at=None,
            completed_at=None,
            created_at=1727798684,
            expires_at=1727799284,
            failed_at=None,
            incomplete_details=None,
            instructions="Answer questions about the menu.",
            last_error=None,
            max_completion_tokens=None,
            max_prompt_tokens=None,
            metadata={},
            model="gpt-4o-2024-08-06",
            object="thread.run",
            parallel_tool_calls=True,
            required_action=RequiredAction(
                submit_tool_outputs=RequiredActionSubmitToolOutputs(
                    tool_calls=[
                        RequiredActionFunctionToolCall(
                            id="call_OTcZMjhm7WbhFnGkrmUjs68T",
                            function=Function(arguments="{}", name="menu-get_specials"),
                            type="function",
                        )
                    ]
                ),
                type="submit_tool_outputs",
            ),
            response_format="auto",
            started_at=1727798685,
            status="requires_action",
            thread_id="thread_jR4ZLlUwSrPcsLfdnGyFxi4Z",
            tool_choice="auto",
            tools=[
                FunctionTool(
                    function=FunctionDefinition(
                        name="menu-get_item_price",
                        description="Provides the price of the requested menu item.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "menu_item": {"type": "string", "description": "The name of the menu item."}
                            },
                            "required": ["menu_item"],
                        },
                        strict=False,
                    ),
                    type="function",
                ),
                FunctionTool(
                    function=FunctionDefinition(
                        name="menu-get_specials",
                        description="Provides a list of specials from the menu.",
                        parameters={"type": "object", "properties": {}, "required": []},
                        strict=False,
                    ),
                    type="function",
                ),
            ],
            truncation_strategy=TruncationStrategy(type="auto", last_messages=None),
            usage=None,
            temperature=1.0,
            top_p=1.0,
            tool_resources={"code_interpreter": {"file_ids": []}},
        ),
        event="thread.run.requires_action",
    )


def mock_thread_run_step_completed():
    return ThreadRunStepCompleted(
        data=RunStep(
            id="step_id_2",
            type="message_creation",
            completed_at=int(datetime.now(timezone.utc).timestamp()),
            created_at=int((datetime.now(timezone.utc) - timedelta(minutes=2)).timestamp()),
            step_details=MessageCreationStepDetails(
                type="message_creation", message_creation=MessageCreation(message_id="test")
            ),
            assistant_id="assistant_id",
            object="thread.run.step",
            run_id="run_id",
            status="completed",
            thread_id="thread_id",
            usage=Usage(completion_tokens=10, prompt_tokens=5, total_tokens=15),
        ),
        event="thread.run.step.completed",
    )


def mock_thread_run_step_completed_with_code():
    return ThreadRunStepCompleted(
        data=RunStep(
            id="step_id_2",
            type="message_creation",
            completed_at=int(datetime.now(timezone.utc).timestamp()),
            created_at=int((datetime.now(timezone.utc) - timedelta(minutes=2)).timestamp()),
            step_details=ToolCallsStepDetails(
                type="tool_calls",
                tool_calls=[
                    CodeInterpreterToolCall(
                        id="tool_call_id",
                        code_interpreter=CodeInterpreter(input="test code", outputs=[]),
                        type="code_interpreter",
                    )
                ],
            ),
            assistant_id="assistant_id",
            object="thread.run.step",
            run_id="run_id",
            status="completed",
            thread_id="thread_id",
            usage=Usage(completion_tokens=10, prompt_tokens=5, total_tokens=15),
        ),
        event="thread.run.step.completed",
    )


def mock_run_with_last_error():
    return ThreadRunFailed(
        data=Run(
            id="run_00OwjJnEg2SGJy8sky7ip35P",
            assistant_id="asst_wMMAX5F59szE7YHrCKSSgJlE",
            cancelled_at=None,
            completed_at=None,
            created_at=1727798684,
            expires_at=1727799284,
            failed_at=None,
            incomplete_details=None,
            instructions="Answer questions about the menu.",
            last_error=LastError(code="server_error", message="Server error"),
            max_completion_tokens=None,
            max_prompt_tokens=None,
            metadata={},
            model="gpt-4o-2024-08-06",
            object="thread.run",
            parallel_tool_calls=True,
            required_action=None,
            response_format="auto",
            started_at=1727798685,
            status="failed",
            thread_id="thread_jR4ZLlUwSrPcsLfdnGyFxi4Z",
            tool_choice="auto",
            tools=[],
            truncation_strategy=TruncationStrategy(type="auto", last_messages=None),
            usage=None,
            temperature=1.0,
            top_p=1.0,
            tool_resources={"code_interpreter": {"file_ids": []}},
        ),
        event="thread.run.failed",
    )


class MockAsyncIterable:
    def __init__(self, items):
        self.items = items.copy()

    def __aiter__(self):
        self._iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockStream:
    def __init__(self, events):
        self.events = events

    async def __aenter__(self):
        return MockAsyncIterable(self.events)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# endregion

# region Tests


async def test_create_assistant(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await azure_openai_assistant_agent.create_assistant(
            ai_model_id="test_model",
            description="test_description",
            instructions="test_instructions",
            name="test_name",
            enable_code_interpreter=True,
            enable_file_search=True,
            vector_store_id="vector_store1",
            code_interpreter_file_ids=["file1", "file2"],
            metadata={"key": "value"},
        )

        assert assistant.model == "test_model"
        assert assistant.description == "test_description"
        assert assistant.id == "test_id"
        assert assistant.instructions == "test_instructions"
        assert assistant.name == "test_name"
        assert assistant.tools == [CodeInterpreterTool(type="code_interpreter"), FileSearchTool(type="file_search")]
        assert assistant.temperature == 0.7
        assert assistant.top_p == 0.9
        assert assistant.response_format == ResponseFormatJSONObject(type="json_object")
        assert assistant.tool_resources == ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        )


async def test_modify_assistant(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await azure_openai_assistant_agent.create_assistant(
            ai_model_id="test_model",
            description="test_description",
            instructions="test_instructions",
            name="test_name",
            enable_code_interpreter=True,
            enable_file_search=True,
            vector_store_id="vector_store1",
            code_interpreter_file_ids=["file1", "file2"],
            metadata={"key": "value"},
        )

        mock_client.beta.assistants.update = AsyncMock(return_value=mock_assistant)

        assistant = await azure_openai_assistant_agent.modify_assistant(
            assistant_id=assistant.id,
            ai_model_id="test_model",
            description="test_description",
            instructions="test_instructions",
            name="test_name",
            enable_code_interpreter=True,
            enable_file_search=True,
            vector_store_id="vector_store1",
            code_interpreter_file_ids=["file1", "file2"],
            metadata={"key": "value"},
        )

        assert assistant.model == "test_model"
        assert assistant.description == "test_description"
        assert assistant.id == "test_id"
        assert assistant.instructions == "test_instructions"
        assert assistant.name == "test_name"
        assert assistant.tools == [CodeInterpreterTool(type="code_interpreter"), FileSearchTool(type="file_search")]
        assert assistant.temperature == 0.7
        assert assistant.top_p == 0.9
        assert assistant.response_format == ResponseFormatJSONObject(type="json_object")
        assert assistant.tool_resources == ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        )


async def test_modify_assistant_not_initialized_throws(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with pytest.raises(AgentInitializationException, match="The assistant has not been created."):
        _ = await azure_openai_assistant_agent.modify_assistant(
            assistant_id="id",
            ai_model_id="test_model",
            description="test_description",
            instructions="test_instructions",
            name="test_name",
            enable_code_interpreter=True,
            enable_file_search=True,
            vector_store_id="vector_store1",
            code_interpreter_file_ids=["file1", "file2"],
            metadata={"key": "value"},
        )


async def test_create_assistant_with_model_attributes(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await azure_openai_assistant_agent.create_assistant(
            ai_model_id="test_model",
            description="test_description",
            instructions="test_instructions",
            name="test_name",
            enable_code_interpreter=True,
            enable_file_search=True,
            vector_store_id="vector_store1",
            code_interpreter_file_ids=["file1", "file2"],
            metadata={"key": "value"},
            kwargs={"temperature": 0.1},
        )

        assert assistant.model == "test_model"
        assert assistant.description == "test_description"
        assert assistant.id == "test_id"
        assert assistant.instructions == "test_instructions"
        assert assistant.name == "test_name"
        assert assistant.tools == [CodeInterpreterTool(type="code_interpreter"), FileSearchTool(type="file_search")]
        assert assistant.temperature == 0.7
        assert assistant.top_p == 0.9
        assert assistant.response_format == ResponseFormatJSONObject(type="json_object")
        assert assistant.tool_resources == ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        )


async def test_create_assistant_delete_and_recreate(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)
        mock_client.beta.assistants.delete = AsyncMock()

        assistant = await azure_openai_assistant_agent.create_assistant()

        assert assistant is not None

        await azure_openai_assistant_agent.delete()

        assert azure_openai_assistant_agent._is_deleted

        assistant = await azure_openai_assistant_agent.create_assistant()

        assert azure_openai_assistant_agent._is_deleted is False


async def test_get_channel_keys(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    keys = azure_openai_assistant_agent.get_channel_keys()
    for key in keys:
        assert isinstance(key, str)


async def test_create_channel(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, mock_thread, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.create = AsyncMock(return_value=mock_thread)

        channel = await azure_openai_assistant_agent.create_channel()

        assert channel is not None


async def test_get_assistant_metadata(
    azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        assistant = await azure_openai_assistant_agent.create_assistant()

        assistant.metadata is not None


async def test_get_agent_tools(azure_openai_assistant_agent, mock_assistant, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        func = KernelFunctionFromMethod(method=kernel_function(lambda x: x**2, name="square"), plugin_name="math")
        azure_openai_assistant_agent.kernel.add_function(plugin_name="test", function=func)

        assistant = await azure_openai_assistant_agent.create_assistant()

        assert assistant.tools is not None
        assert len(assistant.tools) == 2
        tools = azure_openai_assistant_agent.tools
        assert len(tools) == 3
        assert tools[0] == {"type": "code_interpreter"}
        assert tools[1] == {"type": "file_search"}
        assert tools[2]["type"].startswith("function")


async def test_get_assistant_tools_throws_when_no_assistant(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with pytest.raises(AgentInitializationException, match="The assistant has not been created."):
        _ = azure_openai_assistant_agent.tools


async def test_create_thread(azure_openai_assistant_agent, mock_thread, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.create = AsyncMock(return_value=mock_thread)

        thread_id = await azure_openai_assistant_agent.create_thread(
            code_interpreter_file_ids=["file1", "file2"],
            vector_store_id="vector_store1",
            messages=[
                ChatMessageContent(role=AuthorRole.USER, content="test message"),
            ],
            metadata={"key": "value"},
        )

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


async def test_create_thread_throws_with_invalid_role(azure_openai_assistant_agent, mock_thread, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.create = AsyncMock(return_value=mock_thread)

        with pytest.raises(
            AgentExecutionException,
            match="Invalid message role `tool`",
        ):
            _ = await azure_openai_assistant_agent.create_thread(
                messages=[ChatMessageContent(role=AuthorRole.TOOL, content="test message")]
            )


async def test_delete_thread(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.delete = AsyncMock()

        await azure_openai_assistant_agent.delete_thread("test_thread_id")

        mock_client.beta.threads.delete.assert_called_once_with("test_thread_id")


async def test_delete(azure_openai_assistant_agent, mock_assistant, openai_unit_test_env):
    azure_openai_assistant_agent.assistant = mock_assistant

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.delete = AsyncMock()

        azure_openai_assistant_agent._is_deleted = False
        result = await azure_openai_assistant_agent.delete()

        assert result == azure_openai_assistant_agent._is_deleted
        mock_client.beta.assistants.delete.assert_called_once_with(mock_assistant.id)


async def test_add_file(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()
        mock_client.files.create = AsyncMock(return_value=MagicMock(id="test_file_id"))

        mock_open_file = mock_open(read_data="file_content")
        with patch("builtins.open", mock_open_file):
            file_id = await azure_openai_assistant_agent.add_file("test_file_path", "assistants")

            assert file_id == "test_file_id"
            mock_open_file.assert_called_once_with("test_file_path", "rb")
            mock_client.files.create.assert_called_once()


async def test_add_file_not_found(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()

        with patch("builtins.open", mock_open(read_data="file_content")) as mock_open_file:
            mock_open_file.side_effect = FileNotFoundError

            with pytest.raises(AgentFileNotFoundException, match="File not found: test_file_path"):
                await azure_openai_assistant_agent.add_file("test_file_path", "assistants")


async def test_delete_file(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()
        mock_client.files.delete = AsyncMock()

        await azure_openai_assistant_agent.delete_file("test_file_id")

        mock_client.files.delete.assert_called_once_with("test_file_id")


async def test_delete_file_raises_exception(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.files = MagicMock()
        mock_client.files.delete = AsyncMock(side_effect=Exception("Deletion failed"))

        with pytest.raises(AgentExecutionException, match="Error deleting file."):
            await azure_openai_assistant_agent.delete_file("test_file_id")

        mock_client.files.delete.assert_called_once_with("test_file_id")


async def test_create_vector_store(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.vector_stores = MagicMock()
        mock_client.beta.vector_stores.create = AsyncMock(return_value=MagicMock(id="test_vector_store_id"))

        vector_store_id = await azure_openai_assistant_agent.create_vector_store(["file_id1", "file_id2"])

        assert vector_store_id == "test_vector_store_id"
        mock_client.beta.vector_stores.create.assert_called_once_with(file_ids=["file_id1", "file_id2"])


async def test_create_vector_store_single_file_id(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.vector_stores = MagicMock()
        mock_client.beta.vector_stores.create = AsyncMock(return_value=MagicMock(id="test_vector_store_id"))

        vector_store_id = await azure_openai_assistant_agent.create_vector_store("file_id1")

        assert vector_store_id == "test_vector_store_id"
        mock_client.beta.vector_stores.create.assert_called_once_with(file_ids=["file_id1"])


async def test_create_vector_store_raises_exception(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.vector_stores = MagicMock()
        mock_client.beta.vector_stores.create = AsyncMock(side_effect=Exception("Creation failed"))

        with pytest.raises(AgentExecutionException, match="Error creating vector store."):
            await azure_openai_assistant_agent.create_vector_store("file_id1")

        mock_client.beta.vector_stores.create.assert_called_once_with(file_ids=["file_id1"])


async def test_delete_vector_store(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.vector_stores = MagicMock()
        mock_client.beta.vector_stores.delete = AsyncMock()

        await azure_openai_assistant_agent.delete_vector_store("test_vector_store_id")

        mock_client.beta.vector_stores.delete.assert_called_once_with("test_vector_store_id")


async def test_delete_vector_store_raises_exception(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.vector_stores = MagicMock()
        mock_client.beta.vector_stores.delete = AsyncMock(side_effect=Exception("Deletion failed"))

        with pytest.raises(AgentExecutionException, match="Error deleting vector store."):
            await azure_openai_assistant_agent.delete_vector_store("test_vector_store_id")

        mock_client.beta.vector_stores.delete.assert_called_once_with("test_vector_store_id")


async def test_add_chat_message(
    azure_openai_assistant_agent, mock_chat_message_content, mock_message, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.messages = MagicMock()
        mock_client.beta.threads.messages.create = AsyncMock(return_value=mock_message)

        result = await azure_openai_assistant_agent.add_chat_message("test_thread_id", mock_chat_message_content)

        assert result.id == "test_message_id"
        mock_client.beta.threads.messages.create.assert_called_once_with(
            thread_id="test_thread_id",
            role="user",
            content=[{"type": "text", "text": "test message"}],
        )


async def test_add_chat_message_invalid_role(
    azure_openai_assistant_agent, mock_chat_message_content, openai_unit_test_env
):
    mock_chat_message_content.role = AuthorRole.SYSTEM

    with pytest.raises(AgentExecutionException, match="Invalid message role `system`"):
        await azure_openai_assistant_agent.add_chat_message("test_thread_id", mock_chat_message_content)


async def test_get_thread_messages(
    azure_openai_assistant_agent, mock_thread_messages, mock_assistant, openai_unit_test_env
):
    async def mock_list_messages(*args, **kwargs) -> Any:
        return MagicMock(data=mock_thread_messages)

    async def mock_retrieve_assistant(*args, **kwargs) -> Any:
        return mock_assistant

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.threads.messages = MagicMock()
        mock_client.beta.threads.messages.list = AsyncMock(side_effect=mock_list_messages)
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.retrieve = AsyncMock(side_effect=mock_retrieve_assistant)

        messages = [message async for message in azure_openai_assistant_agent.get_thread_messages("test_thread_id")]

        assert len(messages) == 2
        assert len(messages[0].items) == 3
        assert isinstance(messages[0].items[0], TextContent)
        assert isinstance(messages[0].items[1], AnnotationContent)
        assert isinstance(messages[0].items[2], AnnotationContent)
        assert messages[0].items[0].text == "Hello"

        assert len(messages[1].items) == 1
        assert isinstance(messages[1].items[0], FileReferenceContent)
        assert str(messages[1].items[0].file_id) == "test_file_id"


async def test_invoke(
    azure_openai_assistant_agent,
    mock_assistant,
    mock_run_in_progress,
    mock_run_required_action,
    mock_chat_message_content,
    mock_run_step_tool_call,
    mock_run_step_message_creation,
    mock_thread_messages,
    mock_function_call_content,
    openai_unit_test_env,
):
    async def mock_poll_run_status(run, thread_id):
        run.update_status()
        return run

    def mock_get_function_call_contents(run, function_steps):
        function_call_content = mock_function_call_content
        function_call_content.id = "tool_call_id"  # Set expected ID
        function_steps[function_call_content.id] = function_call_content
        return [function_call_content]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)
        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.create = AsyncMock(return_value=mock_run_in_progress)
        mock_client.beta.threads.runs.submit_tool_outputs = AsyncMock()
        mock_client.beta.threads.runs.steps = MagicMock()
        mock_client.beta.threads.runs.steps.list = AsyncMock(
            return_value=MagicMock(data=[mock_run_step_message_creation, mock_run_step_tool_call])
        )

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()
        azure_openai_assistant_agent._get_tools = MagicMock(return_value=["tool"])
        azure_openai_assistant_agent._poll_run_status = AsyncMock(side_effect=mock_poll_run_status)
        azure_openai_assistant_agent._invoke_function_calls = AsyncMock()
        azure_openai_assistant_agent._format_tool_outputs = MagicMock(
            return_value=[{"tool_call_id": "id", "output": "output"}]
        )
        azure_openai_assistant_agent._retrieve_message = AsyncMock(return_value=mock_thread_messages[0])

        with patch(
            "semantic_kernel.agents.open_ai.assistant_content_generation.get_function_call_contents",
            side_effect=mock_get_function_call_contents,
        ):
            _ = [message async for message in azure_openai_assistant_agent.invoke("thread_id")]


async def test_invoke_order(
    azure_openai_assistant_agent,
    mock_assistant,
    mock_run_required_action,
    mock_run_step_function_tool_call,
    mock_run_step_message_creation,
    mock_thread_messages,
    mock_function_call_content,
):
    poll_count = 0

    async def mock_poll_run_status(run, thread_id):
        nonlocal poll_count
        if run.status == "requires_action":
            if poll_count == 0:
                pass
            else:
                run.status = "completed"
            poll_count += 1
        return run

    def mock_get_function_call_contents(run, function_steps):
        function_call_content = mock_function_call_content
        function_call_content.id = "tool_call_id"
        function_steps[function_call_content.id] = function_call_content
        return [function_call_content]

    azure_openai_assistant_agent.assistant = mock_assistant
    azure_openai_assistant_agent._poll_run_status = AsyncMock(side_effect=mock_poll_run_status)
    azure_openai_assistant_agent._retrieve_message = AsyncMock(return_value=mock_thread_messages[0])

    with patch(
        "semantic_kernel.agents.open_ai.assistant_content_generation.get_function_call_contents",
        side_effect=mock_get_function_call_contents,
    ):
        client = azure_openai_assistant_agent.client

        with patch.object(client.beta.threads.runs, "create", new_callable=AsyncMock) as mock_runs_create:
            mock_runs_create.return_value = mock_run_required_action

            with (
                patch.object(client.beta.threads.runs, "submit_tool_outputs", new_callable=AsyncMock),
                patch.object(client.beta.threads.runs.steps, "list", new_callable=AsyncMock) as mock_steps_list,
            ):
                mock_steps_list.return_value = MagicMock(
                    data=[mock_run_step_message_creation, mock_run_step_function_tool_call]
                )

                messages = []
                async for _, content in azure_openai_assistant_agent._invoke_internal("thread_id"):
                    messages.append(content)

    assert len(messages) == 3
    assert isinstance(messages[0].items[0], FunctionCallContent)
    assert isinstance(messages[1].items[0], FunctionResultContent)
    assert isinstance(messages[2].items[0], TextContent)


async def test_invoke_stream(
    azure_openai_assistant_agent,
    mock_assistant,
    mock_thread_messages,
    azure_openai_unit_test_env,
):
    events = [
        MockEvent("thread.run.created", MockRunData(id="run_1", status="queued")),
        MockEvent("thread.run.in_progress", MockRunData(id="run_1", status="in_progress")),
        create_thread_message_delta_mock(),
        mock_thread_run_step_completed(),
        MockEvent("thread.run.completed", MockRunData(id="run_1", status="completed")),
        mock_thread_requires_action_run(),
    ]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()

        messages = []
        async for content in azure_openai_assistant_agent.invoke_stream("thread_id", messages=messages):
            assert content is not None

        assert len(messages) > 0


async def test_invoke_stream_with_function_call(
    azure_openai_assistant_agent,
    mock_assistant,
    mock_thread_messages,
    azure_openai_unit_test_env,
):
    events = [create_thread_run_step_delta_mock()]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()

        async for content in azure_openai_assistant_agent.invoke_stream("thread_id"):
            assert content is not None


async def test_invoke_stream_code_output(
    azure_openai_assistant_agent,
    mock_assistant,
    azure_openai_unit_test_env,
):
    events = [mock_thread_run_step_completed_with_code()]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()

        messages = []
        async for content in azure_openai_assistant_agent.invoke_stream("thread_id", messages=messages):
            assert content is not None
            assert content.metadata.get("code") is True


async def test_invoke_stream_requires_action(
    azure_openai_assistant_agent, mock_assistant, mock_thread_messages, azure_openai_unit_test_env
):
    events = [
        mock_thread_requires_action_run(),
    ]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()

        messages = []
        async for content in azure_openai_assistant_agent.invoke_stream("thread_id", messages=messages):
            assert content is not None

        assert len(messages) > 0


async def test_invoke_stream_throws_exception(
    azure_openai_assistant_agent, mock_assistant, mock_thread_messages, azure_openai_unit_test_env
):
    events = [
        mock_run_with_last_error(),
    ]

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        mock_client.beta.threads.runs = MagicMock()
        mock_client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()

        with pytest.raises(AgentInvokeException):
            async for _ in azure_openai_assistant_agent.invoke_stream("thread_id"):
                pass


async def test_invoke_assistant_not_initialized_throws(azure_openai_assistant_agent, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The assistant has not been created."):
        _ = [message async for message in azure_openai_assistant_agent.invoke("thread_id")]


async def test_invoke_agent_deleted_throws(azure_openai_assistant_agent, mock_assistant, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()
        azure_openai_assistant_agent._is_deleted = True

        with pytest.raises(AgentInitializationException, match="The assistant has been deleted."):
            _ = [message async for message in azure_openai_assistant_agent.invoke("thread_id")]


async def test_invoke_raises_error(
    azure_openai_assistant_agent,
    mock_assistant,
    mock_run_in_progress,
    mock_run_step_tool_call,
    mock_run_step_message_creation,
    openai_unit_test_env,
):
    async def mock_poll_run_status(run, thread_id):
        run.status = "failed"
        return run

    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
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

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()
        azure_openai_assistant_agent._get_tools = MagicMock(return_value=["tool"])
        azure_openai_assistant_agent._poll_run_status = AsyncMock(side_effect=mock_poll_run_status)

        with pytest.raises(
            AgentInvokeException, match="Run failed with status: `failed` for agent `test_name` and thread `thread_id`"
        ):
            _ = [message async for message in azure_openai_assistant_agent.invoke("thread_id")]


@pytest.fixture
def mock_streaming_assistant_stream_manager() -> AsyncAssistantStreamManager[AsyncAssistantEventHandler]:
    assistant_event_handler = AsyncAssistantEventHandler()

    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [assistant_event_handler]

    mock_manager = AsyncMock(spec=AsyncAssistantStreamManager)
    mock_manager.__aenter__.return_value = mock_stream
    mock_manager.__aexit__.return_value = None

    return mock_manager


def test_format_tool_outputs(azure_openai_assistant_agent, openai_unit_test_env):
    chat_history = ChatHistory()
    fcc = FunctionCallContent(
        id="test", name="test-function", arguments='{"input": "world"}', metadata={"test": "test"}
    )
    frc = FunctionResultContent.from_function_call_content_and_result(fcc, 123, {"test2": "test2"})
    chat_history.add_message(message=frc.to_chat_message_content())

    tool_outputs = azure_openai_assistant_agent._format_tool_outputs([fcc], chat_history)
    assert tool_outputs[0] == {"tool_call_id": "test", "output": "123"}


async def test_invoke_function_calls(azure_openai_assistant_agent, openai_unit_test_env):
    chat_history = ChatHistory()
    fcc = FunctionCallContent(
        id="test", name="test-function", arguments='{"input": "world"}', metadata={"test": "test"}
    )

    with patch(
        "semantic_kernel.kernel.Kernel.invoke_function_call", new_callable=AsyncMock
    ) as mock_invoke_function_call:
        mock_invoke_function_call.return_value = "mocked_result"
        results = await azure_openai_assistant_agent._invoke_function_calls([fcc], chat_history)
        assert results == ["mocked_result"]
        mock_invoke_function_call.assert_called_once_with(function_call=fcc, chat_history=chat_history)


def test_get_function_call_contents(azure_openai_assistant_agent, mock_run_required_action, openai_unit_test_env):
    result = get_function_call_contents(run=mock_run_required_action, function_steps={})
    assert result is not None


def test_get_function_call_contents_no_action_required(
    azure_openai_assistant_agent, mock_run_required_action, openai_unit_test_env
):
    mock_run_required_action.required_action = None
    result = get_function_call_contents(run=mock_run_required_action, function_steps={})
    assert result == []


async def test_get_tools(azure_openai_assistant_agent: AzureAssistantAgent, mock_assistant, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.threads = MagicMock()
        mock_client.beta.assistants = MagicMock()
        mock_client.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        azure_openai_assistant_agent.assistant = await azure_openai_assistant_agent.create_assistant()
        tools = azure_openai_assistant_agent._get_tools()
        assert tools is not None


async def test_get_tools_no_assistant_returns_empty_list(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with pytest.raises(AgentInitializationException, match="The assistant has not been created."):
        _ = azure_openai_assistant_agent._get_tools()


def test_generate_message_content(azure_openai_assistant_agent, mock_thread_messages, openai_unit_test_env):
    for message in mock_thread_messages:
        result = generate_message_content(assistant_name="test", message=message)
        assert result is not None


def test_check_if_deleted_throws(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    azure_openai_assistant_agent._is_deleted = True
    with pytest.raises(AgentInitializationException, match="The assistant has been deleted."):
        azure_openai_assistant_agent._check_if_deleted()


def test_get_message_contents(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    message = ChatMessageContent(role=AuthorRole.USER, content="test message")
    message.items = [
        ImageContent(role=AuthorRole.ASSISTANT, content="test message", uri="http://image.url"),
        TextContent(role=AuthorRole.ASSISTANT, text="test message"),
        FileReferenceContent(role=AuthorRole.ASSISTANT, file_id="test_file_id"),
        TextContent(role=AuthorRole.USER, text="test message"),
        FunctionResultContent(role=AuthorRole.ASSISTANT, result=["test result"], id="test_id"),
    ]

    result = get_message_contents(message)
    assert result is not None


async def test_retrieve_message(azure_openai_assistant_agent, mock_thread_messages, openai_unit_test_env):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

        message = await azure_openai_assistant_agent._retrieve_message(
            thread_id="test_thread_id", message_id="test_message_id"
        )
        assert message is not None


async def test_retrieve_message_fails_polls_again(
    azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env
):
    with (
        patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client,
        patch("semantic_kernel.agents.open_ai.open_ai_assistant_agent.logger", autospec=True),
    ):
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.messages.retrieve = AsyncMock(side_effect=Exception("Unable to retrieve message"))

        message = await azure_openai_assistant_agent._retrieve_message(
            thread_id="test_thread_id", message_id="test_message_id"
        )
        assert message is None


async def test_poll_run_status(
    azure_openai_assistant_agent, mock_run_required_action, mock_run_completed, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(return_value=mock_run_completed)

        # Test successful polling
        run = await azure_openai_assistant_agent._poll_run_status(
            run=mock_run_required_action, thread_id="test_thread_id"
        )
        assert run.status == "completed", f"Expected status 'completed', but got '{run.status}'"

        # Test timeout scenario
        mock_client.beta.threads.runs.retrieve = AsyncMock(side_effect=TimeoutError)
        azure_openai_assistant_agent.polling_options.run_polling_timeout = timedelta(milliseconds=10)

        with pytest.raises(AgentInvokeException) as excinfo:
            await azure_openai_assistant_agent._poll_run_status(
                run=mock_run_required_action, thread_id="test_thread_id"
            )

        assert "Polling timed out" in str(excinfo.value)
        assert f"after waiting {azure_openai_assistant_agent.polling_options.run_polling_timeout}" in str(excinfo.value)


async def test_poll_run_status_incomplete(
    azure_openai_assistant_agent, mock_run_required_action, mock_run_incomplete, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(return_value=mock_run_incomplete)

        run = await azure_openai_assistant_agent._poll_run_status(
            run=mock_run_required_action, thread_id="test_thread_id"
        )

        assert run.status in azure_openai_assistant_agent.error_message_states


async def test_poll_run_status_cancelled(
    azure_openai_assistant_agent, mock_run_required_action, mock_run_cancelled, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(return_value=mock_run_cancelled)

        run = await azure_openai_assistant_agent._poll_run_status(
            run=mock_run_required_action, thread_id="test_thread_id"
        )

        assert run.status in azure_openai_assistant_agent.error_message_states


async def test_poll_run_status_exception_polls_again(
    azure_openai_assistant_agent, mock_run_required_action, mock_run_completed, openai_unit_test_env
):
    with patch.object(azure_openai_assistant_agent, "client", spec=AsyncAzureOpenAI) as mock_client:
        mock_client.beta = MagicMock()
        mock_client.beta.assistants = MagicMock()

        mock_client.beta.threads.runs.retrieve = AsyncMock(
            side_effect=[Exception("Failed to retrieve message"), mock_run_completed]
        )

        run = await azure_openai_assistant_agent._poll_run_status(
            run=mock_run_required_action, thread_id="test_thread_id"
        )
        assert run.status == "requires_action"


def test_generate_function_result_content(
    azure_openai_assistant_agent, mock_function_call_content, openai_unit_test_env
):
    mock_tool_call = RequiredActionFunctionToolCall(
        id="tool_call_id", type="function", function=Function(arguments="{}", name="function_name", output="result")
    )

    message = generate_function_result_content(
        agent_name="test", function_step=mock_function_call_content, tool_call=mock_tool_call
    )
    assert message is not None
    assert isinstance(message.items[0], FunctionResultContent)


def test_generate_function_call_content(azure_openai_assistant_agent, mock_function_call_content, openai_unit_test_env):
    message = generate_function_call_content(agent_name="test", fccs=[mock_function_call_content])
    assert message is not None
    assert isinstance(message, ChatMessageContent)
    assert isinstance(message.items[0], FunctionCallContent)


def test_merge_options(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    merged_options = azure_openai_assistant_agent._merge_options(
        ai_model_id="model-id",
        enable_json_response=True,
        enable_code_interpreter=True,
        enable_file_search=True,
        max_completion_tokens=150,
        parallel_tool_calls_enabled=True,
    )

    expected_options = {
        "ai_model_id": "model-id",
        "enable_code_interpreter": True,
        "enable_file_search": True,
        "enable_json_response": True,
        "max_completion_tokens": 150,
        "max_prompt_tokens": None,
        "parallel_tool_calls_enabled": True,
        "truncation_message_count": None,
        "temperature": 0.7,
        "top_p": 0.9,
        "metadata": {},
    }

    assert merged_options == expected_options, f"Expected {expected_options}, but got {merged_options}"


def test_generate_options(azure_openai_assistant_agent: AzureAssistantAgent, openai_unit_test_env):
    options = azure_openai_assistant_agent._generate_options(
        ai_model_id="model-id", max_completion_tokens=150, metadata={"key1": "value1"}
    )

    expected_options = {
        "max_completion_tokens": 150,
        "max_prompt_tokens": None,
        "model": "model-id",
        "top_p": 0.9,
        "response_format": None,
        "temperature": 0.7,
        "truncation_strategy": None,
        "metadata": {"key1": "value1"},
    }

    assert options == expected_options, f"Expected {expected_options}, but got {options}"


def test_generate_function_call_content_sets_assistant_role():
    fcc1 = FunctionCallContent(name="function_name1", arguments={"input": "some input"})
    fcc2 = FunctionCallContent(name="function_name2", arguments={"input": "other input"})
    agent_name = "TestAgent"

    result = generate_function_call_content(agent_name=agent_name, fccs=[fcc1, fcc2])

    assert result.role == AuthorRole.ASSISTANT
    assert result.name == agent_name
    assert len(result.items) == 2
    assert isinstance(result.items[0], FunctionCallContent)
    assert isinstance(result.items[1], FunctionCallContent)
    assert result.items[0].name == "function_name1"
    assert result.items[1].name == "function_name2"


# endregion
