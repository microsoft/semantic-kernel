"""RAG (Retrieval Augmented Generation) example using AWS Bedrock with Semantic Kernel.

This example demonstrates how to:
1. Create a custom memory store using OpenSearch
2. Use AWS Bedrock for embeddings and chat completion
3. Implement the RAG pattern for enhanced LLM responses
4. Handle document storage and retrieval

The example shows how to augment LLM responses with relevant context
from a knowledge base, improving accuracy and relevance of responses.

Requirements:
    - AWS credentials configured
    - Access to AWS Bedrock service
    - OpenSearch instance
    - Required packages: semantic-kernel, boto3, opensearch-py

Example usage:
    python rag_example.py
"""

import logging
import sys
from typing import Optional, List, Tuple

import semantic_kernel as sk
from semantic_kernel.connectors.ai.bedrock import (
    BedrockChatCompletion,
    BedrockTextEmbedding
)
from semantic_kernel.connectors.ai.bedrock.bedrock_config import BedrockConfig
from semantic_kernel.memory import MemoryStore, MemoryRecord
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.exceptions import ServiceInitializationError
from opensearchpy import OpenSearch, OpenSearchException
from config import BEDROCK_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpenSearchMemoryStore(MemoryStore):
    """Custom memory store implementation using OpenSearch.

    This class implements the MemoryStore interface to provide vector
    search capabilities using OpenSearch as the backend.
    """

    def __init__(self, endpoint: str):
        """Initialize OpenSearch memory store.

        Args:
            endpoint: OpenSearch endpoint URL

        Raises:
            OpenSearchException: If connection or index creation fails
        """
        try:
            self.client = OpenSearch(
                hosts=[endpoint],
                use_ssl=True
            )
            self.index = "semantic-kernel-memories"

            # Ensure index exists with proper mapping
            if not self.client.indices.exists(self.index):
                self.client.indices.create(
                    index=self.index,
                    body={
                        "mappings": {
                            "properties": {
                                "embedding": {"type": "dense_vector", "dims": 1536},
                                "text": {"type": "text"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                )
                logger.info(f"Created OpenSearch index: {self.index}")

        except OpenSearchException as e:
            logger.error(f"Failed to initialize OpenSearch: {str(e)}")
            raise

    async def upsert(self, collection: str, record: MemoryRecord) -> str:
        """Upsert a memory record.

        Args:
            collection: Collection name (used as namespace)
            record: Memory record to store

        Returns:
            str: Record ID

        Raises:
            OpenSearchException: If upsert operation fails
        """
        try:
            doc = {
                "id": record.id,
                "text": record.text,
                "embedding": record.embedding.tolist(),
                "metadata": record.metadata
            }
            self.client.index(
                index=self.index,
                body=doc,
                id=record.id,
                refresh=True
            )
            return record.id

        except Exception as e:
            logger.error(f"Failed to upsert record: {str(e)}")
            raise

    async def get(self, collection: str, key: str, with_embedding: bool = False) -> MemoryRecord:
        """Retrieve a memory record by key.

        Args:
            collection: Collection name
            key: Record ID
            with_embedding: Whether to include embeddings in the result

        Returns:
            MemoryRecord: Retrieved record

        Raises:
            OpenSearchException: If retrieval fails
        """
        try:
            result = self.client.get(index=self.index, id=key)
            return self._to_memory_record(result["_source"], with_embedding)
        except Exception as e:
            logger.error(f"Failed to get record {key}: {str(e)}")
            raise

    async def remove(self, collection: str, key: str) -> None:
        """Remove a memory record.

        Args:
            collection: Collection name
            key: Record ID to remove

        Raises:
            OpenSearchException: If deletion fails
        """
        try:
            self.client.delete(index=self.index, id=key)
        except Exception as e:
            logger.error(f"Failed to remove record {key}: {str(e)}")
            raise

    async def get_nearest_matches(
        self,
        collection: str,
        embedding: List[float],
        limit: int = 1,
        min_relevance_score: float = 0.7,
        with_embeddings: bool = False
    ) -> List[Tuple[MemoryRecord, float]]:
        """Find nearest matching records using cosine similarity.

        Args:
            collection: Collection name
            embedding: Query embedding vector
            limit: Maximum number of results
            min_relevance_score: Minimum similarity score threshold
            with_embeddings: Whether to include embeddings in results

        Returns:
            List[Tuple[MemoryRecord, float]]: List of records and their similarity scores

        Raises:
            OpenSearchException: If search operation fails
        """
        try:
            query = {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": embedding}
                    }
                }
            }

            results = self.client.search(
                index=self.index,
                body={"query": query, "size": limit}
            )

            matches = []
            for hit in results["hits"]["hits"]:
                score = (hit["_score"] - 1.0)  # Convert back to cosine similarity
                if score >= min_relevance_score:
                    record = self._to_memory_record(hit["_source"], with_embeddings)
                    matches.append((record, score))

            return matches

        except Exception as e:
            logger.error(f"Failed to perform nearest match search: {str(e)}")
            raise

    def _to_memory_record(self, doc: dict, with_embedding: bool = False) -> MemoryRecord:
        """Convert OpenSearch document to MemoryRecord.

        Args:
            doc: OpenSearch document
            with_embedding: Whether to include embeddings

        Returns:
            MemoryRecord: Converted record
        """
        return MemoryRecord(
            id=doc["id"],
            text=doc["text"],
            embedding=doc["embedding"] if with_embedding else None,
            metadata=doc.get("metadata", {})
        )

async def initialize_kernel() -> Optional[sk.Kernel]:
    """Initialize Semantic Kernel with AWS Bedrock services.

    Returns:
        sk.Kernel: Initialized kernel with Bedrock services
        None: If initialization fails
    """
    try:
        kernel = sk.Kernel()

        # Configure Bedrock services
        config = BedrockConfig(
            model_id=BEDROCK_SETTINGS["model_id"],
            region=BEDROCK_SETTINGS["region"]
        )
        embedding_config = BedrockConfig(
            model_id=BEDROCK_SETTINGS["embedding_model"],
            region=BEDROCK_SETTINGS["region"]
        )

        chat_service = BedrockChatCompletion(config)
        embedding_service = BedrockTextEmbedding(embedding_config)

        kernel.add_chat_service("bedrock", chat_service)
        kernel.add_text_embedding_generation_service("bedrock", embedding_service)

        logger.info(f"Initialized kernel with Bedrock models: {config.model_id}, {embedding_config.model_id}")
        return kernel

    except ServiceInitializationError as e:
        logger.error(f"Failed to initialize Bedrock services: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        return None

async def setup_memory(kernel: sk.Kernel) -> Optional[SemanticTextMemory]:
    """Set up semantic memory with OpenSearch.

    Args:
        kernel: Initialized Semantic Kernel instance

    Returns:
        SemanticTextMemory: Initialized memory instance
        None: If setup fails
    """
    try:
        memory_store = OpenSearchMemoryStore(BEDROCK_SETTINGS["opensearch_endpoint"])
        memory = SemanticTextMemory(
            storage=memory_store,
            embeddings_service=kernel.get_service("bedrock")
        )
        return memory

    except Exception as e:
        logger.error(f"Failed to setup memory: {str(e)}")
        return None

async def populate_memory(memory: SemanticTextMemory) -> bool:
    """Populate memory with sample documents.

    Args:
        memory: Initialized semantic memory instance

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        documents = [
            ("doc1", "Semantic Kernel is an SDK that integrates Large Language Models (LLMs) "
                    "with conventional programming languages. It combines natural language "
                    "semantic functions with traditional code functions, making AI orchestration "
                    "simple and efficient."),

            ("doc2", "RAG (Retrieval Augmented Generation) is a pattern that enhances LLM "
                    "responses by providing relevant context from a knowledge base. It first "
                    "retrieves relevant documents using semantic search, then uses these "
                    "documents to augment the prompt sent to the LLM."),

            ("doc3", "AWS Bedrock provides a unified API for accessing various foundation models. "
                    "It supports models like Claude from Anthropic and Titan from Amazon, "
                    "offering features such as text generation, embeddings, and image generation.")
        ]

        for doc_id, text in documents:
            await memory.save_information("docs", text, doc_id)
            logger.info(f"Saved document: {doc_id}")

        return True

    except Exception as e:
        logger.error(f"Failed to populate memory: {str(e)}")
        return False

async def process_queries(
    kernel: sk.Kernel,
    memory: SemanticTextMemory,
    queries: List[str]
):
    """Process queries using RAG pattern.

    Args:
        kernel: Initialized Semantic Kernel instance
        memory: Semantic memory instance
        queries: List of queries to process
    """
    for query in queries:
        print(f"\nUser Query: {query}")
        try:
            # Retrieve relevant memories
            memories = await memory.search("docs", query, limit=2)
            context = "\n".join(m.text for m in memories)

            # Create prompt with retrieved context
            prompt = f"""
            Use the following context to answer the question. Be specific and use information
            from the context. If you cannot answer based on the context, say so.

            Context:
            {context}

            Question: {query}
            """

            # Get completion from Bedrock
            result = await kernel.chat_completion.complete_chat(
                messages=[{"role": "user", "content": prompt}]
            )
            print(f"Assistant: {result}\n")

        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            print("Sorry, I couldn't process your query. Please try again.")

async def main():
    """Main entry point for the RAG example application."""
    try:
        # Initialize the kernel
        kernel = await initialize_kernel()
        if not kernel:
            logger.error("Failed to initialize the kernel. Exiting...")
            sys.exit(1)

        # Setup memory
        memory = await setup_memory(kernel)
        if not memory:
            logger.error("Failed to setup memory. Exiting...")
            sys.exit(1)

        # Populate memory with sample documents
        if not await populate_memory(memory):
            logger.error("Failed to populate memory. Exiting...")
            sys.exit(1)

        print("\nRunning RAG example with AWS Bedrock and OpenSearch...\n")

        # Example queries demonstrating different aspects
        queries = [
            "What are the key features of Semantic Kernel?",
            "How does RAG work with AWS Bedrock?",
            "What foundation models are available in Bedrock?",
            "How does Semantic Kernel handle AI orchestration?"
        ]

        await process_queries(kernel, memory, queries)

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())