# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import re
from enum import Enum
from typing import Callable, Dict

from semantic_kernel.contents.chat_history import ROOT_KEY_MESSAGE
from semantic_kernel.contents.chat_message_content import ChatMessageContent

logger: logging.Logger = logging.getLogger(__name__)


def _message_to_prompt(context):
    if isinstance(context, ChatMessageContent):
        return str(context.to_prompt(ROOT_KEY_MESSAGE))
    return str(context)


def _message(item):
    start = f"<{ROOT_KEY_MESSAGE}"
    role = item.role
    content = item.content
    if isinstance(role, Enum):
        role = role.value
    start += f' role="{role}"'
    start += ">"
    end = f"</{ROOT_KEY_MESSAGE}>"
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
    print(f"Received args: {args}")
    return list(args)


def _range(*args, **kwargs):
    args = list(args)
    for index, arg in enumerate(args):
        if not isinstance(arg, int):
            try:
                args[index] = int(arg)
            except ValueError:
                args.pop(index)
    if len(args) == 1:
        return list(range(args[0]))
    if len(args) == 2:
        return list(range(args[0], args[1]))
    if len(args) == 3:
        return list(range(args[0], args[1], args[2]))
    return []


def _concat(*args, **kwargs):
    return "".join([str(value) for value in args])


def _or(*args, **kwargs):
    return any(args)


def _add(*args, **kwargs):
    return sum([float(value) for value in args])


def _subtract(*args, **kwargs):
    return float(args[0]) - sum([float(value) for value in args[1:]])


def _equals(*args, **kwargs):
    return args[0] == args[1]


def _less_than(*args, **kwargs):
    return float(args[0]) < float(args[1])


def _greater_than(*args, **kwargs):
    return float(args[0]) > float(args[1])


def _less_than_or_equal(*args, **kwargs):
    return float(args[0]) <= float(args[1])


def _greater_than_or_equal(*args, **kwargs):
    return float(args[0]) >= float(args[1])


def _json(*args, **kwargs):
    if not args:
        return ""
    return json.dumps(args[0])


def _camel_case(*args, **kwargs):
    return "".join([word.capitalize() for word in args[0].split("_")])


def _snake_case(*args, **kwargs):
    arg = args[0]
    arg = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", arg)
    arg = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", arg)
    arg = arg.replace("-", "_")
    return arg.lower()


JINJA2_SYSTEM_HELPERS: Dict[str, Callable] = {
    "get": _safe_get_wrapper,
    "double_open": _double_open,
    "doubleOpen": _double_open,
    "double_close": _double_close,
    "doubleClose": _double_close,
    "message": _message,
    "message_to_prompt": _message_to_prompt,
    "messageToPrompt": _message_to_prompt,
    "array": _array,
    "range": _range,
    "concat": _concat,
    "or": _or,
    "add": _add,
    "subtract": _subtract,
    "equals": _equals,
    "less_than": _less_than,
    "lessThan": _less_than,
    "greater_than": _greater_than,
    "greaterThan": _greater_than,
    "less_than_or_equal": _less_than_or_equal,
    "lessThanOrEqual": _less_than_or_equal,
    "greater_than_or_equal": _greater_than_or_equal,
    "greaterThanOrEqual": _greater_than_or_equal,
    "json": _json,
    "camel_case": _camel_case,
    "camelCase": _camel_case,
    "snake_case": _snake_case,
    "snakeCase": _snake_case,
}
