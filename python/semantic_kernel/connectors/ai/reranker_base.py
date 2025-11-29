# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class RerankResult:
    """Represents a single reranking result."""

    def __init__(self, index: int, text: str, relevance_score: float):
        """Initialize a rerank result.

        Args:
            index: The index of the document in the original list.
            text: The document text.
            relevance_score: The relevance score assigned by the reranker.
        """
        self.index = index
        self.text = text
        self.relevance_score = relevance_score

    def __repr__(self) -> str:
        """Return a string representation of the rerank result."""
        return f"RerankResult(index={self.index}, relevance_score={self.relevance_score}, text={self.text[:50]}...)"


@experimental
class RerankingServiceBase(AIServiceClientBase, ABC):
    """Base class for reranking services."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> list[RerankResult]:
        """Rerank documents based on their relevance to a query.

        Args:
            query (str): The query to rank documents against.
            documents (List[str]): The list of documents to rerank.
            settings (PromptExecutionSettings): The settings to use for the request, optional.
            kwargs (Any): Additional arguments to pass to the request.

        Returns:
            List[RerankResult]: List of reranked documents with relevance scores,
                              sorted by relevance (highest first).
        """
        pass
