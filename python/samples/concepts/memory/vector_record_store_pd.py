# Copyright (c) Microsoft. All rights reserved.

import os
from uuid import uuid4

import pandas as pd

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.data.azure_ai_search.azure_ai_search_vector_record_store import (
    AzureAISearchVectorRecordStore,
)
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)

model_fields = VectorStoreRecordDefinition(
    container_mode=True,
    fields={
        "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector"),
        "id": VectorStoreRecordKeyField(),
        "vector": VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)}
        ),
    },
    to_dict=lambda x: x.to_dict(orient="records"),
    from_dict=lambda x: pd.DataFrame(x),
)


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small"))

    async with AzureAISearchVectorRecordStore[pd.DataFrame](
        data_model_type=pd.DataFrame,
        data_model_definition=model_fields,
        collection_name=os.environ["ALT_SEARCH_INDEX_NAME"],
        search_endpoint=os.environ["ALT_SEARCH_ENDPOINT"],
        api_key=os.environ["ALT_SEARCH_API_KEY"],
        kernel=kernel,
    ) as record_store:
        records = [
            {"id": str(uuid4()), "content": "my dict text", "vector": None},
            {"id": str(uuid4()), "content": "my second text", "vector": None},
        ]
        df = pd.DataFrame(records)
        await record_store.upsert_batch(df, generate_embeddings=True)

        result = await record_store.get(records[0]["id"])
        print(result.shape)
        print(result.head(5))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
