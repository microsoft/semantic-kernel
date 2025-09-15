# Copyright (c) Microsoft. All rights reserved.

import base64
import hashlib
from collections.abc import Iterable

from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class KeyEncoder:
    """A class for encoding keys."""

    @staticmethod
    def generate_hash(keys: Iterable[str]) -> str:
        """Generate a hash from a list of keys.

        Args:
            keys: A list of keys to generate the hash from.

        Returns:
            str: The generated hash.

        Raises:
            AgentExecutionException: If the keys are empty
        """
        if not keys:
            raise AgentExecutionException("Channel Keys must not be empty. Unable to generate channel hash.")
        joined_keys = ":".join(keys)
        buffer = joined_keys.encode("utf-8")
        sha256_hash = hashlib.sha256(buffer).digest()
        return base64.b64encode(sha256_hash).decode("utf-8")
