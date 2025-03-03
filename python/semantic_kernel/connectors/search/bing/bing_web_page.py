# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BingWebPage(KernelBaseModel):
    """A Bing web page."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    display_url: str | None = None
    snippet: str | None = None
    date_last_crawled: str | None = None
    deep_links: list["BingWebPage"] | None = None
    open_graph_image: list[dict[str, str | int]] | None = None
    search_tags: list[dict[str, str]] | None = None
    language: str | None = None
    is_family_friendly: bool | None = None
    is_navigational: bool | None = None
