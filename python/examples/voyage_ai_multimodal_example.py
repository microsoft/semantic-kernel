# Copyright (c) Microsoft. All rights reserved.

"""Example demonstrating VoyageAI multimodal embeddings with Semantic Kernel."""

import asyncio
import os

from semantic_kernel.connectors.ai.voyage_ai import VoyageAIMultimodalEmbedding


async def main():
    """Run the VoyageAI multimodal embedding example."""
    # Get API key from environment
    api_key = os.getenv("VOYAGE_AI_API_KEY")
    if not api_key:
        raise ValueError("Please set the VOYAGE_AI_API_KEY environment variable")

    # Create multimodal embedding service
    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key=api_key,
    )

    # Example 1: Text-only embeddings
    print("Example 1: Text-only embeddings")
    texts = [
        "A photo of a cat sitting on a windowsill",
        "A diagram showing the architecture of a neural network",
    ]

    embeddings = await embedding_service.generate_embeddings(texts)
    print(f"Generated {len(embeddings)} text embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}\n")

    # Example 2: Mixed text and images (requires PIL)
    print("Example 2: Mixed text and images")
    print("To use images, uncomment the following code and provide image paths:\n")

    example_code = """
    from PIL import Image

    # Load images
    image1 = Image.open("path/to/image1.jpg")
    image2 = Image.open("path/to/image2.png")

    # Create mixed inputs
    inputs = [
        "This is a text description",
        image1,
        ["Text before image", image2, "Text after image"],
    ]

    # Generate multimodal embeddings
    embeddings = await embedding_service.generate_multimodal_embeddings(inputs)
    print(f"Generated {len(embeddings)} multimodal embeddings")
    """

    print(example_code)


if __name__ == "__main__":
    asyncio.run(main())
