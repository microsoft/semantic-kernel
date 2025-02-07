# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class CrewAISettings(KernelBaseSettings):
    """The Crew.AI settings.

    Required:
    - endpoint: str - The API endpoint.
    """

    env_prefix: ClassVar[str] = "CREW_AI_"

    endpoint: str
    auth_token: SecretStr | None = None
    polling_interval: float = 1.0


class CrewAIClientSettings(KernelBaseSettings):
    """The Crew.AI client settings.

    Required:
    - endpoint: str - The API endpoint.
    """

    env_prefix: ClassVar[str] = "CREW_AI_CLIENT_"

    endpoint: str
    auth_token: SecretStr | None = None
    polling_interval: float = 1.0
