# Copyright (c) Microsoft. All rights reserved.

"""
Unit tests for OpenAI ResponsesAgent reasoning effort configuration.

These tests verify the reasoning functionality for OpenAI ResponsesAgent,
including priority hierarchies and parameter validation.
"""

from unittest.mock import AsyncMock

import pytest
from openai import AsyncOpenAI

from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.agents.open_ai.responses_agent_thread_actions import ResponsesAgentThreadActions
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException


class TestOpenAIResponsesAgentReasoning:
    """Tests for OpenAI ResponsesAgent reasoning effort configuration."""

    def test_constructor_reasoning_effort_is_stored(self):
        """Test that reasoning effort is stored during construction"""
        client = AsyncMock(spec=AsyncOpenAI)

        agent = OpenAIResponsesAgent(client=client, ai_model_id="gpt-4o", reasoning_effort="high")

        assert agent.reasoning_effort == "high"

    def test_constructor_reasoning_effort_defaults_to_none(self):
        """Test that constructor reasoning effort defaults to None when not specified."""
        # Arrange & Act: Create agent without reasoning effort
        client = AsyncMock(spec=AsyncOpenAI)
        agent = OpenAIResponsesAgent(
            ai_model_id="gpt-4o",
            client=client,
            name="TestAgent",
            # No reasoning_effort specified
        )

        # Assert: Default reasoning effort is None
        assert agent.reasoning_effort is None

    def test_constructor_reasoning_effort_validation(self):
        """Test that invalid reasoning effort values are rejected."""
        client = AsyncMock(spec=AsyncOpenAI)

        # Test valid values don't raise exceptions
        for valid_effort in ["minimal", "low", "medium", "high"]:
            OpenAIResponsesAgent(ai_model_id="o1", client=client, name="TestAgent", reasoning_effort=valid_effort)

        # Test None is also valid
        OpenAIResponsesAgent(ai_model_id="o1", client=client, name="TestAgent", reasoning_effort=None)

        # Test invalid values are rejected
        with pytest.raises(AgentInitializationException, match="Invalid reasoning effort 'invalid'"):
            OpenAIResponsesAgent(ai_model_id="o1", client=client, name="TestAgent", reasoning_effort="invalid")

        with pytest.raises(AgentInitializationException, match="Invalid reasoning effort 'veryhigh'"):
            OpenAIResponsesAgent(ai_model_id="o1", client=client, name="TestAgent", reasoning_effort="veryhigh")

    def test_reasoning_priority_order_constructor_used_as_default(self):
        """Test constructor reasoning effort is used as default."""
        # Arrange: Mock agent with constructor reasoning
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = "low"  # Constructor-level setting

        # Act: Generate options without per-invocation reasoning
        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1")

        # Assert: Constructor default is used
        assert options["reasoning"]["effort"] == "low"

    def test_reasoning_priority_order_per_invocation_overrides_constructor(self):
        """Test per-invocation reasoning overrides constructor default."""
        # Arrange: Mock agent with constructor default
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = "low"  # Constructor setting

        # Act: Override with per-invocation reasoning
        options = ResponsesAgentThreadActions._generate_options(
            agent=agent,
            model="o1",
            reasoning_effort="high",  # Per-invocation override
        )

        # Assert: Per-invocation override wins
        assert options["reasoning"]["effort"] == "high"

    def test_reasoning_priority_order_complete_hierarchy(self):
        """Test complete reasoning priority hierarchy: per-invocation > constructor > model default."""

        # Test 1: Per-invocation has highest priority
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = "low"
        options = ResponsesAgentThreadActions._generate_options(
            agent=agent,
            model="o1",
            reasoning_effort="medium",  # Per-invocation
        )
        assert options["reasoning"]["effort"] == "medium"  # Per-invocation wins

        # Test 2: Constructor has middle priority (no per-invocation)
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = "low"
        options = ResponsesAgentThreadActions._generate_options(
            agent=agent,
            model="o1",
            # No per-invocation reasoning
        )
        assert options["reasoning"]["effort"] == "low"  # Constructor wins

        # Test 3: Model default has lowest priority (no constructor, no per-invocation)
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = None  # No constructor reasoning
        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1")
        assert options["reasoning"]["effort"] == "high"  # Model default for O1

    def test_multi_agent_reasoning_isolation(self):
        """Test multiple agents maintain separate reasoning configurations."""
        client = AsyncMock(spec=AsyncOpenAI)

        # Agent 1 with low reasoning
        low_agent = OpenAIResponsesAgent(ai_model_id="o1", client=client, name="LowAgent", reasoning_effort="low")

        # Agent 2 with high reasoning
        high_agent = OpenAIResponsesAgent(ai_model_id="o1", client=client, name="HighAgent", reasoning_effort="high")

        # Assert: Agents maintain separate defaults
        assert low_agent.reasoning_effort == "low"
        assert high_agent.reasoning_effort == "high"

        # Verify isolation through options generation
        low_options = ResponsesAgentThreadActions._generate_options(agent=low_agent, model="o1")
        high_options = ResponsesAgentThreadActions._generate_options(agent=high_agent, model="o1")

        assert low_options["reasoning"]["effort"] == "low"
        assert high_options["reasoning"]["effort"] == "high"

    def test_o_series_model_gets_automatic_reasoning(self):
        """Test O-series models get automatic reasoning effort."""
        agent = AsyncMock()
        agent.reasoning_effort = None  # No constructor reasoning

        for model in ["o1", "o3-mini", "o4-mini", "o1-preview"]:
            agent.ai_model_id = model
            options = ResponsesAgentThreadActions._generate_options(agent=agent, model=model)

            # O-series models get automatic reasoning
            assert "reasoning" in options
            assert options["reasoning"]["effort"] in ["low", "medium", "high"]

    def test_non_o_series_models_excluded(self):
        """Test that non-O-series models (including o2, o5+) don't get automatic reasoning."""
        agent = AsyncMock()
        agent.reasoning_effort = None  # No constructor reasoning

        # Test models that should NOT get automatic reasoning
        for model in ["gpt-4o", "gpt-3.5", "o2", "o5", "o6", "other-model", "openai-model"]:
            agent.ai_model_id = model
            options = ResponsesAgentThreadActions._generate_options(agent=agent, model=model)

            # These models should not get automatic reasoning
            assert "reasoning" not in options

    def test_invoke_reasoning_effort_validation(self):
        """Test that invalid reasoning effort values are rejected during invoke."""
        # Test that invalid reasoning effort in invoke methods is rejected
        with pytest.raises(Exception):  # Should be AgentInvokeException but we're testing the validation method
            ResponsesAgentThreadActions._validate_reasoning_effort_parameter("invalid")

        # Valid values should not raise exceptions
        ResponsesAgentThreadActions._validate_reasoning_effort_parameter("minimal")
        ResponsesAgentThreadActions._validate_reasoning_effort_parameter("low")
        ResponsesAgentThreadActions._validate_reasoning_effort_parameter("medium")
        ResponsesAgentThreadActions._validate_reasoning_effort_parameter("high")
        ResponsesAgentThreadActions._validate_reasoning_effort_parameter(None)

    def test_non_o_series_model_no_automatic_reasoning(self):
        """Test non-O-series models don't get automatic reasoning."""
        agent = AsyncMock()
        agent.ai_model_id = "gpt-4o"
        agent.reasoning_effort = None  # No constructor reasoning

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="gpt-4o")

        # Non-O-series models don't get automatic reasoning
        assert "reasoning" not in options

    def test_explicit_none_reasoning_disables_automatic_reasoning(self):
        """Test explicitly setting reasoning=None disables automatic reasoning for O-series."""
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = None

        # Explicitly disable reasoning
        options = ResponsesAgentThreadActions._generate_options(
            agent=agent,
            model="o1",
            reasoning_effort=None,  # Explicit None
        )

        # Explicit None should disable automatic reasoning
        assert "reasoning" not in options

    def test_backward_compatibility_agents_without_reasoning_work(self):
        """Test agents without reasoning configuration work unchanged (backward compatibility)."""
        # Agent without any reasoning configuration (legacy)
        agent = AsyncMock()
        agent.ai_model_id = "gpt-4o"
        agent.reasoning_effort = None

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="gpt-4o")

        # Should work without errors, no reasoning applied
        assert "model" in options
        assert options.get("model") == "gpt-4o"
        assert "reasoning" not in options

    @pytest.mark.parametrize(
        "model_id,expected_effort",
        [
            ("o1", "high"),
            ("o3-mini", "high"),
            ("o4-mini", "medium"),
            ("o1-preview", "high"),
        ],
    )
    def test_o_series_model_default_reasoning_levels(self, model_id: str, expected_effort: str):
        """Test different O-series models get appropriate default reasoning levels."""
        agent = AsyncMock()
        agent.ai_model_id = model_id
        agent.reasoning_effort = None  # No constructor reasoning

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model=model_id)

        assert options["reasoning"]["effort"] == expected_effort

    @pytest.mark.parametrize(
        "model_id,should_have_reasoning",
        [
            ("o1", True),
            ("o1-preview", True),
            ("o1-mini", True),
            ("o3", True),
            ("o3-mini", True),
            ("o4", True),
            ("o4-mini", True),
            ("gpt-4o", False),
            ("gpt-3.5", False),
            ("o2", False),  # o2 doesn't exist in O-series
            ("o5", False),  # o5+ don't exist in O-series
            ("o6", False),
            ("other-model", False),
            ("openai-model", False),
        ],
    )
    def test_o_series_detection_accuracy(self, model_id: str, should_have_reasoning: bool):
        """Test accurate O-series model detection (only o1, o3, o4 variants)."""
        agent = AsyncMock()
        agent.ai_model_id = model_id
        agent.reasoning_effort = None

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model=model_id)

        if should_have_reasoning:
            assert "reasoning" in options, f"Model {model_id} should have reasoning"
        else:
            assert "reasoning" not in options, f"Model {model_id} should NOT have reasoning"

    def test_case_insensitive_o_series_detection(self):
        """Test O-series detection works with different cases."""
        agent = AsyncMock()
        agent.ai_model_id = "O1-PREVIEW"
        agent.reasoning_effort = None

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="O1-PREVIEW")

        # Case-insensitive detection should work
        assert options["reasoning"]["effort"] == "high"

    def test_reasoning_object_structure_follows_openai_api(self):
        """Test reasoning parameter is correctly structured for OpenAI API."""
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = "high"

        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1")

        # Verify correct OpenAI API structure
        assert "reasoning" in options
        reasoning = options["reasoning"]
        assert isinstance(reasoning, dict)
        assert "effort" in reasoning
        assert "generate_summary" in reasoning
        assert reasoning["effort"] == "high"
        assert reasoning["generate_summary"] is None

    def test_reasoning_string_to_object_transformation(self):
        """Test that reasoning strings are properly transformed to OpenAI API objects."""
        agent = AsyncMock()
        agent.ai_model_id = "o1"
        agent.reasoning_effort = None

        # Test all reasoning effort levels
        for effort in ["low", "medium", "high"]:
            options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1", reasoning_effort=effort)

            expected_object = {"effort": effort, "generate_summary": None}
            assert options["reasoning"] == expected_object
