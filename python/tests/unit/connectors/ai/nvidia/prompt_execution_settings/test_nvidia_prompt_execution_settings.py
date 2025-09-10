# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import BaseModel, ValidationError

from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaChatPromptExecutionSettings,
    NvidiaEmbeddingPromptExecutionSettings,
    NvidiaPromptExecutionSettings,
)


class TestNvidiaPromptExecutionSettings:
    """Test cases for NvidiaPromptExecutionSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = NvidiaPromptExecutionSettings()
        assert settings.ai_model_id is None
        assert settings.temperature is None
        assert settings.stream is False

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = NvidiaPromptExecutionSettings(
            ai_model_id="test-model",
            temperature=0.7,
            max_tokens=100,
        )
        assert settings.ai_model_id == "test-model"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 100

    def test_validation_temperature_range(self):
        """Test temperature validation range."""
        # Valid values
        settings = NvidiaPromptExecutionSettings(temperature=0.0)
        assert settings.temperature == 0.0

        settings = NvidiaPromptExecutionSettings(temperature=2.0)
        assert settings.temperature == 2.0

        # Invalid values
        with pytest.raises(ValidationError):
            NvidiaPromptExecutionSettings(temperature=-0.1)

        with pytest.raises(ValidationError):
            NvidiaPromptExecutionSettings(temperature=2.1)


class TestNvidiaChatPromptExecutionSettings:
    """Test cases for NvidiaChatPromptExecutionSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = NvidiaChatPromptExecutionSettings()
        assert settings.messages is None
        assert settings.response_format is None
        assert settings.structured_json_response is False

    def test_response_format_with_pydantic_model(self):
        """Test response_format with Pydantic model."""

        class TestModel(BaseModel):
            name: str
            value: int

        settings = NvidiaChatPromptExecutionSettings(response_format=TestModel)

        assert settings.response_format == TestModel
        assert settings.structured_json_response is True

    def test_response_format_with_dict(self):
        """Test response_format with dictionary."""
        settings = NvidiaChatPromptExecutionSettings(response_format={"type": "json_object"})

        assert settings.response_format == {"type": "json_object"}
        assert settings.structured_json_response is False


class TestNvidiaEmbeddingPromptExecutionSettings:
    """Test cases for NvidiaEmbeddingPromptExecutionSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = NvidiaEmbeddingPromptExecutionSettings()
        assert settings.input is None
        assert settings.encoding_format == "float"
        assert settings.input_type == "query"
        assert settings.truncate == "NONE"

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = NvidiaEmbeddingPromptExecutionSettings(
            input=["hello", "world"],
            encoding_format="base64",
            input_type="passage",
            truncate="START",
        )

        assert settings.input == ["hello", "world"]
        assert settings.encoding_format == "base64"
        assert settings.input_type == "passage"
        assert settings.truncate == "START"

    def test_validation_encoding_format(self):
        """Test encoding_format validation."""
        # Valid values
        settings = NvidiaEmbeddingPromptExecutionSettings(encoding_format="float")
        assert settings.encoding_format == "float"

        settings = NvidiaEmbeddingPromptExecutionSettings(encoding_format="base64")
        assert settings.encoding_format == "base64"

        # Invalid values
        with pytest.raises(ValidationError):
            NvidiaEmbeddingPromptExecutionSettings(encoding_format="invalid")
