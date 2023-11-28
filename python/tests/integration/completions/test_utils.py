# Copyright (c) Microsoft. All rights reserved.

import logging
import os
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


async def retry(func, retries=20):
    min_delay = 2
    max_delay = 7
    for i in range(retries):
        try:
            result = str(await func())
            if "Error" in result:
                raise ValueError(result)
            return result
        except Exception as e:
            logger.error(f"Retry {i + 1}: {e}")
            if i == retries - 1:  # Last retry
                raise
            time.sleep(max(min(i, max_delay), min_delay))


def get_aoai_api_versions():
    """Retrieves a list of Azure OpenAI API versions for text completions

    As Azure OpenAI may change the response content with different API versions,
    it is necessary to test across multiple versions.
    Supported API versions:
        https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#completions
    """
    api_versiosn = os.environ["AzureOpenAI__APIVersions"]
    return api_versiosn.split(",")


def get_aoai_chat_api_versions():
    """Retrieves a list of Azure OpenAI API versions for chat completions

    As Azure OpenAI may change the response content with different API versions,
    it is necessary to test across multiple versions.
    Supported API versions:
        https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#chat-completions
    """
    api_versions = os.environ["AzureOpenAIChat__APIVersions"]
    return api_versions.split(",")
