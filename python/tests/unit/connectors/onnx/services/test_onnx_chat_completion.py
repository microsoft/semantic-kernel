# Copyright (c) Microsoft. All rights reserved.
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.exceptions import BlockException, ServiceInitializationError
from semantic_kernel.kernel import Kernel
from tests.unit.connectors.onnx.services.test_utils import (
    broken_prompt_template,
    gen_ai_config,
    jinja_template,
    prompt_template,
)


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_env_variable(gen_ai_config, model, tokenizer, onnx_unit_test_env):
    assert OnnxGenAIChatCompletion(prompt_template=prompt_template, env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_parameter(gen_ai_config, model, tokenizer):
    assert OnnxGenAIChatCompletion(ai_model_path="/valid_path", prompt_template=prompt_template)


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_str_template(gen_ai_config, model, tokenizer):
    assert OnnxGenAIChatCompletion(ai_model_path="/valid_path", prompt_template=jinja_template)


def test_onnx_chat_completion_with_invalid_model():
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(
            ai_model_path="/invalid_path",
            prompt_template=prompt_template,
        )


def test_onnx_chat_completion_without_prompt_template():
    with pytest.raises(TypeError):
        OnnxGenAIChatCompletion()


def test_onnx_chat_completion_with_invalid_env_variable(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(
            prompt_template=prompt_template,
        )


@pytest.mark.parametrize("exclude_list", [["ONNX_GEN_AI_MODEL_PATH"]], indirect=True)
def test_onnx_chat_completion_with_missing_ai_path(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(prompt_template=prompt_template, env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_chat_completion(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ["H", "e", "l", "l", "o"]

    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=prompt_template,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")

    with patch.object(chat_completion, "_generate_next_token", return_value=generator_mock):
        completed_text: ChatMessageContent = await chat_completion.get_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        )

    assert str(completed_text) == "Hello"


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_chat_completion_streaming(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ["H", "e", "l", "l", "o"]

    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=prompt_template,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")

    completed_text: str = ""

    with patch.object(chat_completion, "_generate_next_token", return_value=generator_mock):
        async for chunk in chat_completion.get_streaming_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        ):
            completed_text += str(chunk)

    assert completed_text == "Hello"


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_chat_completion_broken_template(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ["H", "e", "l", "l", "o"]

    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=broken_prompt_template,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")
    with pytest.raises(BlockException):
        _ = await chat_completion.get_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        )
