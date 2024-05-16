# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.filters.filter_context_base import FilterContextBase


class PromptRenderContext(FilterContextBase):
    """Context for prompt rendering filters."""

    rendered_prompt: str | None = None
