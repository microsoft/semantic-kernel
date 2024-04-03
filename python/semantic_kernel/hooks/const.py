# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum
from typing import Final

from semantic_kernel.hooks.function.post_function_invoke_protocol import PostFunctionInvokeProtocol
from semantic_kernel.hooks.function.pre_function_invoke_protocol import PreFunctionInvokeProtocol
from semantic_kernel.hooks.prompt.post_prompt_render_protocol import PostPromptRenderProtocol
from semantic_kernel.hooks.prompt.pre_prompt_render_protocol import PrePromptRenderProtocol

PRE_FUNCTION_INVOKE_NAME: Final[str] = "pre_function_invoke"
POST_FUNCTION_INVOKE_NAME: Final[str] = "post_function_invoke"
PRE_PROMPT_RENDER_NAME: Final[str] = "pre_prompt_render"
POST_PROMPT_RENDER_NAME: Final[str] = "post_prompt_render"


class HookEnum(str, Enum):
    PRE_FUNCTION_INVOKE = PRE_FUNCTION_INVOKE_NAME
    POST_FUNCTION_INVOKE = POST_FUNCTION_INVOKE_NAME
    PRE_PROMPT_RENDER = PRE_PROMPT_RENDER_NAME
    POST_PROMPT_RENDER = POST_PROMPT_RENDER_NAME


HOOK_PROTOCOLS = {
    PRE_FUNCTION_INVOKE_NAME: PreFunctionInvokeProtocol,
    POST_FUNCTION_INVOKE_NAME: PostFunctionInvokeProtocol,
    PRE_PROMPT_RENDER_NAME: PrePromptRenderProtocol,
    POST_PROMPT_RENDER_NAME: PostPromptRenderProtocol,
}
