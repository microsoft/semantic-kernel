# Copyright (c) Microsoft. All rights reserved.
from enum import Enum

from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, ImageContent, TextContent
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.exceptions import ServiceException, ServiceInvalidRequestError


class ONNXTemplate(str, Enum):
    """ONNXTemplate is an enumeration that represents different ONNX model templates.

    Attributes:
        PHI3 (str): Represents the "phi3" ONNX model template.
        PHI3V (str): Represents the "phi3v" ONNX model template.
        GEMMA (str): Represents the "gemma" ONNX model template.
        LLAMA (str): Represents the "llama" ONNX model template.
        NONE (str):  Can be chosen if no Template should be used.

    """

    PHI3 = "phi3"
    PHI3V = "phi3v"
    PHI4 = "phi4"
    PHI4MM = "phi4mm"
    GEMMA = "gemma"
    LLAMA = "llama"
    NONE = "none"


def apply_template(history: ChatHistory, template: ONNXTemplate) -> str:
    """Apply the specified ONNX template to the given chat history.

    Args:
        history (ChatHistory): The chat history to which the template will be applied.
        template (ONNXTemplate): The ONNX template to apply.

    Returns:
        str: The result of applying the template to the chat history.

    Raises:
        ServiceException: If an error occurs while applying the template.
    """
    template_functions = {
        ONNXTemplate.PHI3: phi3_template,
        ONNXTemplate.PHI4: phi4_template,
        ONNXTemplate.GEMMA: gemma_template,
        ONNXTemplate.LLAMA: llama_template,
        ONNXTemplate.PHI3V: phi3v_template,
        ONNXTemplate.PHI4MM: phi4mm_template,
        ONNXTemplate.NONE: lambda text: text,
    }

    try:
        return template_functions[template](history)
    except Exception as e:
        raise ServiceException(f"An error occurred while applying the template: {template.value}") from e


def phi3_template(history: ChatHistory) -> str:
    """Generates a formatted string from the chat history for use with the phi3 model.

    Args:
        history (ChatHistory): An object containing the chat history with a list of messages.

    Returns:
        str: A formatted string where each message is prefixed with the role and suffixed with an end marker.
    """
    phi3_input = ""
    for message in history.messages:
        phi3_input += f"<|{message.role.value}|>\n{message.content}<|end|>\n"
    phi3_input += "<|assistant|>\n"
    return phi3_input


def phi4_template(history: ChatHistory) -> str:
    """Generates a formatted string from the chat history for use with the phi4 model.

    Args:
        history (ChatHistory): An object containing the chat history with a list of messages.

    Returns:
        str: A formatted string where each message is prefixed with the role and suffixed with an end marker.
    """
    phi4_input = ""
    for message in history.messages:
        phi4_input += f"<|{message.role.value}|>\n{message.content}<|end|>\n"
    phi4_input += "<|assistant|>\n"
    return phi4_input


def phi3v_template(history: ChatHistory) -> str:
    """Generates a formatted string from a given chat history for use with the phi3v model.

    Args:
        history (ChatHistory): An object containing the chat history with messages.

    Returns:
        str: A formatted string representing the chat history, with special tokens indicating
             the role of each message (system, user, assistant) and the type of content (text, image).
    """
    phi3v_input = ""
    image_count = 0
    for message in history.messages:
        if message.role == AuthorRole.SYSTEM:
            phi3v_input += f"<|system|>\n{message.content}<|end|>\n"
        if message.role == AuthorRole.USER:
            user_content, image_count, _ = _multimodal_user_content(message, image_count)
            phi3v_input += f"<|user|>\n{user_content}<|end|>\n"
        if message.role == AuthorRole.ASSISTANT:
            phi3v_input += f"<|assistant|>\n{message.content}<|end|>\n"
    phi3v_input += "<|assistant|>\n"
    return phi3v_input


