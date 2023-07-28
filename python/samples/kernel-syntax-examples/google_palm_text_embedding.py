# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion, OpenAITextEmbedding



async def embedding_example() -> None:
    kernel = sk.Kernel()
    
    api_key = sk.google_palm_settings_from_dot_env()
    palm_chat_completion = sk_gp.GooglePalmTextEmbedding(
            "models/embedding-gecko-001", api_key
    )
    kernel.add_text_embedding_generation_service("gecko", palm_chat_completion)

    embedding = await palm_chat_completion.generate_embeddings_async(["Hello world", "Example text"])
    print(embedding)
    """
    api_key, org_id = sk.openai_settings_from_dot_env()
    embed = OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id)
    kernel.add_text_embedding_generation_service("ada", embed)
    embedding = await embed.generate_embeddings_async(["Hello world", "Example text"])
    print(embedding)
    """


async def main() -> None:
    await embedding_example()
    


if __name__ == "__main__":
    asyncio.run(main())
