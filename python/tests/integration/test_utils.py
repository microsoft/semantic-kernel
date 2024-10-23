# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


async def retry(func, retries=20):
    """Retry the function if it raises an exception."""
    for i in range(retries):
        try:
            return await func()
        except Exception as e:
            logger.error(f"Retry {i + 1}: {e}")
            if i == retries - 1:  # Last retry
                raise
            # Binary exponential backoff
            await asyncio.sleep(2**i)
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