def phi4mm_template(history: ChatHistory) -> str:
    """Generates a formatted string from a given chat history for use with the phi4mm model.

    Args:
        history (ChatHistory): An object containing the chat history with messages.

    Returns:
        str: A formatted string representing the chat history, with special tokens indicating
             the role of each message (system, user, assistant) and the type of content (text, image).
    """
    phi4mm_input = ""
    image_count = 0
    audio_count = 0
    for message in history.messages:
        if message.role == AuthorRole.SYSTEM:
            phi4mm_input += f"<|system|>\n{message.content}<|end|>\n"
        if message.role == AuthorRole.USER:
            user_content, image_count, audio_count = _multimodal_user_content(
                message, image_count, audio_count, include_audio=True
            )
            phi4mm_input += f"<|user|>\n{user_content}<|end|>\n"
        if message.role == AuthorRole.ASSISTANT:
            phi4mm_input += f"<|assistant|>\n{message.content}<|end|>\n"
    phi4mm_input += "<|assistant|>\n"
    return phi4mm_input


def _multimodal_user_content(
    message: ChatMessageContent,
    image_count: int,
    audio_count: int = 0,
    include_audio: bool = False,
) -> tuple[str, int, int]:
    """Builds the content of a single user turn for the Phi-3-vision and Phi-4-multimodal templates.

    All content of the message goes into one user turn: the image placeholders first, then the audio
    placeholders, each on its own line, then the text. This is the prompt format given in the model
    cards and used by the onnxruntime-genai examples. Placeholders are numbered across the whole chat
    history, starting at 1.

    Args:
        message (ChatMessageContent): The user message.
        image_count (int): The number of images in the chat history before this message.
        audio_count (int): The number of audio clips in the chat history before this message.
        include_audio (bool): Whether to emit audio placeholders.

    Returns:
        tuple[str, int, int]: The user content and the updated image and audio counts.
    """
    image_tags = ""
    audio_tags = ""
    texts: list[str] = []
    for item in message.items:
        if isinstance(item, TextContent):
            texts.append(item.text)
        elif isinstance(item, ImageContent):
            image_count += 1
            image_tags += f"<|image_{image_count}|>\n"
        elif include_audio and isinstance(item, AudioContent):
            audio_count += 1
            audio_tags += f"<|audio_{audio_count}|>\n"
    return image_tags + audio_tags + "\n".join(texts), image_count, audio_count


def gemma_template(history: ChatHistory) -> str:
    """Generates a formatted string for the Gemma model based on the provided chat history.

    Args:
        history (ChatHistory): An object containing the chat history with messages.

    Returns:
        str: A formatted string representing the chat history for the Gemma model.

    Raises:
        ServiceInvalidRequestError: If a system message is encountered in the chat history.
    """
    gemma_input = "<bos>"
    for message in history.messages:
        if message.role == AuthorRole.SYSTEM:
            raise ServiceInvalidRequestError("System messages are not supported in Gemma")
        if message.role == AuthorRole.USER:
            gemma_input += f"<start_of_turn>user\n{message.content}<end_of_turn>\n"
        if message.role == AuthorRole.ASSISTANT:
            gemma_input += f"<start_of_turn>model\n{message.content}<end_of_turn>\n"
    gemma_input += "<start_of_turn>model\n"
    return gemma_input


def llama_template(history: ChatHistory) -> str:
    """Generates a formatted string from a given chat history for use with the LLaMA model.

    Args:
        history (ChatHistory): An object containing the chat history, which includes a list of messages.

    Returns:
        str: A formatted string where each message is wrapped with specific header and end tags,
             and the final string ends with an assistant header tag.
    """
    llama_input = ""
    for message in history.messages:
        llama_input += f"<|start_header_id|>{message.role.value}<|end_header_id|>\n\n{message.content}<|eot_id|>"
    llama_input += "<|start_header_id|>assistant<|end_header_id|>"
    return llama_input
