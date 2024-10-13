# Copyright (c) Microsoft. All rights reserved.
import json
import logging
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
from typing import Annotated, Any, Final

from pydantic import Field

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
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
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_COLLECTION: Final[str] = "generic"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
COLLECTION_PARAM: Final[str] = "collection"
DEFAULT_RELEVANCE: Final[float] = 0.75
RELEVANCE_PARAM: Final[str] = "relevance"
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
COLLECTION_PARAM: Final[str] = "collection"
DEFAULT_RELEVANCE: Final[float] = 0.75
RELEVANCE_PARAM: Final[str] = "relevance"
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< main
COLLECTION_PARAM: Final[str] = "collection"
DEFAULT_RELEVANCE: Final[float] = 0.75
RELEVANCE_PARAM: Final[str] = "relevance"
=======
DEFAULT_RELEVANCE: Final[float] = 0.75
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
DEFAULT_LIMIT: Final[int] = 1


class TextMemoryPlugin(KernelBaseModel):
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
    """A plugin to interact with a Semantic Text Memory."""

    memory: SemanticTextMemoryBase
    embeddings_kwargs: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self, memory: SemanticTextMemoryBase, embeddings_kwargs: dict[str, Any] = {}
    ) -> None:
        """Initialize a new instance of the TextMemoryPlugin.

        Args:
            memory (SemanticTextMemoryBase): the underlying Semantic Text Memory to use
            embeddings_kwargs (Optional[Dict[str, Any]]): the keyword arguments to pass to the embedding generator
        """
        super().__init__(memory=memory, embeddings_kwargs=embeddings_kwargs)

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
    @kernel_function(
        description="Recall a fact from the long term memory",
        name="recall",
    )
    async def recall(
        self,
        ask: Annotated[str, "The information to retrieve"],
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
        collection: Annotated[
            str, "The collection to search for information."
        ] = DEFAULT_COLLECTION,
        relevance: Annotated[
            float, "The relevance score, from 0.0 to 1.0; 1.0 means perfect match"
        ] = DEFAULT_RELEVANCE,
        limit: Annotated[
            int, "The maximum number of relevant memories to recall."
        ] = DEFAULT_LIMIT,
    ) -> str:
        """Recall a fact from the long term memory.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        kernel: Annotated["Kernel", "The kernel"],
        collection: Annotated[Optional[str], "The collection to search for information."] = DEFAULT_COLLECTION,
        relevance: Annotated[
            Optional[float], "The relevance score, from 0.0 to 1.0; 1.0 means perfect match"
        ] = DEFAULT_RELEVANCE,
        limit: Annotated[Optional[int], "The maximum number of relevant memories to recall."] = DEFAULT_LIMIT,
    ) -> str:
        """
        Recall a fact from the long term memory.
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75

        Example:
            {{memory.recall $ask}} => "Paris"

        Args:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
            ask: The question to ask the memory
            collection: The collection to search for information
            relevance: The relevance score, from 0.0 to 1.0; 1.0 means perfect match
            limit: The maximum number of relevant memories to recall
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            ask -- The question to ask the memory
            collection -- The collection to search for information
            relevance -- The relevance score, from 0.0 to 1.0; 1.0 means perfect match
            limit -- The maximum number of relevant memories to recall
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75

        Returns:
            The nearest item from the memory store as a string or empty string if not found.
        """
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        results = await self.memory.search(
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        results = await self.memory.search(
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< main
        results = await self.memory.search(
=======
        if kernel.memory is None:
            raise ValueError("The context doesn't have a memory instance to search")

        results = await kernel.memory.search(
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
            collection=collection,
            query=ask,
            limit=limit,
            min_relevance_score=relevance,
        )
        if results is None or len(results) == 0:
            logger.warning(f"Memory not found in collection: {collection}")
            return ""

        return results[0].text if limit == 1 else json.dumps([r.text for r in results])  # type: ignore

    @kernel_function(
        description="Save information to semantic memory",
        name="save",
    )
    async def save(
        self,
        text: Annotated[str, "The information to save."],
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
        key: Annotated[str, "The unique key to associate with the information."],
        collection: Annotated[
            str, "The collection to save the information."
        ] = DEFAULT_COLLECTION,
    ) -> None:
        """Save a fact to the long term memory.

        Args:
            text: The text to save to the memory
            kernel: The kernel instance, that has a memory store
            collection: The collection to save the information
            key: The unique key to associate with the information

        """
        await self.memory.save_information(
            collection=collection,
            text=text,
            id=key,
            embeddings_kwargs=self.embeddings_kwargs,
        )
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
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
>>>>>>> ms/small_fixes
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
