# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import re
from collections.abc import Callable
from enum import Enum

logger: logging.Logger = logging.getLogger(__name__)


def _messages(this, options, *args, **kwargs):
    from semantic_kernel.contents.chat_history import ChatHistory

    if not isinstance(this.context["chat_history"], ChatHistory):
        return ""
    return this.context["chat_history"].to_prompt()


def _message_to_prompt(this, *args, **kwargs):
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

    if isinstance(this.context, ChatMessageContent):
        return str(this.context.to_prompt())
    return str(this.context)


def _message(this, options, *args, **kwargs):
    from semantic_kernel.contents.const import CHAT_MESSAGE_CONTENT_TAG

    # everything in kwargs, goes to <ROOT_KEY_MESSAGE kwargs_key="kwargs_value">
    # everything in options, goes in between <ROOT_KEY_MESSAGE>options</ROOT_KEY_MESSAGE>
    start = f"<{CHAT_MESSAGE_CONTENT_TAG}"
    for key, value in kwargs.items():
        if isinstance(value, Enum):
            value = value.value
        if value is not None:
            start += f' {key}="{value}"'
    start += ">"
    end = f"</{CHAT_MESSAGE_CONTENT_TAG}>"
    try:
        content = options["fn"](this)
    except Exception:  # pragma: no cover
        content = ""
    return f"{start}{content}{end}"


def _set(this, *args, **kwargs):
    if "name" in kwargs and "value" in kwargs:
        this.context[kwargs["name"]] = kwargs["value"]
    if len(args) == 2 and isinstance(args[0], str):
        this.context[args[0]] = args[1]
    return ""


def _get(this, *args, **kwargs):
    if len(args) == 0:
        return ""
    return this.context.get(args[0], "")


def _array(this, *args, **kwargs):
    return list(args)


def _range(this, *args, **kwargs):
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


def _concat(this, *args, **kwargs):
    return "".join([str(value) for value in args])


def _or(this, *args, **kwargs):
    return any(args)


def _add(this, *args, **kwargs):
    return sum([float(value) for value in args])


def _subtract(this, *args, **kwargs):
    return float(args[0]) - sum([float(value) for value in args[1:]])


def _equals(this, *args, **kwargs):
    return args[0] == args[1]


def _less_than(this, *args, **kwargs):
    return float(args[0]) < float(args[1])


def _greater_than(this, *args, **kwargs):
    return float(args[0]) > float(args[1])


def _less_than_or_equal(this, *args, **kwargs):
    return float(args[0]) <= float(args[1])


def _greater_than_or_equal(this, *args, **kwargs):
    return float(args[0]) >= float(args[1])


def _json(this, *args, **kwargs):
    if not args:
        return ""
    return json.dumps(args[0])


def _double_open(this, *args, **kwargs):
    return "{{"


def _double_close(this, *args, **kwargs):
    return "}}"


def _camel_case(this, *args, **kwargs):
    return "".join([word.capitalize() for word in args[0].split("_")])


def _snake_case(this, *args, **kwargs):
    arg = args[0]
    arg = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", arg)
    arg = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", arg)
    arg = arg.replace("-", "_")
    return arg.lower()


HANDLEBAR_SYSTEM_HELPERS: dict[str, Callable] = {
    "set": _set,
    "get": _get,
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
    "double_open": _double_open,
    "doubleOpen": _double_open,
    "double_close": _double_close,
    "doubleClose": _double_close,
    "camel_case": _camel_case,
    "camelCase": _camel_case,
    "snake_case": _snake_case,
    "snakeCase": _snake_case,
    "message": _message,
    "message_to_prompt": _message_to_prompt,
    "messageToPrompt": _message_to_prompt,
    "messages": _messages,
}
