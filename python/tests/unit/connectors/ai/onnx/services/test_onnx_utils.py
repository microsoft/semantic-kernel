# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.onnx.utils import (
    gemma_template,
    llama_template,
    phi3_template,
    phi3v_template,
    phi4_template,
    phi4mm_template,
)
from semantic_kernel.contents import AudioContent, AuthorRole, ChatHistory, ImageContent, TextContent

IMAGE_URL = "http://example.com/image.png"
AUDIO_URL = "http://example.com/audio.mp3"


def test_phi3v_template_with_text_and_image():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.SYSTEM, "content": "System message"},
            {
                "role": AuthorRole.USER,
                "items": [TextContent(text="User text message"), ImageContent(url=IMAGE_URL)],
            },
            {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
        ]
    )

    expected_output = (
        "<|system|>\nSystem message<|end|>\n"
        "<|user|>\n<|image_1|>\nUser text message<|end|>\n"
        "<|assistant|>\nAssistant message<|end|>\n"
        "<|assistant|>\n"
    )

    assert phi3v_template(history) == expected_output


def test_phi3v_template_with_image_and_text():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [ImageContent(url=IMAGE_URL), TextContent(text="Describe this image.")],
            },
        ]
    )

    expected_output = "<|user|>\n<|image_1|>\nDescribe this image.<|end|>\n<|assistant|>\n"

    assert phi3v_template(history) == expected_output


def test_phi3v_template_with_multiple_images():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [
                    ImageContent(url=IMAGE_URL),
                    ImageContent(url=IMAGE_URL),
                    TextContent(text="Compare these images."),
                ],
            },
        ]
    )

    expected_output = "<|user|>\n<|image_1|>\n<|image_2|>\nCompare these images.<|end|>\n<|assistant|>\n"

    assert phi3v_template(history) == expected_output


def test_phi3v_template_numbers_images_across_turns():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.USER, "items": [ImageContent(url=IMAGE_URL), TextContent(text="First")]},
            {"role": AuthorRole.ASSISTANT, "content": "Answer"},
            {"role": AuthorRole.USER, "items": [TextContent(text="Second"), ImageContent(url=IMAGE_URL)]},
            {"role": AuthorRole.ASSISTANT, "content": "Answer"},
            {"role": AuthorRole.USER, "items": [TextContent(text="Third")]},
        ]
    )

    expected_output = (
        "<|user|>\n<|image_1|>\nFirst<|end|>\n"
        "<|assistant|>\nAnswer<|end|>\n"
        "<|user|>\n<|image_2|>\nSecond<|end|>\n"
        "<|assistant|>\nAnswer<|end|>\n"
        "<|user|>\nThird<|end|>\n"
        "<|assistant|>\n"
    )

    assert phi3v_template(history) == expected_output


def test_phi3v_template_merges_text_items_into_one_user_turn():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [TextContent(text="Line one"), ImageContent(url=IMAGE_URL), TextContent(text="Line two")],
            },
        ]
    )

    expected_output = "<|user|>\n<|image_1|>\nLine one\nLine two<|end|>\n<|assistant|>\n"

    assert phi3v_template(history) == expected_output


def test_phi4mm_template_with_text_and_image():
    history = ChatHistory(
        messages=[
            {"role": AuthorRole.SYSTEM, "content": "System message"},
            {
                "role": AuthorRole.USER,
                "items": [
                    TextContent(text="User text message"),
                    ImageContent(url=IMAGE_URL),
                    AudioContent(url=AUDIO_URL),
                ],
            },
            {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
        ]
    )

    expected_output = (
        "<|system|>\nSystem message<|end|>\n"
        "<|user|>\n<|image_1|>\n<|audio_1|>\nUser text message<|end|>\n"
        "<|assistant|>\nAssistant message<|end|>\n"
        "<|assistant|>\n"
    )

    assert phi4mm_template(history) == expected_output


def test_phi4mm_template_with_image_and_text():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [ImageContent(url=IMAGE_URL), TextContent(text="Describe this image.")],
            },
        ]
    )

    expected_output = "<|user|>\n<|image_1|>\nDescribe this image.<|end|>\n<|assistant|>\n"

    assert phi4mm_template(history) == expected_output


def test_phi4mm_template_with_multiple_images():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [
                    TextContent(text="Summarize the content of the images."),
                    ImageContent(url=IMAGE_URL),
                    ImageContent(url=IMAGE_URL),
                    ImageContent(url=IMAGE_URL),
                ],
            },
        ]
    )

    expected_output = (
        "<|user|>\n<|image_1|>\n<|image_2|>\n<|image_3|>\nSummarize the content of the images.<|end|>\n<|assistant|>\n"
    )

    assert phi4mm_template(history) == expected_output


def test_phi4mm_template_with_text_and_audio():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [TextContent(text="Transcribe the audio clip into text."), AudioContent(url=AUDIO_URL)],
            },
        ]
    )

    expected_output = "<|user|>\n<|audio_1|>\nTranscribe the audio clip into text.<|end|>\n<|assistant|>\n"

    assert phi4mm_template(history) == expected_output


def test_phi4mm_template_with_audio_only():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "items": [AudioContent(url=AUDIO_URL)]}])

    expected_output = "<|user|>\n<|audio_1|>\n<|end|>\n<|assistant|>\n"

    assert phi4mm_template(history) == expected_output


def test_phi4mm_template_puts_images_before_audio():
    history = ChatHistory(
        messages=[
            {
                "role": AuthorRole.USER,
                "items": [
                    AudioContent(url=AUDIO_URL),
                    ImageContent(url=IMAGE_URL),
                    ImageContent(url=IMAGE_URL),
                ],
            },
        ]
    )

    expected_output = "<|user|>\n<|image_1|>\n<|image_2|>\n<|audio_1|>\n<|end|>\n<|assistant|>\n"

    assert phi4mm_template(history) == expected_output


def test_phi3_template_with_only_text():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "items": [TextContent(text="User text message")]}])

    expected_output = "<|user|>\nUser text message<|end|>\n<|assistant|>\n"

    assert phi3_template(history) == expected_output


def test_phi4_template_with_only_text():
    history = ChatHistory(messages=[{"role": AuthorRole.USER, "items": [TextContent(text="User text message")]}])

    expected_output = "<|user|>\nUser text message<|end|>\n<|assistant|>\n"

    assert phi4_template(history) == expected_output


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
