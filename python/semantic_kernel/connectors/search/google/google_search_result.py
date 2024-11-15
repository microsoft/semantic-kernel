# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class GoogleSearchResult(KernelBaseModel):
    """A Google web page."""

    kind: str = ""
    title: str = ""
    html_title: str = Field("", alias="htmlTitle")
    link: str = ""
    display_link: str = Field("", alias="displayLink")
    snippet: str = ""
    html_snippet: str = Field("", alias="htmlSnippet")
    cache_id: str = Field("", alias="cacheId")
    formatted_url: str = Field("", alias="formattedUrl")
    html_formatted_url: str = Field("", alias="htmlFormattedUrl")
    pagemap: dict[str, Any] = Field(default_factory=dict)
    mime: str = ""
    file_format: str = Field("", alias="fileFormat")
    image: dict[str, Any] = Field(default_factory=dict)
    labels: list[dict[str, Any]] = Field(default_factory=list)
