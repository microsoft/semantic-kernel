# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from functools import partial
from typing import Any, ClassVar

from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import run_in_executor
from semantic_kernel.kernel_pydantic import KernelBaseModel


class BedrockBase(KernelBaseModel, ABC):
    """Amazon Bedrock Service Base Class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "bedrock"

    # Amazon Bedrock Clients
    # Runtime Client: Use for inference
    bedrock_runtime_client: Any
    # Client: Use for model management
    bedrock_client: Any

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
