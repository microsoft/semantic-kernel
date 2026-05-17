# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.perplexity import (
    PerplexityChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


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

    def test_serialization_aliases_number_of_responses_field(self):
        """number_of_responses is serialized as 'n' so it maps to OpenAI-shaped requests."""
        s = PerplexityChatPromptExecutionSettings(number_of_responses=2)
        dumped = s.prepare_settings_dict()
        assert dumped.get("n") == 2
        assert "number_of_responses" not in dumped

    def test_number_of_responses_from_generic_prompt_execution_settings(self):
        settings = PromptExecutionSettings(
            extension_data={
                "number_of_responses": 2,
            },
        )
        chat_settings = PerplexityChatPromptExecutionSettings.from_prompt_execution_settings(settings)
        dumped = chat_settings.prepare_settings_dict()
        assert chat_settings.number_of_responses == 2
        assert dumped.get("n") == 2

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            PerplexityChatPromptExecutionSettings(temperature=3.0)

    def test_search_recency_filter_enum(self):
        s = PerplexityChatPromptExecutionSettings(search_recency_filter="week")
        assert s.search_recency_filter == "week"
        with pytest.raises(ValidationError):
            PerplexityChatPromptExecutionSettings(search_recency_filter="century")
