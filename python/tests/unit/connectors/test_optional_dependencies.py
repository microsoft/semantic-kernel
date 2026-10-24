# Copyright (c) Microsoft. All rights reserved.

import sys
from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.exceptions import ServiceInitializationError


def test_hugging_face_settings_instantiation_without_transformers():
    """HuggingFacePromptExecutionSettings can be imported and instantiated without transformers installed."""
    from semantic_kernel.connectors.ai.hugging_face import HuggingFacePromptExecutionSettings

    settings = HuggingFacePromptExecutionSettings(
        max_new_tokens=100,
        temperature=0.7,
    )
    assert settings.max_new_tokens == 100
    assert settings.temperature == 0.7


def test_hugging_face_settings_get_generation_config_missing_dependency():
    """Calling get_generation_config without transformers produces an actionable error naming the install extra."""
    from semantic_kernel.connectors.ai.hugging_face import (
        HuggingFacePromptExecutionSettings,
        hf_prompt_execution_settings,
    )

    settings = HuggingFacePromptExecutionSettings()

    with patch.object(hf_prompt_execution_settings, "ready", False):
        with pytest.raises(ImportError) as exc_info:
            settings.get_generation_config()

        err_msg = str(exc_info.value)
        assert "transformers is not installed" in err_msg
        assert "semantic-kernel[hugging_face]" in err_msg


def test_hugging_face_settings_get_generation_config_available():
    """When transformers is available, get_generation_config constructs the GenerationConfig."""
    from semantic_kernel.connectors.ai.hugging_face import (
        HuggingFacePromptExecutionSettings,
        hf_prompt_execution_settings,
    )

    mock_gen_config_cls = MagicMock()
    mock_transformers = MagicMock()
    mock_transformers.GenerationConfig = mock_gen_config_cls

    settings = HuggingFacePromptExecutionSettings(temperature=0.8, top_p=0.9)

    with (
        patch.object(hf_prompt_execution_settings, "ready", True),
        patch.dict(sys.modules, {"transformers": mock_transformers}),
    ):
        config = settings.get_generation_config()
        assert config == mock_gen_config_cls.return_value
        mock_gen_config_cls.assert_called_once()


def test_hugging_face_text_completion_missing_dependency():
    """HuggingFaceTextCompletion raises an actionable ImportError naming semantic-kernel[hugging_face]."""
    from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextCompletion
    from semantic_kernel.connectors.ai.hugging_face.services import hf_text_completion

    with patch.object(hf_text_completion, "ready", False):
        with pytest.raises(ImportError) as exc_info:
            HuggingFaceTextCompletion(ai_model_id="test_model")

        err_msg = str(exc_info.value)
        assert "torch and transformers are not installed" in err_msg
        assert "semantic-kernel[hugging_face]" in err_msg


def test_hugging_face_text_embedding_missing_dependency():
    """HuggingFaceTextEmbedding raises an actionable ImportError naming semantic-kernel[hugging_face]."""
    from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextEmbedding
    from semantic_kernel.connectors.ai.hugging_face.services import hf_text_embedding

    with patch.object(hf_text_embedding, "torch_installed", False):
        with pytest.raises(ImportError) as exc_info:
            HuggingFaceTextEmbedding(ai_model_id="test_model")

        err_msg = str(exc_info.value)
        assert "torch is not installed" in err_msg
        assert "semantic-kernel[hugging_face]" in err_msg


def test_onnx_gen_ai_missing_dependency():
    """OnnxGenAICompletionBase raises an actionable ImportError naming semantic-kernel[onnx]."""
    from semantic_kernel.connectors.ai.onnx.services import onnx_gen_ai_completion_base
    from semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base import (
        OnnxGenAICompletionBase,
    )

    with patch.object(onnx_gen_ai_completion_base, "ready", False):
        with pytest.raises(ImportError) as exc_info:
            OnnxGenAICompletionBase(ai_model_path="dummy_path")

        err_msg = str(exc_info.value)
        assert "onnxruntime-genai is not installed" in err_msg
        assert "semantic-kernel[onnx]" in err_msg


def test_chroma_memory_store_missing_dependency():
    """ChromaMemoryStore raises ServiceInitializationError naming semantic-kernel[chroma]."""
    from semantic_kernel.connectors.memory_stores.chroma.chroma_memory_store import (
        ChromaMemoryStore,
    )

    with patch.dict(sys.modules, {"chromadb": None, "chromadb.config": None}):
        with pytest.raises(ServiceInitializationError) as exc_info:
            ChromaMemoryStore()

        err_msg = str(exc_info.value)
        assert "chromadb" in err_msg
        assert "semantic-kernel[chroma]" in err_msg
