# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class CopilotStudioAgentSettings(KernelBaseSettings):
    """Copilot Studio Agent settings currently used by the CopilotStudioAgent."""

    env_prefix: ClassVar[str] = "COPILOT_STUDIO_AGENT_"

    app_client_id: str | None = None
    tenant_id: str | None = None
    environment_id: str | None = None
    agent_identifier: str | None = None
    cloud: str | None = None
    copilot_agent_type: str | None = None
    custom_power_platform_cloud: str | None = None
