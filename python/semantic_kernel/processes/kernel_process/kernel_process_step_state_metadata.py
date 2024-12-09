# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Literal

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelProcessStepStateMetadata(KernelBaseModel):
    """Process state used for State Persistence serialization."""

    # According to the C# code:
    #   [JsonPropertyName("id")]          -> Field(alias="id")
    #   [JsonPropertyName("name")]        -> Field(alias="name")
    #   [JsonPropertyName("versionInfo")] -> Field(alias="versionInfo")
    #   [JsonPropertyName("state")]       -> Field(alias="state")

    # Since this is the base class, and in C# it's defined with polymorphic attributes,
    # we assume this base corresponds to the "Step" type in the C# type discriminators.
    # If the base class is used directly, it will be treated as $type = "Step".
    type: Literal["Step"] = Field("Step", alias="$type")
    id: str | None = Field(None, alias="id")
    name: str | None = Field(None, alias="name")
    versionInfo: str | None = Field(None, alias="versionInfo")
    state: Any | None = Field(None, alias="state")
