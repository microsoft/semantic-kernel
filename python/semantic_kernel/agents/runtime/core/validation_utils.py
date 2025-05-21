# Copyright (c) Microsoft. All rights reserved.

import re

from semantic_kernel.utils.feature_stage_decorator import experimental

_AGENT_TYPE_REGEX = re.compile(r"^[\w\-\.]+\Z")


@experimental
def is_valid_agent_type(value: str) -> bool:
    """Check if the agent type is valid."""
    return bool(_AGENT_TYPE_REGEX.match(value))
