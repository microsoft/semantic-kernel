# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class BedrockModelProvider(Enum):
    """Amazon Bedrock Model Provider Enum.

    This list contains the providers of all base models available on Amazon Bedrock.
    """

    AI21LABS = "ai21"
    AMAZON = "amazon"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    META = "meta"
    MISTRALAI = "mistral"
    STABILITYAI = "stability"
