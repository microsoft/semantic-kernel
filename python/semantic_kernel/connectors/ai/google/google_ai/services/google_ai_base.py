# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from google.genai import Client, types

from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.telemetry.user_agent import IS_TELEMETRY_ENABLED, SEMANTIC_KERNEL_USER_AGENT


class GoogleAIBase(KernelBaseModel, ABC):
    """Google AI Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "googleai"

    service_settings: GoogleAISettings

    client: Client | None = None

    def _get_http_options(self) -> types.HttpOptionsDict | None:
        """Get the HTTP options for the Google AI client.

        Returns:
            The HTTP options dictionary, or None if telemetry is disabled.
        """
        if not IS_TELEMETRY_ENABLED:
            return None

        return types.HttpOptionsDict(headers={USER_AGENT: SEMANTIC_KERNEL_USER_AGENT})
