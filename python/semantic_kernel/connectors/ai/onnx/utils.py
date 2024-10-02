# Copyright (c) Microsoft. All rights reserved.
from enum import Enum

from semantic_kernel.contents import AuthorRole, ChatHistory, ImageContent, TextContent
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
        ONNXTemplate.GEMMA: gemma_template,
        ONNXTemplate.LLAMA: llama_template,
        ONNXTemplate.PHI3V: phi3v_template,
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


def phi3v_template(history: ChatHistory) -> str:
    """Generates a formatted string from a given chat history for use with the phi3v model.

    Args:
        history (ChatHistory): An object containing the chat history with messages.

    Returns:
        str: A formatted string representing the chat history, with special tokens indicating
             the role of each message (system, user, assistant) and the type of content (text, image).
    """
    phi3v_input = ""
    for message in history.messages:
        if message.role == AuthorRole.SYSTEM:
            phi3v_input += f"<|system|>\n{message.content}<|end|>\n"
        if message.role == AuthorRole.USER:
            for item in message.items:
                if isinstance(item, TextContent):
                    phi3v_input += f"<|user|>\n{item.text}<|end|>\n"
                # Currently only one image is supported in Onnx
                if isinstance(item, ImageContent):
                    phi3v_input += "<|image_1|>\n"
        if message.role == AuthorRole.ASSISTANT:
            phi3v_input += f"<|assistant|>\n{message.content}<|end|>\n"
    phi3v_input += "<|assistant|>\n"
    return phi3v_input


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
