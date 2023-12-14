# Copyright (c) Microsoft. All rights reserved.

import os
from importlib.metadata import version

TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(
    TELEMETRY_DISABLED_ENV_VAR, "false"
).lower() not in ["true", "1"]

HTTP_USER_AGENT = "Semantic-Kernel"

APP_INFO = (
    {
        "name": HTTP_USER_AGENT,
        "version": version("semantic-kernel"),
        "url": "",
    }
    if IS_TELEMETRY_ENABLED
    else None
)
