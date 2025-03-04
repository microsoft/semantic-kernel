# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from functools import partial
from typing import Any, ClassVar

import boto3

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.async_utils import run_in_executor


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

    async def get_foundation_model_info(self, model_id: str) -> dict[str, Any]:
        """Get the foundation model information."""
        response = await run_in_executor(
            None,
            partial(
                self.bedrock_client.get_foundation_model,
                modelIdentifier=model_id,
            ),
        )

        return response.get("modelDetails")
