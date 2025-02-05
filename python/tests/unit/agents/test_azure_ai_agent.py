# test_azure_ai_agent_settings.py

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.azure_ai.azure_ai_agent_settings import AzureAIAgentSettings


def test_azure_ai_agent_settings_valid():
    settings = AzureAIAgentSettings(
        model_deployment_name="test_model",
        project_connection_string="secret_value",
    )
    assert settings.model_deployment_name == "test_model"
    assert settings.project_connection_string.get_secret_value() == "secret_value"


def test_azure_ai_agent_settings_invalid():
    with pytest.raises(ValidationError):
        AzureAIAgentSettings(
            model_deployment_name="",  # Missing or invalid
            project_connection_string="",
        )


# ------------------------------------------------------------------------------------

# test_agent_content_generation.py

from azure.ai.projects.models import (
    MessageDeltaTextContent,
    MessageDeltaTextFileCitationAnnotation,
    MessageImageFileContent,
    MessageTextContent,
    MessageTextFilePathAnnotation,
    RunStep,
    RunStepDeltaFunctionToolCall,
    RunStepFunctionToolCall,
    ThreadMessage,
)

from semantic_kernel.agents.azure_ai.agent_content_generation import (
    generate_annotation_content,
    generate_code_interpreter_content,
    generate_function_call_content,
    generate_function_result_content,
    generate_message_content,
    generate_streaming_annotation_content,
    generate_streaming_code_interpreter_content,
    generate_streaming_function_content,
    generate_streaming_message_content,
    get_function_call_contents,
    get_message_contents,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def test_get_message_contents_all_types():
    chat_msg = ChatMessageContent(role=AuthorRole.USER)
    chat_msg.items.append(TextContent(text="hello world"))
    chat_msg.items.append(ImageContent(uri="http://example.com/image.png"))
    chat_msg.items.append(FileReferenceContent(file_id="file123"))
    chat_msg.items.append(FunctionResultContent(result={"a": 1}))
    results = get_message_contents(chat_msg)
    assert len(results) == 4
    assert results[0]["type"] == "text"
    assert results[1]["type"] == "image"
    assert results[2]["type"] == "image_file"
    assert results[3]["type"] == "text"


def test_generate_message_content_text_and_image():
    thread_msg = ThreadMessage(
        content=[
            MessageTextContent(type="text", text={"value": "some text", "annotations": []}),
            MessageImageFileContent(type="image_file", image_file={"file_id": "test_file_id"}),
        ],
        role="user",
    )
    step = RunStep(
        id="step_id",
        run_id="run_id",
        thread_id="thread_id",
        assistant_id="assistant_id",
        usage=None,
        created_at=None,
        completed_at=None,
        status=None,
        type=None,
        step_details=None,
    )
    content = generate_message_content("assistant", thread_msg, step)
    assert len(content.items) == 2
    assert isinstance(content.items[0], TextContent)
    assert isinstance(content.items[1], FileReferenceContent)
    assert content.metadata["step_id"] == "step_id"
    assert content.role == AuthorRole.USER


def test_generate_streaming_message_content_text_annotations():
    class FakeAnnotation(MessageDeltaTextFileCitationAnnotation):
        file_citation = type("FileCitation", (), {"file_id": "citation_file"})
        text = "cited text"
        start_index = 0
        end_index = 10

    fake_delta = MessageDeltaTextContent(
        type="text",
        text={
            "value": "Hello streaming text",
            "annotations": [FakeAnnotation()],
        },
        index=0,
    )
    chunk = type("DeltaChunk", (), {"delta": type("Delta", (), {"role": "assistant", "content": [fake_delta]})})()
    content = generate_streaming_message_content("assistant", chunk)
    assert len(content.items) == 2
    assert content.items[0].text == "Hello streaming text"
    assert content.items[1].file_id == "citation_file"


def test_get_function_call_contents_no_action():
    run = type("ThreadRunFake", (), {"required_action": None})()
    fc = get_function_call_contents(run, {})
    assert fc == []


def test_get_function_call_contents_submit_tool_outputs():
    class FakeFunction:
        name = "test_function"
        arguments = {"arg": "val"}

    class FakeToolCall:
        id = "tool_id"
        function = FakeFunction()

    run = type(
        "ThreadRunFake",
        (),
        {
            "required_action": type(
                "RequiredAction", (), {"submit_tool_outputs": type("FakeSubmit", (), {"tool_calls": [FakeToolCall()]})}
            )
        },
    )()
    function_steps = {}
    fc = get_function_call_contents(run, function_steps)
    assert len(fc) == 1
    assert function_steps["tool_id"].function_name == "test_function"


def test_generate_function_call_content():
    fcc = FunctionCallContent(id="id123", name="func_name", arguments={"x": 1})
    msg = generate_function_call_content("my_agent", [fcc])
    assert len(msg.items) == 1
    assert msg.role == AuthorRole.ASSISTANT


def test_generate_function_result_content():
    step = FunctionCallContent(id="123", name="func_name", arguments={"k": "v"})
    tool_call = RunStepFunctionToolCall(function=type("Function", (), {"output": "result_data"}))
    msg = generate_function_result_content("my_agent", step, tool_call)
    assert len(msg.items) == 1
    assert msg.items[0].result == "result_data"
    assert msg.role == AuthorRole.TOOL


def test_generate_code_interpreter_content():
    msg = generate_code_interpreter_content("my_agent", "some_code()")
    assert msg.content == "some_code()"
    assert msg.metadata["code"] is True


def test_generate_streaming_function_content_empty():
    step_details = type("Details", (), {"tool_calls": []})()
    assert generate_streaming_function_content("my_agent", step_details) is None


def test_generate_streaming_function_content_with_function():
    step_details = type(
        "Details",
        (),
        {
            "tool_calls": [
                RunStepDeltaFunctionToolCall(
                    id="tool123",
                    type="function",
                    function=type("FunObj", (), {"name": "some_func", "arguments": {"arg": "val"}}),
                )
            ]
        },
    )()
    msg = generate_streaming_function_content("my_agent", step_details)
    assert msg is not None
    assert len(msg.items) == 1
    assert msg.items[0].function_name == "some_func"


def test_generate_streaming_code_interpreter_content_no_calls():
    step_details = type("Details", (), {"tool_calls": None})
    assert generate_streaming_code_interpreter_content("my_agent", step_details) is None


def test_generate_annotation_content_path():
    ann = MessageTextFilePathAnnotation(
        file_path=type("FilePathObj", (), {"file_id": "file123"}),
        text="some text",
        start_index=0,
        end_index=9,
    )
    out = generate_annotation_content(ann)
    assert out.file_id == "file123"


def test_generate_streaming_annotation_content_citation():
    ann = MessageDeltaTextFileCitationAnnotation(
        file_citation=type("CitationObj", (), {"file_id": "file789"}),
        text="cite text",
        start_index=0,
        end_index=9,
    )
    out = generate_streaming_annotation_content(ann)
    assert out.file_id == "file789"


# ------------------------------------------------------------------------------------

# test_azure_ai_agent.py

from unittest.mock import AsyncMock, MagicMock, patch

from azure.ai.projects.models import Agent as AzureAIAgentModel

from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
async def test_azure_ai_agent_init():
    mock_client = MagicMock()
    mock_def = AzureAIAgentModel(id="agent123", name="agentName", description="desc", instructions="Do this")
    agent = AzureAIAgent(client=mock_client, definition=mock_def)
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"


@pytest.mark.asyncio
async def test_azure_ai_agent_add_chat_message():
    mock_client = MagicMock()
    mock_def = AzureAIAgentModel(id="agent123", name="agentName")
    agent = AzureAIAgent(client=mock_client, definition=mock_def)
    with patch.object(AgentThreadActions, "create_message", new_callable=AsyncMock) as mock_create_message:
        await agent.add_chat_message("threadId", MagicMock())
        mock_create_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_agent_invoke():
    mock_client = MagicMock()
    mock_def = AzureAIAgentModel(id="agent123", name="agentName", instructions="Hello")
    agent = AzureAIAgent(client=mock_client, definition=mock_def, kernel=Kernel())
    with patch.object(AgentThreadActions, "invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = __async_gen([(True, MagicMock())])
        results = []
        async for item in agent.invoke("threadId"):
            results.append(item)
        assert len(results) == 1
        mock_invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_agent_invoke_stream():
    mock_client = MagicMock()
    mock_def = AzureAIAgentModel(id="agent123", name="agentName")
    agent = AzureAIAgent(client=mock_client, definition=mock_def, kernel=Kernel())
    with patch.object(AgentThreadActions, "invoke_stream", new_callable=AsyncMock) as mock_invoke_stream:
        mock_invoke_stream.return_value = __async_gen([MagicMock()])
        results = []
        async for item in agent.invoke_stream("threadId"):
            results.append(item)
        assert len(results) == 1
        mock_invoke_stream.assert_awaited_once()


def test_azure_ai_agent_get_channel_keys():
    mock_client = MagicMock(scope="someScope")
    mock_def = AzureAIAgentModel(id="agent123", name="agentName")
    agent = AzureAIAgent(client=mock_client, definition=mock_def)
    keys = list(agent.get_channel_keys())
    assert len(keys) == 3
    assert "AzureAIAgent" in keys
    assert "agent123" in keys
    assert "agentName" in keys


@pytest.mark.asyncio
async def test_azure_ai_agent_create_channel():
    mock_client = MagicMock()
    mock_def = AzureAIAgentModel(id="agent123", name="agentName")
    with patch.object(AgentThreadActions, "create_thread", new_callable=AsyncMock) as mock_create_thread:
        mock_create_thread.return_value = "fakeThreadId"
        agent = AzureAIAgent(client=mock_client, definition=mock_def)
        ch = await agent.create_channel()
        assert isinstance(ch, AgentChannel)
        assert ch.thread_id == "fakeThreadId"


# Helper for converting list to async generator
async def __async_gen(items):
    for i in items:
        yield i


# ------------------------------------------------------------------------------------

# test_azure_ai_agent_utils.py

from azure.ai.projects.models import MessageAttachment, MessageRole

from semantic_kernel.agents.azure_ai.azure_ai_agent_utils import AzureAIAgentUtils


def test_azure_ai_agent_utils_get_thread_messages_none():
    msgs = AzureAIAgentUtils.get_thread_messages([])
    assert msgs is None


def test_azure_ai_agent_utils_get_thread_messages():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="Hello!")
    msg1.items.append(FileReferenceContent(file_id="file123"))
    results = AzureAIAgentUtils.get_thread_messages([msg1])
    assert len(results) == 1
    assert results[0].content == "Hello!"
    assert results[0].role == MessageRole.USER
    assert len(results[0].attachments) == 1
    assert isinstance(results[0].attachments[0], MessageAttachment)


def test_azure_ai_agent_utils_get_attachments_empty():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="No file items")
    atts = AzureAIAgentUtils.get_attachments(msg1)
    assert atts == []


