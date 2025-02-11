# Copyright (c) Microsoft. All rights reserved.
import aiohttp


class AsyncSession:
    """A wrapper around aiohttp.ClientSession that can be used as an async context manager."""

    def __init__(self, session: aiohttp.ClientSession = None):
        """Initializes a new instance of the AsyncSession class."""
        self._session = session if session else aiohttp.ClientSession()

    async def __aenter__(self):
        """Enter the session."""
        return await self._session.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        """Close the session."""
        await self._session.close()
