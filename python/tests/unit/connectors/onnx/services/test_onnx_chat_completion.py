# Copyright (c) Microsoft. All rights reserved.
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, ImageContent
from semantic_kernel.exceptions import BlockException, ServiceInitializationError, ServiceInvalidExecutionSettingsError
from semantic_kernel.kernel import Kernel
from tests.unit.connectors.onnx.services.test_utils import (
    broken_jinja_prompt,
    broken_prompt_template,
    gen_ai_config,
    gen_ai_config_vision,
    jinja_template,
    prompt_template,
)


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_valid_env_variable(gen_ai_config, model, tokenizer, onnx_unit_test_env):
    assert OnnxGenAIChatCompletion(prompt_template=prompt_template, env_file_path="test.env")


@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config_vision))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
def test_onnx_chat_completion_with_vision_valid_env_variable(
    gen_ai_vision_config, model, tokenizer, onnx_unit_test_env
):
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


@pytest.mark.parametrize(
    "prompt_templates",
    [
        pytest.param(prompt_template, id="prompt_template_config"),
        pytest.param(jinja_template, id="prompt_template_string"),
    ],
)
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_chat_completion(gen_ai_config, model, tokenizer, prompt_templates):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ["H", "e", "l", "l", "o"]

    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=prompt_templates,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")

    with patch.object(chat_completion, "_generate_next_token", return_value=generator_mock):
        completed_text: ChatMessageContent = await chat_completion.get_chat_message_content(
            prompt="test", chat_history=history, settings=OnnxGenAIPromptExecutionSettings(), kernel=Kernel()
        )

    assert str(completed_text) == "Hello"


@pytest.mark.parametrize(
    "prompt_templates",
    [
        pytest.param(prompt_template, id="prompt_template_config"),
        pytest.param(jinja_template, id="prompt_template_string"),
    ],
)
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_chat_completion_streaming(gen_ai_config, model, tokenizer, prompt_templates):
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = ["H", "e", "l", "l", "o"]

    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=prompt_templates,
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


@pytest.mark.parametrize(
    "broken_prompt_templates",
    [
        pytest.param(broken_prompt_template, id="broken_prompt_template_config"),
        pytest.param(broken_jinja_prompt, id="broken_prompt_template_string"),
    ],
)
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_apply_template_broken_template(gen_ai_config, model, tokenizer, broken_prompt_templates):
    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=broken_prompt_templates,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")
    with pytest.raises(BlockException):
        _ = await chat_completion._apply_chat_template(chat_history=history, kernel=Kernel())


@pytest.mark.parametrize(
    "prompt_templates",
    [
        pytest.param(prompt_template, id="prompt_template_config"),
        pytest.param(jinja_template, id="prompt_template_string"),
    ],
)
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(gen_ai_config))
@patch("onnxruntime_genai.Model")
@patch("onnxruntime_genai.Tokenizer")
@pytest.mark.asyncio
async def test_onnx_apply_chat_template(gen_ai_config, model, tokenizer, prompt_templates):
    chat_completion = OnnxGenAIChatCompletion(
        prompt_template=prompt_templates,
    )

    history = ChatHistory()
    history.add_system_message("test")
    history.add_user_message("test")
    rendered_template = await chat_completion._apply_chat_template(chat_history=history, kernel=Kernel())
    assert "<|system|>\ntest<|end|>" in rendered_template
    assert "<|user|>\ntest<|end|>" in rendered_template


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
            prompt_template=jinja_template,
            ai_model_path="test",
        )

        image_content = ImageContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../../../", "assets/sample_image.jpg")
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


@pytest.mark.asyncio
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
            prompt_template=jinja_template,
            ai_model_path="test",
        )

        image_content = ImageContent.from_image_path(
            image_path=os.path.join(os.path.dirname(__file__), "../../../../", "assets/sample_image.jpg")
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
