# Copyright (c) Microsoft. All rights reserved.

import os

import pkg_resources

TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(
    TELEMETRY_DISABLED_ENV_VAR, "false"
).lower() not in ["true", "1"]

HTTP_USER_AGENT = "Semantic-Kernel"

APP_INFO = (
    {
        "name": HTTP_USER_AGENT,
        "version": pkg_resources.get_distribution("semantic-kernel").version,
        "url": "",
    }
    if IS_TELEMETRY_ENABLED
    else None
)
