# Copyright (c) Microsoft. All rights reserved.

"""A cut-off reply must not run a tool call whose arguments never arrived.

These tests go through the real `OpenAIChatCompletion` connector: the OpenAI client gets a mock HTTP
transport, so the request and the streamed response are handled exactly as in production.
"""

import json

import httpx
import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

TOOL = "set_mode"


class RecordingPlugin:
    """`set_mode` has only optional parameters; `do_action` requires one."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @kernel_function(name=TOOL, description="set the mode")
    def set_mode(self, mode: str = "default") -> str:
        self.calls.append(f"set_mode(mode={mode!r})")
        return "done"

    @kernel_function(name="do_action", description="do the action")
    def do_action(self, target: str) -> str:
        self.calls.append(f"do_action(target={target!r})")
        return "done"


def _chunk(delta: dict, finish: str | None = None) -> str:
    return (
        "data: "
        + json.dumps({
            "id": "chatcmpl-mock",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "gpt-4o-mini",
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
        })
        + "\n\n"
    )


def _tool_delta(arguments: str | None = None, name: str | None = None, call_id: str = "") -> dict:
    function: dict = {}
    if name is not None:
        function["name"] = name
    if arguments is not None:
        function["arguments"] = arguments
    return {
        "role": "assistant",
        "tool_calls": [{"index": 0, "id": call_id, "type": "function", "function": function}],
    }


def _stream_body(fragments: list[str], finish: str, name: str | None = TOOL) -> bytes:
    """One tool call streamed the way the API streams it.

    The first delta carries the call id, the function name and an empty argument string; every later
    delta carries an empty id and no name, so only the index identifies it. Captured from qwen-plus:
    `{"index": 0, "id": "call_...", "function": {"name": "set_mode", "arguments": ""}}` then
    `{"index": 0, "id": "", "function": {"arguments": "{\\""}}`.
    """
    body = _chunk(_tool_delta(arguments="", name=name, call_id="call_1"))
    body += "".join(_chunk(_tool_delta(fragment)) for fragment in fragments)
    return (body + _chunk({}, finish) + "data: [DONE]\n\n").encode()


def _body(arguments: str | None, finish: str, name: str = TOOL) -> bytes:
    function: dict = {"name": name}
    if arguments is not None:
        function["arguments"] = arguments
    return json.dumps({
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "call_1", "type": "function", "function": function}],
                },
                "finish_reason": finish,
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }).encode()


def _service(body: bytes, sse: bool) -> OpenAIChatCompletion:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream" if sse else "application/json"},
            content=body,
        )

    client = AsyncOpenAI(
        api_key="sk-" + "a" * 48,
        base_url="http://mock/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    return OpenAIChatCompletion(ai_model_id="gpt-4o-mini", async_client=client)


def _settings() -> PromptExecutionSettings:
    return PromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True, maximum_auto_invoke_attempts=1)
    )


def _kernel(plugin: RecordingPlugin) -> Kernel:
    kernel = Kernel()
    kernel.add_plugin(plugin, plugin_name="record")
    return kernel


async def _invoke(plugin: RecordingPlugin, service: OpenAIChatCompletion, stream: bool) -> list:
    history = ChatHistory()
    history.add_user_message("do it")
    if not stream:
        await service.get_chat_message_contents(history, _settings(), kernel=_kernel(plugin))
        return []
    yielded = []
    async for message in service.get_streaming_chat_message_content(history, _settings(), kernel=_kernel(plugin)):
        yielded.append(message)
    return yielded


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_cut_off_reply_with_empty_arguments_does_not_run_the_tool(stream: bool) -> None:
    """max_tokens stopped the model right after the tool name, so no parameter was ever written."""
    plugin = RecordingPlugin()
    body = _stream_body([""], "length") if stream else _body("", "length")
    await _invoke(plugin, _service(body, stream), stream)

    assert plugin.calls == [], f"tool ran with defaults: {plugin.calls!r}"


@pytest.mark.asyncio
async def test_cut_off_reply_with_several_empty_fragments_does_not_run_the_tool() -> None:
    """Empty fragments are combined into "{}" by the aggregation, which must not look like real arguments."""
    plugin = RecordingPlugin()
    await _invoke(plugin, _service(_stream_body(["", "", ""], "length"), True), True)

    assert plugin.calls == [], f"tool ran with defaults: {plugin.calls!r}"


@pytest.mark.asyncio
async def test_cut_off_reply_with_an_explicit_empty_object_still_runs_the_tool() -> None:
    """The model really wrote {}, so the call is complete even though the reply was cut off afterwards."""
    plugin = RecordingPlugin()
    await _invoke(plugin, _service(_stream_body(["{", "}"], "length"), True), True)

    assert plugin.calls == ["set_mode(mode='default')"]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_cut_off_reply_with_empty_arguments_does_not_run_a_tool_needing_one(stream: bool) -> None:
    plugin = RecordingPlugin()
    body = _stream_body([""], "length", "do_action") if stream else _body("", "length", "do_action")
    await _invoke(plugin, _service(body, stream), stream)

    assert plugin.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_cut_off_reply_with_complete_arguments_still_runs_the_tool(stream: bool) -> None:
    """Compatibility: the model finished writing its arguments and only then hit the limit.

    Streamed, the arguments arrive in several chunks that carry no call id (captured from qwen-plus at
    `max_tokens=9`), so the pieces must be recognised as one call that did write its arguments.
    """
    plugin = RecordingPlugin()
    body = _stream_body(['{"', 'mode": "', 'silent"}'], "length") if stream else _body('{"mode": "silent"}', "length")
    await _invoke(plugin, _service(body, stream), stream)

    assert plugin.calls == ["set_mode(mode='silent')"]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_zero_argument_call_in_a_complete_reply_still_runs(stream: bool) -> None:
    """Compatibility: an empty argument string is normal for a tool without parameters."""
    plugin = RecordingPlugin()
    body = _stream_body([""], "tool_calls") if stream else _body("", "tool_calls")
    await _invoke(plugin, _service(body, stream), stream)

    assert plugin.calls == ["set_mode(mode='default')"]


@pytest.mark.asyncio
async def test_missing_arguments_from_the_connector_are_not_run_either() -> None:
    """Anthropic reports a tool without input as no argument text; a cut-off reply still must not run it."""
    plugin = RecordingPlugin()
    await _invoke(plugin, _service(_body(None, "length"), False), False)

    assert plugin.calls == []


@pytest.mark.asyncio
async def test_refused_streamed_call_reports_its_result_to_the_caller() -> None:
    """A refused call must reach the caller like any other tool result, not disappear."""
    plugin = RecordingPlugin()
    yielded = await _invoke(plugin, _service(_stream_body([""], "length"), True), True)

    results = [
        item for message in yielded if message for item in message.items if isinstance(item, FunctionResultContent)
    ]
    assert plugin.calls == []
    assert [r.name for r in results] == [TOOL]
    assert "cut off" in str(results[0].result)


@pytest.mark.asyncio
async def test_agent_stream_sends_the_refusal_back_to_the_model() -> None:
    """The agent filters tool results from the caller stream, so what matters is that the model sees the refusal."""
    from semantic_kernel.agents import ChatCompletionAgent
    from semantic_kernel.functions.kernel_arguments import KernelArguments

    requests: list[bytes] = []
    cut_off = _stream_body([""], "length")
    follow_up = (_chunk({"role": "assistant", "content": "ok"}) + _chunk({}, "stop") + "data: [DONE]\n\n").encode()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.content)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=cut_off if len(requests) == 1 else follow_up,
        )

    client = AsyncOpenAI(
        api_key="sk-" + "a" * 48,
        base_url="http://mock/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    plugin = RecordingPlugin()
    agent = ChatCompletionAgent(
        kernel=_kernel(plugin),
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini", async_client=client),
        name="probe",
    )

    async for _ in agent.invoke_stream(messages=ChatHistory(), arguments=KernelArguments()):
        pass

    assert plugin.calls == []
    assert len(requests) == 2, "the cut-off reply should have been followed by another attempt"
    assert "cut off at the token limit" in requests[1].decode()


def _anthropic_service(stop_reason: str) -> object:
    """Anthropic-format connectors hand over the parsed tool input, not the raw argument text.

    Bedrock reports a call cut off right after the tool name as `input={}` in the non-streamed reply
    (verified on Bedrock with Claude Haiku 4.5, `max_tokens=40`), so this loop sees an empty mapping
    where the OpenAI connector would have handed it the text `""`.
    """
    from unittest.mock import AsyncMock, MagicMock

    from anthropic import AsyncAnthropic
    from anthropic.types import Message, ToolUseBlock, Usage

    from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import (
        AnthropicChatCompletion,
    )

    message = Message(
        id="msg_1",
        content=[ToolUseBlock(id="toolu_1", type="tool_use", name=TOOL, input={})],
        model="claude-3-5-haiku-20241022",
        role="assistant",
        stop_reason=stop_reason,
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=10),
    )
    client = MagicMock(spec=AsyncAnthropic)
    client.messages.create = AsyncMock(return_value=message)
    return AnthropicChatCompletion(
        ai_model_id="claude-3-5-haiku-20241022", service_id="test", api_key="", async_client=client
    )


async def _invoke_anthropic(plugin: RecordingPlugin, service) -> None:
    from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
        AnthropicChatPromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments

    settings = AnthropicChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True, maximum_auto_invoke_attempts=1)
    )
    history = ChatHistory(system_message="Test")
    history.add_user_message("do it")
    await service.get_chat_message_contents(history, settings, kernel=_kernel(plugin), arguments=KernelArguments())


@pytest.mark.asyncio
async def test_cut_off_reply_that_arrives_as_an_empty_mapping_does_not_run_the_tool() -> None:
    """The arguments never arrived, they were just reported as an empty mapping instead of an empty string."""
    plugin = RecordingPlugin()
    await _invoke_anthropic(plugin, _anthropic_service("max_tokens"))

    assert plugin.calls == [], f"tool ran with defaults: {plugin.calls!r}"


@pytest.mark.asyncio
async def test_empty_mapping_in_a_reply_that_was_not_cut_off_still_runs_the_tool() -> None:
    """A deliberate no-argument call ends with `tool_use`, so an empty mapping is only nothing-written under length."""
    plugin = RecordingPlugin()
    await _invoke_anthropic(plugin, _anthropic_service("tool_use"))

    assert plugin.calls == ["set_mode(mode='default')"]


def _anthropic_streaming_service(stop_reason: str) -> object:
    """The same connector, streamed: the tool input is serialized to `"{}"` instead of handed over as a mapping."""
    from unittest.mock import AsyncMock, MagicMock

    from anthropic import AsyncAnthropic
    from anthropic.types import (
        ContentBlockStopEvent,
        Message,
        MessageDeltaUsage,
        RawMessageDeltaEvent,
        RawMessageStartEvent,
        ToolUseBlock,
        Usage,
    )
    from anthropic.types.raw_message_delta_event import Delta

    from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import (
        AnthropicChatCompletion,
    )

    events = [
        RawMessageStartEvent(
            message=Message(
                id="msg_1",
                content=[],
                model="claude-3-5-haiku-20241022",
                role="assistant",
                stop_reason=None,
                stop_sequence=None,
                type="message",
                usage=Usage(input_tokens=10, output_tokens=1),
            ),
            type="message_start",
        ),
        ContentBlockStopEvent(
            index=0,
            type="content_block_stop",
            content_block=ToolUseBlock(id="toolu_1", type="tool_use", name=TOOL, input={}),
        ),
        RawMessageDeltaEvent(
            delta=Delta(stop_reason=stop_reason, stop_sequence=None),
            type="message_delta",
            usage=MessageDeltaUsage(output_tokens=5),
        ),
    ]

    async def async_generator():
        for event in events:
            yield event

    stream = AsyncMock()
    stream.__aenter__.return_value = async_generator()

    client = MagicMock(spec=AsyncAnthropic)
    client.messages = MagicMock()
    client.messages.stream.return_value = stream
    return AnthropicChatCompletion(
        ai_model_id="claude-3-5-haiku-20241022", service_id="test", api_key="", async_client=client
    )


async def _invoke_anthropic_stream(plugin: RecordingPlugin, service) -> None:
    from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
        AnthropicChatPromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments

    settings = AnthropicChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True, maximum_auto_invoke_attempts=1)
    )
    history = ChatHistory(system_message="Test")
    history.add_user_message("do it")
    async for _ in service.get_streaming_chat_message_content(
        history, settings, kernel=_kernel(plugin), arguments=KernelArguments()
    ):
        pass


@pytest.mark.asyncio
async def test_cut_off_streamed_reply_that_arrives_as_an_empty_object_does_not_run_the_tool() -> None:
    """The connector serializes the cut-off input to `"{}"`, which the aggregation cannot tell from written text."""
    plugin = RecordingPlugin()
    await _invoke_anthropic_stream(plugin, _anthropic_streaming_service("max_tokens"))

    assert plugin.calls == [], f"tool ran with defaults: {plugin.calls!r}"


@pytest.mark.asyncio
async def test_empty_object_in_a_streamed_reply_that_was_not_cut_off_still_runs_the_tool() -> None:
    """Same shape, but the model ended the turn on `tool_use`: the empty object is the arguments it meant."""
    plugin = RecordingPlugin()
    await _invoke_anthropic_stream(plugin, _anthropic_streaming_service("tool_use"))

    assert plugin.calls == ["set_mode(mode='default')"]
