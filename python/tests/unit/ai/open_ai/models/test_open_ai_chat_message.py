from openai.util import convert_to_openai_object

from semantic_kernel.connectors.ai.open_ai.models.open_ai_chat_message import (
    OpenAIChatMessage,
)
from semantic_kernel.models.chat.chat_message import ChatMessage


def test_from_openai_object():
    # Create a mock OpenAIObject to use as input
    openai_object = convert_to_openai_object(
        resp={"role": "assistant", "content": "user input"}
    )

    # Call the method being tested
    result = OpenAIChatMessage.from_openai_object(openai_object)

    # Check that the output is of the correct type
    assert isinstance(result, ChatMessage)

    # Check that the output has the correct values
    assert result.role == "assistant"
    assert result.content == "user input"
    assert result.fixed_content == "user input"
    assert result.name is None
