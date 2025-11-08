# Copyright (c) Microsoft. All rights reserved.

"""Example demonstrating VoyageAI reranking with Semantic Kernel."""

import asyncio
import os

from semantic_kernel.connectors.ai.voyage_ai import VoyageAIReranker


async def main():
    """Run the VoyageAI reranker example."""
    # Get API key from environment
    api_key = os.getenv("VOYAGE_AI_API_KEY")
    if not api_key:
        raise ValueError("Please set the VOYAGE_AI_API_KEY environment variable")

    # Create reranker service
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key=api_key,
    )

    # Define query and documents
    query = "What are the key features of Semantic Kernel?"

    documents = [
        "Semantic Kernel is an open-source SDK that lets you easily build agents that can call your existing code.",
        "The capital of France is Paris, a beautiful city known for its art and culture.",
        "Python is a high-level, interpreted programming language with dynamic typing.",
        "Semantic Kernel provides enterprise-ready AI orchestration with model flexibility and plugin ecosystem.",
        "Machine learning models require large amounts of data for training.",
    ]

    print(f"Query: {query}\n")
    print("Documents to rerank:")
    for i, doc in enumerate(documents, 1):
        print(f"{i}. {doc}")

    # Rerank documents
    results = await reranker_service.rerank(query, documents)

    print("\nReranked results (sorted by relevance):")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.relevance_score:.4f}")
        print(f"   Original Index: {result.index}")
        print(f"   Text: {result.text}")


if __name__ == "__main__":
    asyncio.run(main())
