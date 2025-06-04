# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib

from qdrant_client.async_qdrant_client import AsyncQdrantClient


class AsyncQdrantClientWrapper(AsyncQdrantClient):
    """Wrapper to make sure the connection is closed when the object is deleted."""

    def __del__(self) -> None:
        """Async close connection, done when the object is deleted, used when SK creates a client."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
