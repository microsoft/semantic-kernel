# Copyright (c) Microsoft. All rights reserved.

"""Example demonstrating VoyageAI text embeddings with Semantic Kernel."""

import asyncio
import os

from semantic_kernel.connectors.ai.voyage_ai import VoyageAITextEmbedding


async def main():
    """Run the VoyageAI text embedding example."""
    # Get API key from environment
    api_key = os.getenv("VOYAGE_AI_API_KEY")
    if not api_key:
        raise ValueError("Please set the VOYAGE_AI_API_KEY environment variable")

    # Create embedding service
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key=api_key,
    )

    # Generate embeddings
    texts = [
        "Semantic Kernel is an SDK for integrating AI models",
        "VoyageAI provides high-quality embeddings",
        "Python is a popular programming language",
    ]

    print("Generating embeddings for:")
    for i, text in enumerate(texts, 1):
        print(f"{i}. {text}")

    embeddings = await embedding_service.generate_embeddings(texts)

    print(f"\nGenerated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First embedding (first 5 values): {embeddings[0][:5]}")


if __name__ == "__main__":
    asyncio.run(main())
