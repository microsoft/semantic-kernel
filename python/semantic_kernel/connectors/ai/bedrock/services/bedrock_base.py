# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import Any, ClassVar

import boto3

from semantic_kernel.kernel_pydantic import KernelBaseModel


class BedrockBase(KernelBaseModel, ABC):
    """Amazon Bedrock Service Base Class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "bedrock"

    # Amazon Bedrock Clients
    # Runtime Client: Use for inference
    bedrock_runtime_client: Any
    # Client: Use for model management
    bedrock_client: Any

    def __init__(
        self,
        *,
        runtime_client: Any | None = None,
        client: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Amazon Bedrock Base Class.

        Args:
            runtime_client: The Amazon Bedrock runtime client to use.
            client: The Amazon Bedrock client to use.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            bedrock_runtime_client=runtime_client or boto3.client("bedrock-runtime"),
            bedrock_client=client or boto3.client("bedrock"),
            **kwargs,
        )
