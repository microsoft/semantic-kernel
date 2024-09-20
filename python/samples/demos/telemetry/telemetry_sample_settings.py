# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class TelemetrySampleSettings(KernelBaseSettings):
    """Settings for the telemetry sample application.

    Optional settings for prefix 'TELEMETRY_SAMPLE_' are:
    - connection_string: str - The connection string for the Application Insights resource.
                This value can be found in the Overview section when examining
                your resource from the Azure portal.
                (Env var TELEMETRY_SAMPLE_CONNECTION_STRING)
    - otlp_endpoint: str - The OTLP endpoint to send telemetry data to.
                Depending on the exporter used, you may find this value in different places.
                (Env var TELEMETRY_SAMPLE_OTLP_ENDPOINT)

    If no connection string or OTLP endpoint is provided, the telemetry data will be
    exported to the console.
    """

    env_prefix: ClassVar[str] = "TELEMETRY_SAMPLE_"

    connection_string: str | None = None
    otlp_endpoint: str | None = None
