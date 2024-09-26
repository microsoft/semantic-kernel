# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.onnx.utils import gemma_template, llama_template, phi3_template, phi3v_template
from semantic_kernel.contents import AuthorRole, ChatHistory, ImageContent, TextContent


def test_phi3v_template_with_text_and_image():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.SYSTEM, "content": "System message"},
            {
                "role": AuthorRole.USER,
                "items": [TextContent(text="User text message"), ImageContent(url="http://example.com/image.png")],
            },
            {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
        ]
    )

    expected_output = (
        "<|system|>\nSystem message<|end|>\n"
        "<|user|>\nUser text message<|end|>\n"
        "<|image_1|>\n"
        "<|assistant|>\nAssistant message<|end|>\n"
        "<|assistant|>\n"
    )

    assert phi3v_template(history) == expected_output


def test_phi3_template_with_only_text():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "items": [TextContent(text="User text message")]}])

    expected_output = "<|user|>\nUser text message<|end|>\n<|assistant|>\n"

    assert phi3_template(history) == expected_output


def test_gemma_template_with_user_and_assistant_messages():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.USER, "content": "User text message"},
            {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
        ]
    )

    expected_output = (
        "<bos>"
        "<start_of_turn>user\nUser text message<end_of_turn>\n"
        "<start_of_turn>model\nAssistant message<end_of_turn>\n"
        "<start_of_turn>model\n"
    )

    assert gemma_template(history) == expected_output


def test_gemma_template_with_only_user_message():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "content": "User text message"}])

    expected_output = "<bos><start_of_turn>user\nUser text message<end_of_turn>\n<start_of_turn>model\n"

    assert gemma_template(history) == expected_output


def test_llama_template_with_user_and_assistant_messages():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.USER, "content": "User text message"},
            {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
        ]
    )

    expected_output = (
        "<|start_header_id|>user<|end_header_id|>\n\nUser text message<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\nAssistant message<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>"
    )

    assert llama_template(history) == expected_output


def test_llama_template_with_only_user_message():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "content": "User text message"}])

    expected_output = (
        "<|start_header_id|>user<|end_header_id|>\n\nUser text message<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>"
    )

    assert llama_template(history) == expected_output
