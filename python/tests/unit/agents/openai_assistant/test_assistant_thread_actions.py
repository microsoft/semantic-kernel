# Copyright (c) Microsoft. All rights reserved.


from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.assistant_stream_event import (
    ThreadMessageDelta,
    ThreadRunRequiresAction,
    ThreadRunStepCompleted,
    ThreadRunStepDelta,
)
from openai.types.beta.code_interpreter_tool import CodeInterpreterTool
from openai.types.beta.file_search_tool import FileSearchTool
from openai.types.beta.function_tool import FunctionTool
from openai.types.beta.threads import ImageFileDelta, ImageFileDeltaBlock, MessageDelta, TextDelta, TextDeltaBlock
from openai.types.beta.threads.file_citation_annotation import FileCitation, FileCitationAnnotation
from openai.types.beta.threads.file_citation_delta_annotation import FileCitationDeltaAnnotation
from openai.types.beta.threads.file_path_annotation import FilePath, FilePathAnnotation
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.message import Message
from openai.types.beta.threads.message_delta_event import MessageDeltaEvent
from openai.types.beta.threads.required_action_function_tool_call import Function, RequiredActionFunctionToolCall
from openai.types.beta.threads.run import (
    RequiredAction,
    RequiredActionSubmitToolOutputs,
    Run,
)
from openai.types.beta.threads.run_create_params import TruncationStrategy
from openai.types.beta.threads.runs import (
    FunctionToolCallDelta,
    RunStep,
    RunStepDelta,
    RunStepDeltaEvent,
    ToolCallDeltaObject,
    ToolCallsStepDetails,
)
from openai.types.beta.threads.runs.code_interpreter_tool_call import CodeInterpreter, CodeInterpreterToolCall
from openai.types.beta.threads.runs.code_interpreter_tool_call_delta import CodeInterpreter as CodeInterpreterDelta
from openai.types.beta.threads.runs.code_interpreter_tool_call_delta import CodeInterpreterToolCallDelta
from openai.types.beta.threads.runs.function_tool_call import Function as RunsFunction
from openai.types.beta.threads.runs.function_tool_call import FunctionToolCall
from openai.types.beta.threads.runs.function_tool_call_delta import Function as FunctionForToolCallDelta
from openai.types.beta.threads.runs.message_creation_step_details import MessageCreation, MessageCreationStepDetails
from openai.types.beta.threads.runs.run_step import Usage
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.shared.function_definition import FunctionDefinition

from semantic_kernel.agents.open_ai.assistant_thread_actions import AssistantThreadActions
from semantic_kernel.agents.open_ai.function_action_result import FunctionActionResult
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


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


class MockError:
    def __init__(self, message: str):
        self.message = message


class MockRunData:
    def __init__(self, id, status):
        self.id = id
        self.status = status


class ErrorMockRunData(MockRunData):
    def __init__(self, id, status, last_error=None):
        super().__init__(id, status)
        self.last_error = last_error


class MockEvent:
    def __init__(self, event, data):
        self.event = event
        self.data = data


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
                CodeInterpreterToolCall(  # type: ignore
                    type="code_interpreter",
                    id="tool_call_id",
                    code_interpreter=CodeInterpreter(input="test code", outputs=[]),
                ),
                FunctionToolCall(
                    type="function",
                    id="tool_call_id",
                    function=RunsFunction(arguments="{}", name="function_name", output="test output"),
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
            tool_resources={"code_interpreter": {"file_ids": []}},  # type: ignore
        ),
        event="thread.run.requires_action",
    )


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
                                file_citation=FileCitation(file_id="test_file_id"),
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


class SamplePlugin:
    @kernel_function
    def test_plugin(self, *args, **kwargs):
        pass


async def test_agent_thread_actions_create_message():
    client = AsyncMock(spec=AsyncOpenAI)
    client.beta = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.threads.messages = MagicMock()
    client.beta.threads.messages.create = AsyncMock(spec=Message)

    msg = ChatMessageContent(role=AuthorRole.USER, content="some content")
    created_message = await AssistantThreadActions.create_message(client, "threadXYZ", msg)
    assert created_message is not None


