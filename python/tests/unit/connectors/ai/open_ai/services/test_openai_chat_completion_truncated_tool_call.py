# Copyright (c) Microsoft. All rights reserved.

import json

import httpx
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


class _Plugin:
    def __init__(self) -> None:
        self.calls: list[str] = []

    @kernel_function(name="set_mode")
    def set_mode(self, mode: str = "default") -> str:
        self.calls.append(mode)
        return "done"


def _service(handler) -> OpenAIChatCompletion:
    client = AsyncOpenAI(
        api_key="sk-" + "a" * 48,
        base_url="http://mock/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    return OpenAIChatCompletion(ai_model_id="gpt-4o-mini", async_client=client)


def _stream_handler(arguments: str, finish_reason: str):
    body = (
        'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_1",'
        '"type":"function","function":{"name":"set_mode","arguments":' + json.dumps(arguments) + "}}]}}]}\n\n"
        'data: {"choices":[{"index":0,"delta":{},"finish_reason":"' + finish_reason + '"}]}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if json.loads(request.content).get("messages", [])[-1]["role"] == "tool":
            done = 'data: {"choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=done.encode())
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body.encode())

    return handler


def _json_handler(arguments: str, finish_reason: str):
    def handler(request: httpx.Request) -> httpx.Response:
        if json.loads(request.content).get("messages", [])[-1]["role"] == "tool":
            message = {"role": "assistant", "content": "ok"}
            choice = {"index": 0, "message": message, "finish_reason": "stop"}
        else:
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function", "function": {"name": "set_mode", "arguments": arguments}}
                ],
            }
            choice = {"index": 0, "message": message, "finish_reason": finish_reason}
        payload = {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4o-mini",
            "choices": [choice],
        }
        return httpx.Response(200, json=payload)

    return handler


async def _run_streaming(service, plugin) -> None:
    kernel = Kernel()
    kernel.add_plugin(plugin, plugin_name="p")
    settings = PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto())
    history = ChatHistory()
    history.add_user_message("do it")
    async for _ in service.get_streaming_chat_message_contents(history, settings, kernel=kernel):
        pass


async def _run_non_streaming(service, plugin) -> None:
    kernel = Kernel()
    kernel.add_plugin(plugin, plugin_name="p")
    settings = PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto())
    history = ChatHistory()
    history.add_user_message("do it")
    await service.get_chat_message_contents(history, settings, kernel=kernel)


async def test_streaming_skips_tool_call_with_no_arguments_when_cut_off():
    plugin = _Plugin()
    await _run_streaming(_service(_stream_handler("", "length")), plugin)
    assert plugin.calls == []


async def test_non_streaming_skips_tool_call_with_no_arguments_when_cut_off():
    plugin = _Plugin()
    await _run_non_streaming(_service(_json_handler("", "length")), plugin)
    assert plugin.calls == []


async def test_streaming_runs_tool_call_with_arguments_when_cut_off_afterwards():
    plugin = _Plugin()
    await _run_streaming(_service(_stream_handler('{"mode": "silent"}', "length")), plugin)
    assert plugin.calls == ["silent"]


async def test_non_streaming_runs_tool_call_with_arguments_when_cut_off_afterwards():
    plugin = _Plugin()
    await _run_non_streaming(_service(_json_handler('{"mode": "silent"}', "length")), plugin)
    assert plugin.calls == ["silent"]


async def test_streaming_runs_tool_call_with_no_arguments_when_not_cut_off():
    plugin = _Plugin()
    await _run_streaming(_service(_stream_handler("", "tool_calls")), plugin)
    assert plugin.calls == ["default"]


async def test_non_streaming_runs_tool_call_with_no_arguments_when_not_cut_off():
    plugin = _Plugin()
    await _run_non_streaming(_service(_json_handler("", "tool_calls")), plugin)
    assert plugin.calls == ["default"]
