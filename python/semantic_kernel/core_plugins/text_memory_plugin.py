# Copyright (c) Microsoft. All rights reserved.
import json
import logging
import sys
import typing as t
from typing import Final, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

if t.TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_COLLECTION: Final[str] = "generic"
DEFAULT_RELEVANCE: Final[float] = 0.75
DEFAULT_LIMIT: Final[int] = 1


class TextMemoryPlugin(KernelBaseModel):
    @kernel_function(
        description="Recall a fact from the long term memory",
        name="recall",
    )
    async def recall(
        self,
        ask: Annotated[str, "The information to retrieve"],
        kernel: Annotated["Kernel", "The kernel"],
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
        if kernel.memory is None:
            raise ValueError("The context doesn't have a memory instance to search")

        results = await kernel.memory.search(
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
        kernel: Annotated["Kernel", "The kernel"],
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

        if kernel.memory is None:
            raise ValueError("The context doesn't have a memory instance to search")

        await kernel.memory.save_information(collection, text=text, id=key)
