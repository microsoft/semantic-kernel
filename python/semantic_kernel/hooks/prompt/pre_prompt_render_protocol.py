# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from semantic_kernel.hooks.prompt import PrePromptRenderContext


@runtime_checkable
class PrePromptRenderProtocol(Protocol):
    """PrePromptRenderProtocol."""

    def pre_prompt_render(self, context: "PrePromptRenderContext") -> None:
        """pre_prompt_render."""
