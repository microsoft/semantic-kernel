# Copyright (c) Microsoft. All rights reserved.

import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict

from semantic_kernel.connectors.ai.open_ai.const import USER_AGENT

TELEMETRY_DISABLED_ENV_VAR = "AZURE_TELEMETRY_DISABLED"

IS_TELEMETRY_ENABLED = os.environ.get(TELEMETRY_DISABLED_ENV_VAR, "false").lower() not in ["true", "1"]

HTTP_USER_AGENT = "Semantic-Kernel"

try:
    version_info = version("semantic-kernel")
except PackageNotFoundError:
    version_info = "dev"

APP_INFO = (
    {
        "Semantic-Kernel-Version": f"python-{version_info}",
    }
    if IS_TELEMETRY_ENABLED
    else None
)


def prepend_semantic_kernel_to_user_agent(headers: Dict[str, Any]):
    """
    Prepend "Semantic-Kernel" to the User-Agent in the headers.

    Args:
        headers: The existing headers dictionary.

    Returns:
        The modified headers dictionary with "Semantic-Kernel" prepended to the User-Agent.
    """

    headers[USER_AGENT] = f"{HTTP_USER_AGENT} {headers[USER_AGENT]}" if USER_AGENT in headers else f"{HTTP_USER_AGENT}"

    return headers
