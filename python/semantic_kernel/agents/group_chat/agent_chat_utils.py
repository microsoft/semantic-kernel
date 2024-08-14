# Copyright (c) Microsoft. All rights reserved.

import base64
import hashlib

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KeyEncoder:
    """A class for encoding keys."""

    @staticmethod
    def generate_hash(keys):
        """Generate a hash from a list of keys."""
        # Join the keys into a single string with ':' as the separator
        joined_keys = ":".join(keys)

        # Encode the joined string to bytes
        buffer = joined_keys.encode("utf-8")

        # Compute the SHA-256 hash
        sha256_hash = hashlib.sha256(buffer).digest()

        # Convert the hash to a base64-encoded string
        return base64.b64encode(sha256_hash).decode("utf-8")
