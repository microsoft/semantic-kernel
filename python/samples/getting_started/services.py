# Copyright (c) Microsoft. All rights reserved.

"""This module defines an enumeration representing different services."""

from enum import Enum


class Service(Enum):
    """Attributes:
    OpenAI (str): Represents the OpenAI service.
    AzureOpenAI (str): Represents the Azure OpenAI service.
    HuggingFace (str): Represents the HuggingFace service.
    """

    OpenAI = "openai"
    AzureOpenAI = "azureopenai"
    HuggingFace = "huggingface"
