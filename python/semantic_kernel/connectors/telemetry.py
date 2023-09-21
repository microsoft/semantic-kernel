# Copyright (c) Microsoft. All rights reserved.

import os
import pkg_resources

TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(TELEMETRY_DISABLED_ENV_VAR, "false").lower() != "true"

HTTP_USER_AGENT = "Semantic-Kernel"

APP_INFO = {
    "name": HTTP_USER_AGENT if IS_TELEMETRY_ENABLED else "",
    "version": pkg_resources.get_distribution("semantic-kernel").version if IS_TELEMETRY_ENABLED else ""
}
