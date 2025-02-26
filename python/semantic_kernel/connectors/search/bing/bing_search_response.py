# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BingWebPages(KernelBaseModel):
    """The web pages from a Bing search."""

    id: str | None = None
    some_results_removed: bool | None = Field(default=None, alias="someResultsRemoved")
    total_estimated_matches: int | None = Field(default=None, alias="totalEstimatedMatches")
    web_search_url: str | None = Field(default=None, alias="webSearchUrl")
    value: list[BingWebPage] = Field(default_factory=list)


@experimental
class BingSearchResponse(KernelBaseModel):
    """The response from a Bing search."""

    type_: str = Field(default="", alias="_type")
    query_context: dict[str, Any] = Field(default_factory=dict, validation_alias="queryContext")
    web_pages: BingWebPages | None = Field(default=None, alias="webPages")
