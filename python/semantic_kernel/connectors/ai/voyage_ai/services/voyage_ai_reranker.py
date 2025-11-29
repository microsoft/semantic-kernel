# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.connectors.ai.reranker_base import RerankingServiceBase, RerankResult
from semantic_kernel.connectors.ai.voyage_ai.services.voyage_ai_base import VoyageAIBase
from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_prompt_execution_settings import (
    VoyageAIRerankPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceResponseException,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class VoyageAIReranker(VoyageAIBase, RerankingServiceBase):
    """VoyageAI Reranker Service.

    Supports models like:
    - rerank-2.5
    - rerank-2.5-lite
    - rerank-2
    - rerank-2-lite
    - rerank-1
    - rerank-lite-1
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        endpoint: str | None = None,
    ):
        """Initialize VoyageAI reranker service.

        Args:
            ai_model_id: The VoyageAI reranker model ID (required).
            service_id: The service ID (optional).
            api_key: The VoyageAI API key (optional).
            client: A pre-configured VoyageAI client (optional).
            env_file_path: Path to .env file (optional).
            endpoint: VoyageAI API endpoint (optional).
        """
        # Use reranker model from settings if not provided
        if not ai_model_id:
            from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_settings import VoyageAISettings

            settings = VoyageAISettings.create(env_file_path=env_file_path)
            ai_model_id = settings.reranker_model_id

        if not ai_model_id:
            raise ServiceInitializationError(
                "No model ID provided. Set ai_model_id parameter or VOYAGE_AI_RERANKER_MODEL_ID environment variable."
            )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id,
            api_key=api_key,
            client=client,
            env_file_path=env_file_path,
            endpoint=endpoint,
        )

    @override
    async def rerank(
        self,
        query: str,
        documents: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> list[RerankResult]:
        """Rerank documents based on relevance to a query.

        Args:
            query: The query to rank documents against.
            documents: List of documents to rerank (max 1,000 documents).
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments to pass to the request.

        Returns:
            List[RerankResult]: Reranked documents sorted by relevance score (descending).
        """
        if not settings:
            settings = VoyageAIRerankPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)

        try:
            # Call VoyageAI rerank API
            response = await self.aclient.rerank(
                query=query,
                documents=documents,
                model=self.ai_model_id,
                **settings.prepare_settings_dict(),
            )

            # Convert to RerankResult objects
            return [
                RerankResult(
                    index=result.index,
                    text=result.document,
                    relevance_score=result.relevance_score,
                )
                for result in response.results
            ]

        except Exception as e:
            raise ServiceResponseException(f"VoyageAI rerank request failed: {e}") from e

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the prompt execution settings class."""
        return VoyageAIRerankPromptExecutionSettings
