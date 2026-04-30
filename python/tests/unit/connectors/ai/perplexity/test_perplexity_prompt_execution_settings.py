# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.perplexity import (
    PerplexityChatPromptExecutionSettings,
)


class TestPerplexityChatPromptExecutionSettings:
    def test_defaults(self):
        s = PerplexityChatPromptExecutionSettings()
        assert s.stream is False
        assert s.temperature is None
        assert s.search_recency_filter is None

    def test_serialization_aliases_model_field(self):
        """ai_model_id is serialized as 'model' so it maps to OpenAI-shaped requests."""
        s = PerplexityChatPromptExecutionSettings(ai_model_id="sonar-pro")
        dumped = s.prepare_settings_dict()
        assert dumped.get("model") == "sonar-pro"
        assert "ai_model_id" not in dumped

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            PerplexityChatPromptExecutionSettings(temperature=3.0)

    def test_search_recency_filter_enum(self):
        s = PerplexityChatPromptExecutionSettings(search_recency_filter="week")
        assert s.search_recency_filter == "week"
        with pytest.raises(ValidationError):
            PerplexityChatPromptExecutionSettings(search_recency_filter="century")
