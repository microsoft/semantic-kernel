# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib

from azure.identity.aio import DefaultAzureCredential


class AsyncDefaultAzureCredentialWrapper(DefaultAzureCredential):
    """Wrapper to make sure the async version of the DefaultAzureCredential is closed properly."""

    def __del__(self) -> None:
        """Close the DefaultAzureCredential."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