def test_azure_ai_agent_utils_get_attachments_file():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="One file item")
    msg1.items.append(FileReferenceContent(file_id="file123"))
    atts = AzureAIAgentUtils.get_attachments(msg1)
    assert len(atts) == 1
    assert atts[0].file_id == "file123"


def test_azure_ai_agent_utils_get_metadata():
    msg1 = ChatMessageContent(role=AuthorRole.USER, content="has meta", metadata={"k": 123})
    meta = AzureAIAgentUtils.get_metadata(msg1)
    assert meta["k"] == "123"


def test_azure_ai_agent_utils_get_tool_definition():
    gen = AzureAIAgentUtils._get_tool_definition(["file_search", "code_interpreter", "non_existent"])
    # file_search & code_interpreter exist, non_existent yields nothing
    tools_list = list(gen)
    assert len(tools_list) == 2


# ------------------------------------------------------------------------------------

# test_agent_thread_actions.py

import pytest

from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException


@pytest.mark.asyncio
async def test_agent_thread_actions_create_thread():
    mock_client = MagicMock()
    mock_client.agents.create_thread.return_value = MagicMock(id="thread123")
    thread_id = await AgentThreadActions.create_thread(mock_client)
    assert thread_id == "thread123"


@pytest.mark.asyncio
async def test_agent_thread_actions_create_message():
    mock_client = MagicMock()
    mock_client.agents.create_message.return_value = MagicMock()
    msg = MagicMock(content="some content", items=[], role=MagicMock())
    out = await AgentThreadActions.create_message(mock_client, "threadXYZ", msg)
    assert out is not None
    mock_client.agents.create_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_agent_thread_actions_create_message_no_content():
    mock_client = MagicMock()
    message = MagicMock(content="    ", items=[], role=MagicMock())  # blank
    out = await AgentThreadActions.create_message(mock_client, "threadXYZ", message)
    assert out is None
    mock_client.agents.create_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_agent_thread_actions_invoke_cancelled_status():
    mock_agent = MagicMock()
    mock_agent.id = "agentID"
    mock_agent.name = "agentName"
    mock_agent.kernel = MagicMock()
    mock_agent.definition.model = "model"
    mock_agent.definition.tools = []
    mock_agent.definition.temperature = None
    mock_agent.definition.top_p = None
    mock_agent.definition.max_prompt_tokens = None
    mock_agent.definition.max_completion_tokens = None
    mock_agent.definition.instructions = "some instructions"

    mock_run = MagicMock()
    mock_run.status = "cancelled"
    mock_run.id = "runID"
    mock_run.last_error.message = "some error"

    with patch.object(mock_agent.client.agents, "create_run", new_callable=AsyncMock) as mock_create_run:
        mock_create_run.return_value = mock_run
        with pytest.raises(AgentInvokeException) as exc:
            async for _ in AgentThreadActions.invoke(agent=mock_agent, thread_id="threadXYZ"):
                pass
        assert "cancelled" in str(exc.value)


