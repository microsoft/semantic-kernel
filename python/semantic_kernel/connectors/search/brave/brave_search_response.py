# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.connectors.search.brave.brave_web_page import BraveWebPage
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BraveWebPages(KernelBaseModel):
    """THe web pages from a Brave search."""

    type: str | None = Field(default="webpage")
    family_friendly: bool | None = Field(default=None)
    results: list[BraveWebPage] = Field(default_factory=list)


@experimental
class BraveSearchResponse(KernelBaseModel):
    """The response from a Brave search."""

    type: str = Field(default="search", alias="type")
    query_context: dict[str, Any] = Field(default_factory=dict, validation_alias="query")
    web_pages: BraveWebPages | None = Field(default=None, validation_alias="web")
