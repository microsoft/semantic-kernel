# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BingWebPages(KernelBaseModel):
    """The web pages from a Bing search."""

    id: str | None = None
    some_results_removed: bool | None = Field(None, alias="someResultsRemoved")
    total_estimated_matches: int | None = Field(None, alias="totalEstimatedMatches")
    web_search_url: str | None = Field(None, alias="webSearchUrl")
    value: list[BingWebPage] = Field(default_factory=list)


@experimental_class
class BingSearchResponse(KernelBaseModel):
    """The response from a Bing search."""

    type_: str = Field("", alias="_type")
    query_context: dict[str, Any] = Field(default_factory=dict, validation_alias="queryContext")
    web_pages: BingWebPages | None = Field(None, alias="webPages")
