# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import Any

import boto3

from semantic_kernel.kernel_pydantic import KernelBaseModel


class BedrockBase(KernelBaseModel, ABC):
    """Amazon Bedrock Service Base Class."""

    MODEL_PROVIDER_NAME: str = "bedrock"

    bedrock_client: Any

    def __init__(
        self,
        client: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Amazon Bedrock Service Base Class.

        Args:
            client: The Amazon Bedrock client to use.
            **kwargs: Additional keyword arguments.
        """
        self.bedrock_client = client or boto3.client("bedrock-runtime")
