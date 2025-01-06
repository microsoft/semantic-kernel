# Copyright (c) Microsoft. All rights reserved.
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings, ONNXTemplate
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, ImageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidExecutionSettingsError
from semantic_kernel.kernel import Kernel
from tests.unit.connectors.ai.onnx.conftest import gen_ai_config, gen_ai_config_vision


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_env_variable(gen_ai_config, model, tokenizer, onnx_unit_test_env):
    service = OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3, env_file_path="test.env")
    assert not service.enable_multi_modality


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config_vision))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_vision_valid_env_variable(
    gen_ai_vision_config, model, tokenizer, onnx_unit_test_env
):
    service = OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3, env_file_path="test.env")
    assert service.enable_multi_modality


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_parameter(gen_ai_config, model, tokenizer):
    assert OnnxGenAIChatCompletion(ai_model_path="/valid_path", template=ONNXTemplate.PHI3)


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_str_template(gen_ai_config, model, tokenizer):
    assert OnnxGenAIChatCompletion(ai_model_path="/valid_path", template="phi3")


def test_onnx_chat_completion_with_invalid_model():
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(
            ai_model_path="/invalid_path",
            template=ONNXTemplate.PHI3,
        )


def test_onnx_chat_completion_without_prompt_template():
    with pytest.raises(TypeError):
        OnnxGenAIChatCompletion()


def test_onnx_chat_completion_with_invalid_env_variable(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(
            template=ONNXTemplate.PHI3,
        )


@pytest.mark.parametrize("exclude_list", [["ONNX_GEN_AI_CHAT_MODEL_FOLDER"]], indirect=True)
def test_onnx_chat_completion_with_missing_ai_path(onnx_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3, env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
async def test_onnx_chat_completion(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [["H"], ["e"], ["l"], ["l"], ["o"]]

    chat_completion = OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3, ai_model_path="test")

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")

    with patch.object(chat_completion, "_generate_next_token_async", return_value=generator_mock):
        completed_text: ChatMessageContent = await chat_completion.get_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        )

    assert str(completed_text) == "Hello"


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
async def test_onnx_chat_completion_streaming(gen_ai_config, model, tokenizer):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [["H"], ["e"], ["l"], ["l"], ["o"]]

    chat_completion = OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3, ai_model_path="test")

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")

    completed_text: str = ""

    with patch.object(chat_completion, "_generate_next_token_async", return_value=generator_mock):
        async for chunk in chat_completion.get_streaming_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        ):
            completed_text += str(chunk)

    assert completed_text == "Hello"


@patch("onnxruntime_genai.Model")
def test_onnx_chat_get_image_history(model):
    builtin_open = open  # save the unpatched version

    def patch_open(*args, **kwargs):
        if "genai_config.json" in str(args[0]):
            # mocked open for path "genai_config.json"
            return mock_open(read_data=json.dumps(gen_ai_config_vision))(*args, **kwargs)
        # unpatched version for every other path
        return builtin_open(*args, **kwargs)

    with patch("builtins.open", patch_open):
        chat_completion = OnnxGenAIChatCompletion(
            template=ONNXTemplate.PHI3,
            ai_model_path="test",
        )

        image_content = ImageContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../../../../", "assets/sample_image.jpg")
        )

        history = ChatHistory()
        history.add_system_message("test")
        history.add_user_message("test")
        history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[image_content],
            ),
        )

        last_image = chat_completion._get_images_from_history(history)
        assert last_image == image_content


@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
async def test_onnx_chat_get_image_history_with_not_multimodal(model, tokenizer):
    builtin_open = open  # save the unpatched version

    def patch_open(*args, **kwargs):
        if "genai_config.json" in str(args[0]):
            # mocked open for path "genai_config.json"
            return mock_open(read_data=json.dumps(gen_ai_config))(*args, **kwargs)
        # unpatched version for every other path
        return builtin_open(*args, **kwargs)

    with patch("builtins.open", patch_open):
        chat_completion = OnnxGenAIChatCompletion(
            template=ONNXTemplate.PHI3,
            ai_model_path="test",
        )

        image_content = ImageContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../../../../", "assets/sample_image.jpg")
        )

        history = ChatHistory()
        history.add_system_message("test")
        history.add_user_message("test")
        history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[image_content],
            ),
        )

        with pytest.raises(ServiceInvalidExecutionSettingsError):
            _ = await chat_completion._get_images_from_history(history)
