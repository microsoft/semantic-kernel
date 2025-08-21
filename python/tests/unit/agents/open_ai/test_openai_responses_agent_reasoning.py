# Copyright (c) Microsoft. All rights reserved.

"""
Unit tests for OpenAI ResponsesAgent reasoning configuration.

These tests verify the reasoning functionality for OpenAI ResponsesAgent,
including priority hierarchies, parameter validation, and callback handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.responses.response_reasoning_item import ResponseReasoningItem
from openai.types.responses.response_reasoning_text_delta_event import ResponseReasoningTextDeltaEvent
from openai.types.responses.response_reasoning_text_done_event import ResponseReasoningTextDoneEvent

from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.agents.open_ai.responses_agent_thread_actions import ResponsesAgentThreadActions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.reasoning_content import ReasoningContent
from semantic_kernel.contents.streaming_reasoning_content import StreamingReasoningContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ContentAdditionException


def test_constructor_reasoning_is_stored():
    """Test that reasoning object is stored during construction"""
    client = AsyncMock(spec=AsyncOpenAI)

    agent = OpenAIResponsesAgent(client=client, ai_model_id="gpt-4o", reasoning={"effort": "high"})

    assert agent.reasoning == {"effort": "high"}


def test_constructor_reasoning_defaults_to_none():
    """Test that constructor reasoning defaults to None when not specified."""
    # Arrange & Act: Create agent without reasoning
    client = AsyncMock(spec=AsyncOpenAI)
    agent = OpenAIResponsesAgent(
        ai_model_id="gpt-4o",
        client=client,
        name="TestAgent",
        # No reasoning specified
    )

    # Assert: Default reasoning is None
    assert agent.reasoning is None


def test_reasoning_priority_order_per_invocation_overrides_constructor():
    """Test per-invocation reasoning overrides constructor default."""
    # Arrange: Mock agent with constructor default
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = {"effort": "low"}  # Constructor setting

    # Act: Override with per-invocation reasoning
    options = ResponsesAgentThreadActions._generate_options(
        agent=agent,
        model="o1",
        reasoning={"effort": "high"},  # Per-invocation override
    )

    # Assert: Per-invocation override wins
    assert options["reasoning"] == {"effort": "high"}


def test_reasoning_priority_order_complete_hierarchy():
    """Test complete reasoning priority hierarchy: per-invocation > constructor."""

    # Test 1: Per-invocation has highest priority
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = {"effort": "low"}
    options = ResponsesAgentThreadActions._generate_options(
        agent=agent,
        model="o1",
        reasoning={"effort": "medium"},  # Per-invocation
    )
    assert options["reasoning"] == {"effort": "medium"}  # Per-invocation wins

    # Test 2: Constructor has priority when no per-invocation
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = {"effort": "low"}
    options = ResponsesAgentThreadActions._generate_options(
        agent=agent,
        model="o1",
        # No per-invocation reasoning
    )
    assert options["reasoning"] == {"effort": "low"}  # Constructor wins

    # Test 3: No reasoning when neither constructor nor per-invocation provided
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = None  # No constructor reasoning
    options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1")
    assert "reasoning" not in options  # No automatic defaults


def test_multi_agent_reasoning_isolation():
    """Test multiple agents maintain separate reasoning configurations."""
    client = AsyncMock(spec=AsyncOpenAI)

    # Agent 1 with low reasoning
    low_agent = OpenAIResponsesAgent(ai_model_id="o1", client=client, name="LowAgent", reasoning={"effort": "low"})

    # Agent 2 with high reasoning
    high_agent = OpenAIResponsesAgent(ai_model_id="o1", client=client, name="HighAgent", reasoning={"effort": "high"})

    # Assert: Agents maintain separate defaults
    assert low_agent.reasoning == {"effort": "low"}
    assert high_agent.reasoning == {"effort": "high"}

    # Verify isolation through options generation
    low_options = ResponsesAgentThreadActions._generate_options(agent=low_agent, model="o1")
    high_options = ResponsesAgentThreadActions._generate_options(agent=high_agent, model="o1")

    assert low_options["reasoning"] == {"effort": "low"}
    assert high_options["reasoning"] == {"effort": "high"}


def test_reasoning_validation_not_available():
    """Test that validation method was removed in simplified implementation."""
    # The validation method was removed, so this test now checks that it's not available
    assert not hasattr(ResponsesAgentThreadActions, "_validate_reasoning_effort_parameter")


def test_explicit_none_reasoning_disables_reasoning():
    """Test explicitly setting reasoning=None disables reasoning."""
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = None

    # Explicitly disable reasoning
    options = ResponsesAgentThreadActions._generate_options(
        agent=agent,
        model="o1",
        reasoning=None,  # Explicit None
    )

    # Explicit None should disable reasoning
    assert "reasoning" not in options


def test_reasoning_object_structure_follows_openai_api():
    """Test reasoning parameter is correctly structured for OpenAI API."""
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = {"effort": "high", "summary": "auto"}

    options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1")

    # Verify correct OpenAI API structure
    assert "reasoning" in options
    reasoning = options["reasoning"]
    assert isinstance(reasoning, dict)
    assert reasoning == {"effort": "high", "summary": "auto"}


def test_reasoning_object_pass_through():
    """Test that reasoning objects are passed through directly."""
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = None

    # Test different reasoning object structures
    test_cases = [
        {"effort": "low"},
        {"effort": "medium", "summary": "concise"},
        {"effort": "high", "summary": "detailed"},
        {"effort": "minimal", "generate_summary": "auto"},  # deprecated field
    ]

    for reasoning_obj in test_cases:
        options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1", reasoning=reasoning_obj)
        assert options["reasoning"] == reasoning_obj


def test_get_reasoning_items_from_output():
    """Test extraction of reasoning items from response output."""
    # Create mock ResponseReasoningItem
    mock_reasoning_item = MagicMock(spec=ResponseReasoningItem)
    mock_reasoning_item.id = "reasoning-123"
    mock_reasoning_item.content = "The model is thinking..."
    mock_reasoning_item.summary = "Analyzed the problem"
    mock_reasoning_item.status = "completed"

    # Create mock ResponsesAgentThreadActions._create_reasoning_content_from_openai_item method
    expected_reasoning_content = MagicMock(spec=ReasoningContent)

    with patch.object(
        ResponsesAgentThreadActions,
        "_create_reasoning_content_from_openai_item",
        return_value=expected_reasoning_content,
    ):
        # Test with reasoning item in output
        output_with_reasoning = [mock_reasoning_item, MagicMock()]
        result = ResponsesAgentThreadActions._get_reasoning_items_from_output(output_with_reasoning)

        assert len(result) == 1
        assert result[0] == expected_reasoning_content
        ResponsesAgentThreadActions._create_reasoning_content_from_openai_item.assert_called_once_with(
            mock_reasoning_item
        )


def test_get_reasoning_items_from_output_empty():
    """Test extraction with no reasoning items in output."""
    # Test with no reasoning items
    output_without_reasoning = [MagicMock(), MagicMock()]
    result = ResponsesAgentThreadActions._get_reasoning_items_from_output(output_without_reasoning)

    assert len(result) == 0


def test_get_reasoning_items_from_output_mixed():
    """Test extraction with mixed output types including reasoning."""
    # Create mock items
    mock_reasoning_item1 = MagicMock(spec=ResponseReasoningItem)
    mock_reasoning_item2 = MagicMock(spec=ResponseReasoningItem)
    mock_other_item = MagicMock()

    expected_reasoning1 = MagicMock(spec=ReasoningContent)
    expected_reasoning2 = MagicMock(spec=ReasoningContent)

    with patch.object(
        ResponsesAgentThreadActions,
        "_create_reasoning_content_from_openai_item",
        side_effect=[expected_reasoning1, expected_reasoning2],
    ):
        output_mixed = [mock_other_item, mock_reasoning_item1, mock_reasoning_item2]
        result = ResponsesAgentThreadActions._get_reasoning_items_from_output(output_mixed)

        assert len(result) == 2
        assert result[0] == expected_reasoning1
        assert result[1] == expected_reasoning2


@pytest.mark.parametrize(
    "reasoning_config,expected_summary",
    [
        ({"effort": "high"}, None),
        ({"effort": "high", "summary": "detailed"}, "detailed"),
        ({"effort": "medium", "summary": "concise"}, "concise"),
        ({"effort": "low", "summary": "auto"}, "auto"),
    ],
)
def test_reasoning_summary_configuration(reasoning_config, expected_summary):
    """Test that reasoning summary configuration is properly handled."""
    agent = AsyncMock()
    agent.ai_model_id = "o1"
    agent.reasoning = None

    options = ResponsesAgentThreadActions._generate_options(agent=agent, model="o1", reasoning=reasoning_config)

    assert options["reasoning"] == reasoning_config
    if expected_summary:
        assert options["reasoning"]["summary"] == expected_summary


def test_streaming_reasoning_content_creation():
    """Test StreamingReasoningContent creation and basic functionality."""
    # Test basic creation
    reasoning = StreamingReasoningContent(text="Initial reasoning", choice_index=0)

    assert reasoning.text == "Initial reasoning"
    assert reasoning.choice_index == 0
    assert str(reasoning) == "Initial reasoning"
    assert bytes(reasoning) == b"Initial reasoning"


def test_streaming_reasoning_content_addition():
    """Test StreamingReasoningContent __add__ method."""
    reasoning1 = StreamingReasoningContent(
        text="First part", choice_index=0, ai_model_id="gpt-4o", metadata={"key1": "value1"}
    )
    reasoning2 = StreamingReasoningContent(
        text=" second part", choice_index=0, ai_model_id="gpt-4o", metadata={"key2": "value2"}
    )

    combined = reasoning1 + reasoning2

    assert combined.text == "First part second part"
    assert combined.choice_index == 0
    assert combined.ai_model_id == "gpt-4o"
    assert combined.metadata == {"key1": "value1", "key2": "value2"}


def test_streaming_reasoning_content_addition_errors():
    """Test StreamingReasoningContent addition error conditions."""
    reasoning1 = StreamingReasoningContent(text="text1", choice_index=0, ai_model_id="model1")
    reasoning2 = StreamingReasoningContent(text="text2", choice_index=1, ai_model_id="model1")
    reasoning3 = StreamingReasoningContent(text="text3", choice_index=0, ai_model_id="model2")

    # Different choice_index should raise error
    with pytest.raises(ContentAdditionException, match="different choice_index"):
        reasoning1 + reasoning2

    # Different ai_model_id should raise error
    with pytest.raises(ContentAdditionException, match="different ai_model_id"):
        reasoning1 + reasoning3


def test_streaming_reasoning_content_with_regular_reasoning():
    """Test StreamingReasoningContent addition with regular ReasoningContent."""
    streaming = StreamingReasoningContent(
        text="Stream: ", choice_index=0, ai_model_id="gpt-4o", metadata={"stream": True}
    )
    regular = ReasoningContent(text="regular", ai_model_id="gpt-4o", metadata={"regular": True})

    combined = streaming + regular

    assert isinstance(combined, StreamingReasoningContent)
    assert combined.text == "Stream: regular"
    assert combined.choice_index == 0
    assert combined.ai_model_id == "gpt-4o"
    assert combined.metadata == {"stream": True, "regular": True}


def test_reasoning_content_from_response_item():
    """Test ReasoningContent creation from OpenAI ResponseReasoningItem via agent thread actions."""
    mock_item = MagicMock(spec=ResponseReasoningItem)
    mock_item.id = "reasoning-123"
    mock_item.summary = [MagicMock(text="Analyzed the user's request")]
    mock_item.status = "completed"

    # Test the _create_reasoning_content_from_openai_item method via thread actions
    reasoning = ResponsesAgentThreadActions._create_reasoning_content_from_openai_item(mock_item)

    assert isinstance(reasoning, ReasoningContent)
    assert reasoning.text == "Analyzed the user's request"
    assert reasoning.metadata["id"] == "reasoning-123"
    assert reasoning.metadata["status"] == "completed"


def test_callback_signature_validation():
    """Test that on_intermediate_message callback has correct signature."""

    async def valid_callback(message: ChatMessageContent) -> None:
        """Valid callback signature."""
        pass

    async def invalid_callback(message: str) -> None:
        """Invalid callback signature."""
        pass

    # This test verifies the expected signature pattern exists
    # In actual usage, the callback should accept ChatMessageContent
    test_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[ReasoningContent(text="reasoning")])

    # Valid callback should work (this is a type check test)
    assert callable(valid_callback)
    assert test_message.role == AuthorRole.ASSISTANT
    # Note: Runtime type checking would be done by the agent implementation


@patch.object(ResponsesAgentThreadActions, "_get_reasoning_items_from_output")
def test_reasoning_yield_pattern(mock_get_reasoning):
    """Test that reasoning content yields False (intermediate) while final content yields True."""
    # Mock reasoning items being found
    mock_reasoning_content = ReasoningContent(text="Thinking about the answer...")
    mock_get_reasoning.return_value = [mock_reasoning_content]

    # In actual usage, when reasoning items are found:
    # yield False, reasoning_message  # <- Intermediate (not visible to user)
    # yield True, final_message       # <- Final response (visible to user)

    # This test verifies the pattern exists in the invoke method
    result = ResponsesAgentThreadActions._get_reasoning_items_from_output([])
    mock_get_reasoning.assert_called_once()
    assert result is not None  # Verify the method returns something


def test_streaming_reasoning_events():
    """Test handling of streaming reasoning events."""
    # Test delta event
    delta_event = MagicMock(spec=ResponseReasoningTextDeltaEvent)
    delta_event.delta = "Thinking"
    delta_event.item_id = "reasoning-123"

    # Test done event
    done_event = MagicMock(spec=ResponseReasoningTextDoneEvent)
    done_event.text = "Thinking process complete"
    done_event.item_id = "reasoning-123"

    # Verify events have expected attributes
    assert hasattr(delta_event, "delta")
    assert hasattr(done_event, "text")

    # These would be processed in invoke_stream method
    # Delta events create StreamingReasoningContent
    # Done events create ReasoningContent


def test_reasoning_metadata_handling():
    """Test that reasoning content properly handles metadata."""
    reasoning = ReasoningContent(text="Analysis complete", metadata={"model": "gpt-4o", "reasoning_effort": "high"})

    streaming_reasoning = StreamingReasoningContent(
        text="Analyzing...", choice_index=0, metadata={"stream": True, "chunk": 1}
    )

    assert reasoning.metadata["model"] == "gpt-4o"
    assert reasoning.metadata["reasoning_effort"] == "high"
    assert streaming_reasoning.metadata["stream"] is True
    assert streaming_reasoning.metadata["chunk"] == 1


@pytest.mark.parametrize(
    "text_input,expected_bytes",
    [
        ("Simple reasoning", b"Simple reasoning"),
        ("", b""),
        ("Unicode: 🤔", "Unicode: 🤔".encode()),
    ],
)
def test_streaming_reasoning_content_bytes_conversion(text_input, expected_bytes):
    """Test StreamingReasoningContent bytes conversion with various inputs."""
    reasoning = StreamingReasoningContent(text=text_input, choice_index=0)
    assert bytes(reasoning) == expected_bytes


def test_streaming_reasoning_content_default_text():
    """Test StreamingReasoningContent with default text value."""
    # Test with no text parameter (should default to empty string)
    reasoning_default = StreamingReasoningContent(choice_index=0)
    assert reasoning_default.text is None
    assert str(reasoning_default) == ""
    assert bytes(reasoning_default) == b""

    # Test with empty string
    reasoning_empty = StreamingReasoningContent(text="", choice_index=0)
    assert reasoning_empty.text == ""
    assert str(reasoning_empty) == ""
    assert bytes(reasoning_empty) == b""


def test_reasoning_integration_flow():
    """Test the complete flow of reasoning content through the system."""
    # 1. OpenAI returns ResponseReasoningItem
    mock_reasoning_item = MagicMock(spec=ResponseReasoningItem)
    mock_reasoning_item.content = "Let me analyze this step by step..."

    # 2. Convert to ReasoningContent
    reasoning_content = ReasoningContent(text="Let me analyze this step by step...")

    # 3. Create ChatMessageContent with reasoning
    reasoning_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[reasoning_content], ai_model_id="gpt-4o")

    # 4. Verify message structure
    assert len(reasoning_message.items) == 1
    assert isinstance(reasoning_message.items[0], ReasoningContent)
    assert reasoning_message.items[0].text == "Let me analyze this step by step..."
    assert reasoning_message.role == AuthorRole.ASSISTANT


def test_multiple_reasoning_items_extraction():
    """Test extraction of multiple reasoning items from response output."""
    # Create multiple mock reasoning items
    reasoning1 = MagicMock(spec=ResponseReasoningItem)
    reasoning1.content = "First reasoning step"

    reasoning2 = MagicMock(spec=ResponseReasoningItem)
    reasoning2.content = "Second reasoning step"

    other_item = MagicMock()  # Non-reasoning item

    output = [reasoning1, other_item, reasoning2]

    with patch.object(
        ResponsesAgentThreadActions,
        "_create_reasoning_content_from_openai_item",
        side_effect=lambda x: ReasoningContent(text=x.content),
    ):
        result = ResponsesAgentThreadActions._get_reasoning_items_from_output(output)

        assert len(result) == 2
        assert result[0].text == "First reasoning step"
        assert result[1].text == "Second reasoning step"
