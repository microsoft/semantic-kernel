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
    name: str | None = None,
):
    """Retry the function if it raises an exception.

    Args:
        func (function): The function to retry.
        retries (int): Number of retries.
        reset (function): Function to reset the state of any variables used in the function

    """
    logger.info(f"Running {retries} retries with func: {name or func.__module__}")
    for i in range(retries):
        logger.info(f"   Try {i + 1} for {name or func.__module__}")
        try:
            if reset:
                reset()
            return await func()
        except Exception as e:
            logger.warning(f"   On try {i + 1} got this error: {e}")
            if i == retries - 1:  # Last retry
                raise
            # Binary exponential backoff
            backoff = 2**i
            logger.info(f"   Sleeping for {backoff} seconds before retrying")
            await asyncio.sleep(backoff)
    return None


def is_service_setup_for_testing(env_var_names: list[str], raise_if_not_set: bool | None = None) -> bool:
    """Check if the environment variables are set and not empty.

    Returns True if all the environment variables in the list are set and not empty. Otherwise, returns False.
    This method can also be configured to raise an exception if the environment variables are not set.

    By default, this function does not raise an exception if the environment variables in the list are not set.
    To raise an exception, set the environment variable `INTEGRATION_TEST_SERVICE_SETUP_EXCEPTION` to `true`,
    or set the `raise_if_not_set` parameter to `True`.

    On local testing, not raising an exception is useful to avoid the need to set up all services.
    On CI, the environment variables should be set, and the tests should fail if they are not set.

    Args:
        env_var_names (list[str]): Environment variable names.
        raise_if_not_set (bool | None): Raise an exception if the environment variables are not set.
    """
    if raise_if_not_set is None:
        raise_if_not_set = os.getenv("INTEGRATION_TEST_SERVICE_SETUP_EXCEPTION", "false").lower() == "true"

    def does_env_var_exist(env_var_name):
        exist = os.getenv(env_var_name, False)
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
