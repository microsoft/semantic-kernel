import pytest

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)


def test_chat_message():
    # Test initialization with default values
    message = ChatMessage()
    assert message.role == "assistant"
    assert message.fixed_content is None
    assert message.content is None
    assert message.content_template is None
    assert message.name is None


@pytest.mark.asyncio
async def test_chat_message_rendering(create_kernel):
    # Test initialization with custom values
    kernel = create_kernel
    expected_content = "Hello, world!"
    prompt_config = PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )
    content_template = PromptTemplate(
        "Hello, {{$input}}!", kernel.prompt_template_engine, prompt_config
    )

    message = ChatMessage(
        role="user",
        content_template=content_template,
    )
    context = kernel.create_new_context()
    context.variables["input"] = "world"
    await message.render_message_async(context)
    assert message.role == "user"
    assert message.fixed_content == expected_content
    assert message.content_template == content_template

    # Test content property
    assert message.content == expected_content
