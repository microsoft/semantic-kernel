# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class GoogleSearchResult(KernelBaseModel):
    """A Google web page."""

    kind: str = ""
    title: str = ""
    html_title: str = Field(default="", alias="htmlTitle")
    link: str = ""
    display_link: str = Field(default="", alias="displayLink")
    snippet: str = ""
    html_snippet: str = Field(default="", alias="htmlSnippet")
    cache_id: str = Field(default="", alias="cacheId")
    formatted_url: str = Field(default="", alias="formattedUrl")
    html_formatted_url: str = Field(default="", alias="htmlFormattedUrl")
    pagemap: dict[str, Any] = Field(default_factory=dict)
    mime: str = ""
    file_format: str = Field(default="", alias="fileFormat")
    image: dict[str, Any] = Field(default_factory=dict)
    labels: list[dict[str, Any]] = Field(default_factory=list)
