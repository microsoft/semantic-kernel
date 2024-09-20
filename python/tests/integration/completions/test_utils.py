# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


async def retry(func, retries=20):
    min_delay = 2
    max_delay = 7
    for i in range(retries):
        try:
            return await func()
        except Exception as e:
            logger.error(f"Retry {i + 1}: {e}")
            if i == retries - 1:  # Last retry
                raise
            await asyncio.sleep(max(min(i, max_delay), min_delay))
    return None