async def test_assistant_thread_actions_invoke(
    mock_run_step_message_creation, mock_run_step_tool_call, mock_run_in_progress, mock_thread_messages
):
    async def mock_poll_run_status(agent, run, thread_id, polling_options):
        run.update_status()
        return run

    sample_prompt_template_config = PromptTemplateConfig(
        template="template",
    )

    kernel_plugin = KernelPlugin(name="expected_plugin_name", description="expected_plugin_description")

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = [FileSearchTool(type="file_search"), CodeInterpreterTool(type="code_interpreter")]
    definition.model = "gpt-4o"
    definition.temperature = (1.0,)
    definition.top_p = 1.0
    definition.metadata = {}

    client.beta = MagicMock()
    client.beta.threads = MagicMock()
    client.beta.threads.runs = MagicMock()
    client.beta.threads.runs.create = AsyncMock(return_value=mock_run_in_progress)
    client.beta.threads.runs.submit_tool_outputs = AsyncMock()
    client.beta.threads.runs.steps = MagicMock()
    client.beta.threads.runs.steps.list = AsyncMock(
        return_value=MagicMock(data=[mock_run_step_message_creation, mock_run_step_tool_call])
    )

    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
        arguments=KernelArguments(test="test"),
        kernel=AsyncMock(spec=Kernel),
        plugins=[SamplePlugin(), kernel_plugin],
        polling_options=AsyncMock(spec=RunPollingOptions),
        prompt_template_config=sample_prompt_template_config,
        other_arg="test",
    )

    with (
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions._poll_run_status",
            new=AsyncMock(side_effect=mock_poll_run_status),
        ),
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions._retrieve_message",
            new=AsyncMock(side_effect=AsyncMock(return_value=mock_thread_messages[0])),
        ),
    ):
        async for message in AssistantThreadActions.invoke(
            agent=agent,
            thread_id="thread123",
            kernel=AsyncMock(spec=Kernel),
            additional_messages=[
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content="additional content",
                    items=[FileReferenceContent(file_id="file_id", tools=["file_search"])],
                    metadata={"sample_metadata_key": "sample_metadata_val"},
                )
            ],
        ):
            assert message is not None


async def test_assistant_thread_actions_stream(
    mock_thread_messages,
):
    events = [
        MockEvent("thread.run.created", MockRunData(id="run_1", status="queued")),
        MockEvent("thread.run.in_progress", MockRunData(id="run_1", status="in_progress")),
        mock_thread_run_step_completed(),
        MockEvent("thread.run.completed", MockRunData(id="run_1", status="completed")),
        MockEvent(
            "thread.run.failed", ErrorMockRunData(id="run_1", status="failed", last_error=MockError("Test error"))
        ),
    ]

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = []
    definition.model = "gpt-4o"
    definition.temperature = 0.7
    definition.top_p = 0.9
    definition.metadata = {}
    definition.response_format = {"type": "json_object"}

    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    client.beta = MagicMock()
    client.beta.threads = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.threads.runs = MagicMock()
    client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))
    client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

    # Set up agent prompts
    agent.instructions = "Base instructions"
    agent.prompt_template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(template="Template instructions")
    )

    # Scenario A: Use only prompt template
    messages = []
    async for content in AssistantThreadActions.invoke_stream(
        agent=agent, thread_id="thread_id", output_messages=messages
    ):
        assert content is not None


async def test_assistant_thread_actions_stream_run_fails(
    mock_thread_messages,
):
    events = [
        MockEvent("thread.run.failed", ErrorMockRunData(id=1, status="failed", last_error=MockError("Test error"))),
    ]

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = []
    definition.model = "gpt-4o"
    definition.temperature = 0.7
    definition.top_p = 0.9
    definition.metadata = {}
    definition.response_format = {"type": "json_object"}

    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    client.beta = MagicMock()
    client.beta.threads = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.threads.runs = MagicMock()
    client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))
    client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

    # Set up agent prompts
    agent.instructions = "Base instructions"
    agent.prompt_template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(template="Template instructions")
    )

    # Scenario A: Use only prompt template
    messages = []
    with pytest.raises(AgentInvokeException):
        async for _ in AssistantThreadActions.invoke_stream(
            agent=agent, thread_id="thread_id", output_messages=messages
        ):
            pass


