# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

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


def is_service_setup_for_testing(env_var_name: str) -> bool:
    return env_var_name in os.environ and os.environ[env_var_name]
