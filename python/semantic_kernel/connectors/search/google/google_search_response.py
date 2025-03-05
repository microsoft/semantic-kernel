# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.connectors.search.google.google_search_result import GoogleSearchResult
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class GoogleSearchInformation(KernelBaseModel):
    """Information about the search."""

    search_time: float = Field(alias="searchTime")
    formatted_search_time: str = Field(alias="formattedSearchTime")
    total_results: str = Field(alias="totalResults")
    formatted_total_results: str = Field(alias="formattedTotalResults")


@experimental_class
class GoogleSearchResponse(KernelBaseModel):
    """The response from a Google search."""

    kind: str = ""
    url: dict[str, str] = Field(default_factory=dict)
    queries: dict[str, list[dict[str, str | int]]] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    search_information: GoogleSearchInformation | None = None
    spelling: dict[str, Any] = Field(default_factory=dict)
    promotions: list[dict[str, Any]] = Field(default_factory=list)
    items: list[GoogleSearchResult] | None = Field(None)
