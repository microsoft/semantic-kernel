# Copyright (c) Microsoft. All rights reserved.

from typing import Any, ClassVar

from pydantic import SecretStr, model_validator

from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class WeaviateSettings(KernelBaseSettings):
    """Weaviate model settings.

    Args:
        url: HttpsUrl | None - Weaviate URL (Env var WEAVIATE_URL)
        api_key: SecretStr | None - Weaviate token (Env var WEAVIATE_API_KEY)
        local_host: str | None - Local Weaviate host, i.e. a Docker instance (Env var WEAVIATE_LOCAL_HOST)
        local_port: int | None - Local Weaviate port (Env var WEAVIATE_LOCAL_PORT)
        local_grpc_port: int | None - Local Weaviate gRPC port (Env var WEAVIATE_LOCAL_GRPC_PORT)
        use_embed: bool - Whether to use the client embedding options
          (Env var WEAVIATE_USE_EMBED)
    """

    env_prefix: ClassVar[str] = "WEAVIATE_"

    # Using a Weaviate Cloud instance (WCD)
    url: HttpsUrl | None = None
    api_key: SecretStr | None = None

    # Using a local Weaviate instance (i.e. Weaviate in a Docker container)
    local_host: str | None = None
    local_port: int | None = None
    local_grpc_port: int | None = None

    # Using the client embedding options
    use_embed: bool = False

    @model_validator(mode="before")
    @classmethod
    def validate_settings(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate Weaviate settings."""
        enabled = sum([
            cls.is_using_weaviate_cloud(data),
            cls.is_using_local_weaviate(data),
            cls.is_using_client_embedding(data),
        ])

        if enabled == 0:
            raise ServiceInvalidExecutionSettingsError(
                "Weaviate settings must specify either a ",
                "Weaviate Cloud instance, a local Weaviate instance, or the client embedding options.",
            )
        if enabled > 1:
            raise ServiceInvalidExecutionSettingsError(
                "Weaviate settings must specify only one of the following: ",
                "Weaviate Cloud instance, a local Weaviate instance, or the client embedding options.",
            )

        return data

    @classmethod
    def is_using_weaviate_cloud(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using a Weaviate Cloud instance.

        `api_key` is not checked here. Clients should report an error if `api_key` is not set during initialization.
        """
        return data.get("url") is not None

    @classmethod
    def is_using_local_weaviate(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using a local Weaviate instance.

        `local_port` and `local_grpc_port` are not checked here.
        Clients should report an error if `local_port` and `local_grpc_port` are not set during initialization.
        """
        return data.get("local_host") is not None

    @classmethod
    def is_using_client_embedding(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using the client embedding options."""
        return data.get("use_embed") is True
