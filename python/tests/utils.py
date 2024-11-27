# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
import platform
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


async def retry(
    func: Callable[..., Awaitable[Any]],
    retries: int = 20,
    reset: Callable[..., None] | None = None,
):
    """Retry the function if it raises an exception.

    Args:
        func (function): The function to retry.
        retries (int): Number of retries.
        reset (function): Function to reset the state of any variables used in the function

    """
    logger.info(f"Running {retries} retries with func: {func.__module__}")
    for i in range(retries):
        logger.info(f"   Try {i + 1} for {func.__module__}")
        try:
            if reset:
                reset()
            return await func()
        except Exception as e:
            logger.info(f"   On try {i + 1} got this error: {e}")
            if i == retries - 1:  # Last retry
                raise
            # Binary exponential backoff
            backoff = 2**i
            logger.info(f"   Sleeping for {backoff} seconds before retrying")
            await asyncio.sleep(backoff)
    return None


def is_service_setup_for_testing(env_var_names: list[str], raise_if_not_set: bool = True) -> bool:
    """Check if the environment variables are set and not empty.

    By default, this function raises an exception if the environment variable is not set.
    This is to make sure we throw before starting any tests and we cover all services in our pipeline.

    For local testing, you can set `raise_if_not_set=False` to avoid the exception.

    Args:
        env_var_names (list[str]): Environment variable names.
        raise_if_not_set (bool): Raise exception if the environment variable is not set.
    """

    def does_env_var_exist(env_var_name):
        exist = env_var_name in os.environ and os.environ[env_var_name]
        if not exist and raise_if_not_set:
            raise KeyError(f"Environment variable {env_var_name} is not set.")
        return exist

    return all([does_env_var_exist(name) for name in env_var_names])


def is_test_running_on_supported_platforms(platforms: list[str]) -> bool:
    """Check if the test is running on supported platforms.

    Args:
        platforms (list[str]): List of supported platforms.
    """

    return platform.system() in platforms
