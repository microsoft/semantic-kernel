# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import HttpUrl, SecretStr, model_validator

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class

IN_MEMORY_STRING = ":memory:"


@experimental_class
class QdrantSettings(KernelBaseSettings):
    """Qdrant settings currently used by the Qdrant Vector Record Store."""

    env_prefix: ClassVar[str] = "QDRANT_"

    url: HttpUrl | None = None
    api_key: SecretStr | None = None
    host: str | None = None
    port: int | None = None
    grpc_port: int | None = None
    path: str | None = None
    location: str | None = None
    prefer_grpc: bool = False

    @model_validator(mode="before")
    def validate_settings(cls, values):
        """Validate the settings."""
        if "url" not in values and "host" not in values and "path" not in values and "location" not in values:
            values["location"] = IN_MEMORY_STRING
        return values

    def model_dump(self, **kwargs):
        """Dump the model."""
        dump = super().model_dump(**kwargs)
        if "api_key" in dump:
            dump["api_key"] = dump["api_key"].get_secret_value()
        if "url" in dump:
            dump["url"] = str(dump["url"])
        return dump
