# Copyright (c) Microsoft. All rights reserved.

import os
from importlib.metadata import PackageNotFoundError, version

TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(TELEMETRY_DISABLED_ENV_VAR, "false").lower() not in ["true", "1"]

HTTP_USER_AGENT = "Semantic-Kernel"

try:
    version_info = version("semantic-kernel")
except PackageNotFoundError:
    version_info = "dev"

APP_INFO = (
    {
        "UserAgent": HTTP_USER_AGENT,
        "Semantic-Kernel-Version": f"python-{version_info}",
    }
    if IS_TELEMETRY_ENABLED
    else None
)
