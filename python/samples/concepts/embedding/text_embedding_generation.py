# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.text_embedding_services import Services, get_text_embedding_service_and_request_settings

"""
This sample shows how to generating embeddings for text data. This sample uses the following component:
- an text embedding generator: This component is responsible for generating embeddings for text data.
"""

# You can select from the following text embedding services:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.HUGGING_FACE
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.VERTEX_AI
# Please make sure you have configured your environment correctly for the selected text embedding service.
text_embedding_service, request_settings = get_text_embedding_service_and_request_settings(Services.OPENAI)

TEXTS = [
    "A dog ran joyfully through the green field, chasing after butterflies in the warm afternoon sun.",
    "A happy puppy sprinted across the grassy meadow, playfully pursuing insects under the bright sky.",
]


def cosine_similarity(a, b):
    from scipy.spatial.distance import cosine

    # Note that scipy.spatial.distance.cosine computes the cosine distance, which is 1 - cosine similarity.
    # https://en.wikipedia.org/wiki/Cosine_similarity#Cosine_distance
    return 1 - cosine(a, b)


async def main() -> None:
    # 1. Generate embeddings in batches.
    embeddings = await text_embedding_service.generate_embeddings(TEXTS, request_settings)
    print(embeddings)

    # 2. Generate embeddings for a single text. Since the two texts are similar in meaning,
    # the cosine similarity between the two embeddings should be high.
    embedding_a = await text_embedding_service.generate_embeddings([TEXTS[0]], request_settings)
    embedding_b = await text_embedding_service.generate_embeddings([TEXTS[1]], request_settings)
    print(f"Similarity between the two texts: {cosine_similarity(embedding_a[0], embedding_b[0])}")

    """
    Sample output:
    [[ 0.02221295 -0.00633203  0.00067574 ... -0.00513578 -0.0314321
      -0.02128683]
    [-0.00864875  0.02254905 -0.00182191 ...  0.01043635 -0.00777349
      -0.02256389]]
    Similarity between the two texts: 0.7263079790609065
    """


if __name__ == "__main__":
    asyncio.run(main())