async def test_assistant_thread_actions_stream_with_instructions(
    mock_thread_messages,
):
    events = [
        MockEvent("thread.run.created", MockRunData(id="run_1", status="queued")),
        MockEvent("thread.run.in_progress", MockRunData(id="run_1", status="in_progress")),
        create_thread_message_delta_mock(),
        create_thread_run_step_delta_mock(),
        mock_thread_requires_action_run(),
        mock_thread_run_step_completed(),
        MockEvent("thread.run.completed", MockRunData(id="run_1", status="completed")),
    ]

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = []
    definition.model = "gpt-4o"
    definition.temperature = 0.7
    definition.top_p = 0.9
    definition.metadata = {}
    definition.response_format = {"type": "json_object"}

    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    client.beta = MagicMock()
    client.beta.threads = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.threads.runs = MagicMock()
    client.beta.threads.runs.stream = MagicMock(return_value=MockStream(events))
    client.beta.threads.messages.retrieve = AsyncMock(side_effect=mock_thread_messages)

    # Set up agent prompts
    agent.instructions = "Base instructions"
    agent.prompt_template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(template="Template instructions")
    )

    # Scenario A: Use only prompt template
    messages = []
    async for content in AssistantThreadActions.invoke_stream(
        agent=agent, thread_id="thread_id", output_messages=messages
    ):
        assert content is not None

    assert len(messages) > 0, "Expected messages to be populated during the stream."
    client.beta.threads.runs.stream.assert_called_once_with(
        assistant_id=agent.id,
        thread_id="thread_id",
        instructions="Template instructions",
        tools=[],
        temperature=0.7,
        top_p=0.9,
        model="gpt-4o",
        metadata={},
    )

    client.beta.threads.runs.stream.reset_mock()

    # Scenario B: Use prompt template with additional instructions
    messages = []
    async for content in AssistantThreadActions.invoke_stream(
        agent=agent,
        thread_id="thread_id",
        output_messages=messages,
        additional_instructions="My additional instructions",
    ):
        assert content is not None

    assert len(messages) > 0, "Expected messages to be populated during the stream."
    client.beta.threads.runs.stream.assert_called_once_with(
        assistant_id=agent.id,
        thread_id="thread_id",
        instructions="Template instructions\n\nMy additional instructions",
        tools=[],
        temperature=0.7,
        top_p=0.9,
        model="gpt-4o",
        metadata={},
    )

    client.beta.threads.runs.stream.reset_mock()


async def test_poll_loop_exits_on_status_change():
    AssistantThreadActions.polling_status = {"in_progress"}  # type: ignore

    polling_interval = timedelta(seconds=0.01)
    dummy_polling_options = MagicMock()
    dummy_polling_options.get_polling_interval = lambda count: polling_interval

    run_id = "run_123"
    initial_run = MagicMock()
    initial_run.id = run_id

    polling_options = RunPollingOptions()

    run_in_progress = MagicMock()
    run_in_progress.id = run_id
    run_in_progress.status = "in_progress"

    run_completed = MagicMock()
    run_completed.id = run_id
    run_completed.status = "completed"

    dummy_agent = MagicMock()
    dummy_agent.polling_options = dummy_polling_options
    dummy_agent.client.beta.threads.runs.retrieve = AsyncMock(side_effect=[run_in_progress, run_completed])

    thread_id = "thread_123"

    result_run = await AssistantThreadActions._poll_loop(dummy_agent, initial_run, thread_id, polling_options)

    assert result_run.status == "completed"


async def test_handle_streaming_requires_action_returns_result():
    dummy_run = MagicMock()
    dummy_run.id = "dummy_run_id"
    dummy_function_steps = {"step1": MagicMock()}
    dummy_fccs = {"fcc_key": "fcc_value"}
    dummy_function_call_streaming_content = MagicMock()
    dummy_function_result_streaming_content = MagicMock()
    dummy_tool_outputs = {"output": "value"}
    dummy_kernel = MagicMock()
    dummy_agent_name = "TestAgent"
    dummy_args = {}
    with (
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.get_function_call_contents",
            return_value=dummy_fccs,
        ),
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.generate_function_call_streaming_content",
            return_value=dummy_function_call_streaming_content,
        ),
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.merge_streaming_function_results",
            return_value=dummy_function_result_streaming_content,
        ),
        patch.object(AssistantThreadActions, "_invoke_function_calls", new=AsyncMock(return_value=[None])),
        patch.object(AssistantThreadActions, "_format_tool_outputs", return_value=dummy_tool_outputs),
    ):
        result = await AssistantThreadActions._handle_streaming_requires_action(
            dummy_agent_name,
            dummy_kernel,
            dummy_run,
            dummy_function_steps,  # type: ignore
            dummy_args,
        )
        assert result is not None
        assert isinstance(result, FunctionActionResult)
        assert result.function_call_streaming_content == dummy_function_call_streaming_content
        assert result.function_result_streaming_content == dummy_function_result_streaming_content
        assert result.tool_outputs == dummy_tool_outputs


async def test_handle_streaming_requires_action_returns_none():
    dummy_run = MagicMock()
    dummy_run.id = "dummy_run_id"
    dummy_function_steps = {"step1": MagicMock()}
    dummy_kernel = MagicMock()
    dummy_agent_name = "TestAgent"
    dummy_args = {}
    with patch("semantic_kernel.agents.open_ai.assistant_thread_actions.get_function_call_contents", return_value=None):
        result = await AssistantThreadActions._handle_streaming_requires_action(
            dummy_agent_name,
            dummy_kernel,
            dummy_run,
            dummy_function_steps,  # type: ignore
            dummy_args,
        )
        assert result is None
