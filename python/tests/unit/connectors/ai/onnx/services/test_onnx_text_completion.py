# Copyright (c) Microsoft. All rights reserved.
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxGenAIPromptExecutionSettings, OnnxGenAITextCompletion  # noqa: E402
from semantic_kernel.contents import TextContent
from semantic_kernel.exceptions import ServiceInitializationError
from tests.unit.connectors.ai.onnx.conftest import gen_ai_config


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_env_variable(gen_ai_config, model, tokenizer, onnx_unit_test_env):
    assert OnnxGenAITextCompletion(env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_parameter(gen_ai_config, model, tokenizer):
    assert OnnxGenAITextCompletion(ai_model_path="/valid_path")


def test_onnx_chat_completion_with_invalid_model():
    with pytest.raises(ServiceInitializationError):
        OnnxGenAITextCompletion(ai_model_path="/invalid_path")


def test_onnx_chat_completion_with_invalid_env_variable(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAITextCompletion()


@pytest.mark.parametrize("exclude_list", [["ONNX_GEN_AI_TEXT_MODEL_FOLDER"]], indirect=True)
def test_onnx_chat_completion_with_missing_ai_path(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAITextCompletion(env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
async def test_onnx_text_completion(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [["H"], ["e"], ["l"], ["l"], ["o"]]

    text_completion = OnnxGenAITextCompletion(ai_model_path="test")
    with patch.object(text_completion, "_generate_next_token_async", return_value=generator_mock):
        completed_text: TextContent = await text_completion.get_text_content(
            prompt="test", settings=OnnxGenAIPromptExecutionSettings()
        )

    assert completed_text.text == "Hello"


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
async def test_onnx_text_completion_streaming(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [["H"], ["e"], ["l"], ["l"], ["o"]]

    text_completion = OnnxGenAITextCompletion(ai_model_path="test")
    completed_text: str = ""
    with patch.object(text_completion, "_generate_next_token_async", return_value=generator_mock):
        async for chunk in text_completion.get_streaming_text_content(
            prompt="test", settings=OnnxGenAIPromptExecutionSettings()
        ):
            completed_text += chunk.text

    assert completed_text == "Hello"
