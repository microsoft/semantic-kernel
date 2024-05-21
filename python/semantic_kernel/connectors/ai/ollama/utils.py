# Copyright (c) Microsoft. All rights reserved.

import aiohttp


class AsyncSession:
    def __init__(self, session: aiohttp.ClientSession = None):
        self._session = session if session else aiohttp.ClientSession()

    async def __aenter__(self):
        return await self._session.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        await self._session.close()
