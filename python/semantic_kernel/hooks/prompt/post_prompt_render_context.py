# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.hooks.prompt.prompt_hook_context_base import PromptHookContextBase


class PostPromptRenderContext(PromptHookContextBase):
    rendered_prompt: str
