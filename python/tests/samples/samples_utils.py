# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


async def retry(func, reset=None, max_retries=3, timeout=30):
    """Retry a function a number of times before raising an exception.

    args:
        func: the async function to retry (required)
        reset: a function to reset the state of any variables used in the function (optional)
        max_retries: the number of times to retry the function before raising an exception (optional)
        timeout: the time to wait for the function to complete before timing out (optional)
    """
    attempt = 0
    while attempt < max_retries:
        try:
            if reset:
                reset()
            await asyncio.wait_for(func(), timeout=timeout)
            break
        except asyncio.TimeoutError:
            logger.error(f"Attempt {attempt + 1} for {func.__name__} timed out.")
            attempt += 1
            if attempt == max_retries:
                logger.error(f"All {max_retries} attempts for {func.__name__} failed")
                raise
            await asyncio.sleep(1)
        except Exception as e:
            attempt += 1
            logger.error(f"Attempt {attempt} for {func.__name__} failed: {e}")
            if attempt == max_retries:
                logger.error(f"All {max_retries} attempts for {func.__name__} failed")
                raise e
            await asyncio.sleep(1)
