# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import Any, ClassVar

from google.genai import Client

from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, SEMANTIC_KERNEL_USER_AGENT


class GoogleAIBase(KernelBaseModel, ABC):
    """Google AI Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "googleai"

    service_settings: GoogleAISettings

    client: Client | None = None

    def _get_http_options(self) -> dict[str, Any] | None:
        """Get the HTTP options for the Google AI client.

        Returns:
            The HTTP options dictionary, or None if telemetry is disabled.
        """
        # APP_INFO's presence indicates telemetry is enabled.
        if not APP_INFO:
            return

        return {"headers": {USER_AGENT: SEMANTIC_KERNEL_USER_AGENT}}
