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
        assert settings.format is None
        assert settings.options is None

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = NvidiaPromptExecutionSettings(
            format="json",
            options={"key": "value"},
        )
        assert settings.format == "json"
        assert settings.options == {"key": "value"}

    def test_validation_format_values(self):
        """Test format validation values."""
        # Valid values
        settings = NvidiaPromptExecutionSettings(format="json")
        assert settings.format == "json"


class TestNvidiaChatPromptExecutionSettings:
    """Test cases for NvidiaChatPromptExecutionSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = NvidiaChatPromptExecutionSettings()
        assert settings.messages is None
        assert settings.response_format is None

    def test_response_format_with_pydantic_model(self):
        """Test response_format with Pydantic model."""

        class TestModel(BaseModel):
            name: str
            value: int

        settings = NvidiaChatPromptExecutionSettings(response_format=TestModel)

        assert settings.response_format == TestModel

    def test_response_format_with_dict(self):
        """Test response_format with dictionary."""
        settings = NvidiaChatPromptExecutionSettings(response_format={"type": "json_object"})

        assert settings.response_format == {"type": "json_object"}


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