# Additional tests for other branches, coverage of poll loop, streaming, etc.,
# would follow similarly with mocks, appropriate statuses, exceptions, etc.

# ------------------------------------------------------------------------------------

# test_azure_ai_channel.py

import pytest

from semantic_kernel.agents.azure_ai.azure_ai_channel import AzureAIChannel
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


@pytest.mark.asyncio
async def test_azure_ai_channel_receive():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "thread123")
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.create_message", new_callable=AsyncMock
    ) as mock_create_message:
        await channel.receive([MagicMock()])
        mock_create_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_channel_invoke_invalid_agent():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "thread123")
    with pytest.raises(AgentChatException):
        async for _ in channel.invoke(MagicMock()):
            pass


@pytest.mark.asyncio
async def test_azure_ai_channel_invoke_valid_agent():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "thread123")
    agent = AzureAIAgent(client=mock_client, definition=MagicMock())
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke", new_callable=AsyncMock
    ) as mock_invoke:
        mock_invoke.return_value = __async_gen([(True, MagicMock())])
        results = []
        async for item in channel.invoke(agent):
            results.append(item)
        assert len(results) == 1
        mock_invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_channel_invoke_stream_valid_agent():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "thread123")
    agent = AzureAIAgent(client=mock_client, definition=MagicMock())
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream", new_callable=AsyncMock
    ) as mock_invoke_stream:
        mock_invoke_stream.return_value = __async_gen([MagicMock()])
        results = []
        async for item in channel.invoke_stream(agent, [MagicMock()]):
            results.append(item)
        assert len(results) == 1
        mock_invoke_stream.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_channel_get_history():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "threadXYZ")
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.get_messages", new_callable=AsyncMock
    ) as mock_get_messages:
        mock_get_messages.return_value = __async_gen([MagicMock()])
        results = []
        async for item in channel.get_history():
            results.append(item)
        assert len(results) == 1
        mock_get_messages.assert_awaited_once()


@pytest.mark.asyncio
async def test_azure_ai_channel_reset():
    mock_client = MagicMock()
    channel = AzureAIChannel(mock_client, "threadXYZ")
    await channel.reset()
    mock_client.agents.delete_thread.assert_awaited_once_with(thread_id="threadXYZ")


# Helper again
async def __async_gen(items):
    for i in items:
        yield i
