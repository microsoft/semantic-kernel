# Copyright (c) Microsoft. All rights reserved.

import logging
import re
from collections.abc import Callable
from enum import Enum

logger: logging.Logger = logging.getLogger(__name__)


def _messages(chat_history):
    from semantic_kernel.contents.chat_history import ChatHistory

    if not isinstance(chat_history, ChatHistory):
        return ""
    return chat_history.to_prompt()


def _message_to_prompt(context):
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

    if isinstance(context, ChatMessageContent):
        return str(context.to_prompt())
    return str(context)


def _message(item):
    from semantic_kernel.contents.const import CHAT_MESSAGE_CONTENT_TAG

    start = f"<{CHAT_MESSAGE_CONTENT_TAG}"
    role = item.role
    content = item.content
    if isinstance(role, Enum):
        role = role.value
    start += f' role="{role}"'
    start += ">"
    end = f"</{CHAT_MESSAGE_CONTENT_TAG}>"
    return f"{start}{content}{end}"


# Wrap the _get function to safely handle calls without arguments
def _safe_get_wrapper(context=None, name=None, default=""):
    if context is None or name is None:
        return default
    return _get(context, name, default)


def _get(context, name, default=""):
    """Retrieves a value from the context, with a default if not found."""
    return context.get(name, default)


def _double_open():
    """Returns the string representing double open braces."""
    return "{{"


def _double_close():
    """Returns the string representing double close braces."""
    return "}}"


def _array(*args, **kwargs):
    return list(args)


def _camel_case(*args, **kwargs):
    return "".join([word.capitalize() for word in args[0].split("_")])


def _snake_case(*args, **kwargs):
    arg = args[0]
    arg = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", arg)
    arg = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", arg)
    arg = arg.replace("-", "_")
    return arg.lower()


JINJA2_SYSTEM_HELPERS: dict[str, Callable] = {
    "get": _safe_get_wrapper,
    "double_open": _double_open,
    "doubleOpen": _double_open,
    "double_close": _double_close,
    "doubleClose": _double_close,
    "message": _message,
    "message_to_prompt": _message_to_prompt,
    "messages": _messages,
    "messageToPrompt": _message_to_prompt,
    "array": _array,
    "camel_case": _camel_case,
    "camelCase": _camel_case,
    "snake_case": _snake_case,
    "snakeCase": _snake_case,
}
