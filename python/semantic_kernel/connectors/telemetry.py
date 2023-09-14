# Copyright (c) Microsoft. All rights reserved.

import os


TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

HTTP_USER_AGENT = "Semantic-Kernel"

IS_TELEMETRY_ENABLED = os.environ.get(TELEMETRY_DISABLED_ENV_VAR, "false").lower() != "true"