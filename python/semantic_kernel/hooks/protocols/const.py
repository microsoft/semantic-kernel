# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum
from typing import Final

from semantic_kernel.hooks.protocols.post_function_invoke import PostFunctionInvokeProtocol
from semantic_kernel.hooks.protocols.pre_function_invoke import PreFunctionInvokeProtocol

PRE_FUNCTION_INVOKE_NAME: Final[str] = "pre_function_invoke"
POST_FUNCTION_INVOKE_NAME: Final[str] = "post_function_invoke"


class HookEnum(str, Enum):
    PRE_FUNCTION_INVOKE = PRE_FUNCTION_INVOKE_NAME
    POST_FUNCTION_INVOKE = POST_FUNCTION_INVOKE_NAME


HOOK_PROTOCOLS = {
    PRE_FUNCTION_INVOKE_NAME: PreFunctionInvokeProtocol,
    POST_FUNCTION_INVOKE_NAME: PostFunctionInvokeProtocol,
}
