# Copyright (c) Microsoft. All rights reserved.
import json
import logging
import sys
from typing import ClassVar, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase

logger: logging.Logger = logging.getLogger(__name__)


class TextMemoryPlugin(KernelBaseModel):
    DEFAULT_COLLECTION: ClassVar[str] = "generic"
    COLLECTION_PARAM: ClassVar[str] = "collection"
    DEFAULT_RELEVANCE: ClassVar[float] = 0.75
    RELEVANCE_PARAM: ClassVar[str] = "relevance"
    DEFAULT_LIMIT: ClassVar[int] = 1

    memory: SemanticTextMemoryBase

    def __init__(self, memory: SemanticTextMemoryBase) -> None:
        """
        Initialize a new instance of the TextMemoryPlugin

        Args:
            memory (SemanticTextMemoryBase) - the underlying Semantic Text Memory to use
        """
        super().__init__(memory=memory)

    @kernel_function(
        description="Recall a fact from the long term memory",
        name="recall",
    )
    async def recall(
        self,
        ask: Annotated[str, "The information to retrieve"],
        collection: Annotated[Optional[str], "The collection to search for information."] = DEFAULT_COLLECTION,
        relevance: Annotated[
            Optional[float], "The relevance score, from 0.0 to 1.0; 1.0 means perfect match"
        ] = DEFAULT_RELEVANCE,
        limit: Annotated[Optional[int], "The maximum number of relevant memories to recall."] = DEFAULT_LIMIT,
    ) -> str:
        """
        Recall a fact from the long term memory.

        Example:
            {{memory.recall $ask}} => "Paris"

        Args:
            ask -- The question to ask the memory
            collection -- The collection to search for information
            relevance -- The relevance score, from 0.0 to 1.0; 1.0 means perfect match
            limit -- The maximum number of relevant memories to recall

        Returns:
            The nearest item from the memory store as a string or empty string if not found.
        """
        results = await self.memory.search(
            collection=collection,
            query=ask,
            limit=limit,
            min_relevance_score=relevance,
        )
        if results is None or len(results) == 0:
            logger.warning(f"Memory not found in collection: {collection}")
            return ""

        return results[0].text if limit == 1 else json.dumps([r.text for r in results])

    @kernel_function(
        description="Save information to semantic memory",
        name="save",
    )
    async def save(
        self,
        text: Annotated[str, "The information to save."],
        key: Annotated[str, "The unique key to associate with the information."],
        collection: Annotated[Optional[str], "The collection to save the information."] = DEFAULT_COLLECTION,
    ) -> None:
        """
        Save a fact to the long term memory.

        Args:
            text -- The text to save to the memory
            kernel -- The kernel instance, that has a memory store
            collection -- The collection to save the information
            key -- The unique key to associate with the information

        """

        await self.memory.save_information(collection, text=text, id=key)
