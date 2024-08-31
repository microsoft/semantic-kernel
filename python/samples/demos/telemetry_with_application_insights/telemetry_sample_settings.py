# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class TelemetrySampleSettings(KernelBaseSettings):
    """Settings for the telemetry sample application.

    Required settings for prefix 'TELEMETRY_SAMPLE_' are:
    - connection_string: str - The connection string for the Application Insights resource.
                This value can be found in the Overview section when examining
                your resource from the Azure portal.
                (Env var TELEMETRY_SAMPLE_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "TELEMETRY_SAMPLE_"

    connection_string: str
