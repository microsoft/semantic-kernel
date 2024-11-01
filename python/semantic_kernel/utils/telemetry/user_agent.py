# Copyright (c) Microsoft. All rights reserved.

import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from semantic_kernel.const import USER_AGENT

# Note that if this environment variable does not exist, telemetry is enabled.
TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(TELEMETRY_DISABLED_ENV_VAR, "false").lower() not in ["true", "1"]

HTTP_USER_AGENT = "semantic-kernel-python"

try:
    version_info = version("semantic-kernel")
except PackageNotFoundError:
    version_info = "dev"

APP_INFO = (
    {
        "semantic-kernel-version": f"python/{version_info}",
    }
    if IS_TELEMETRY_ENABLED
    else None
)


SEMANTIC_KERNEL_USER_AGENT = f"{HTTP_USER_AGENT}/{version_info}"


def prepend_semantic_kernel_to_user_agent(headers: dict[str, Any]):
    """Prepend "semantic-kernel" to the User-Agent in the headers.

    Args:
        headers: The existing headers dictionary.

    Returns:
        The modified headers dictionary with "semantic-kernel-python/{version}" prepended to the User-Agent.
    """
    headers[USER_AGENT] = (
        f"{SEMANTIC_KERNEL_USER_AGENT} {headers[USER_AGENT]}" if USER_AGENT in headers else SEMANTIC_KERNEL_USER_AGENT
    )

    return headers
