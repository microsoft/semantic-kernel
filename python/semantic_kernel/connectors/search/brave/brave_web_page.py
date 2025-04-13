# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BraveWebPage(KernelBaseModel):
    """A Brave web page."""

    type: str | None = None
    title: str | None = None
    url: str | None = None
    thumbnail: dict[str, str | bool] | None = None
    description: str | None = None
    age: str | None = None
    language: str | None = None
    family_friendly: bool | None = None
    extra_snippets: list[str] | None = None
    meta_ur: dict[str, str] | None = None
    source: str | None = None
