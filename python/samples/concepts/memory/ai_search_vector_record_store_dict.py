# Copyright (c) Microsoft. All rights reserved.


import os
from uuid import uuid4

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
    fields={
        "id": VectorStoreRecordKeyField(),
        "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector"),
        "vector": VectorStoreRecordVectorField(local_embedding=False),
    }
)


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small"))
    async with AzureAISearchVectorRecordStore[dict](
        data_model_type=dict,
        data_model_definition=model_fields,
        collection_name=os.environ["ALT_SEARCH_INDEX_NAME"],
        search_endpoint=os.environ["ALT_SEARCH_ENDPOINT"],
        api_key=os.environ["ALT_SEARCH_API_KEY"],
        kernel=kernel,
    ) as record_store:
        record1 = {"id": str(uuid4()), "content": "my dict text", "vector": None}
        await kernel.add_embedding_to_object(
            [record1], "content", "vector", {"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)}
        )
        await record_store.upsert(record1)

        result = await record_store.get(record1["id"])
        print(f"vector: {result.pop('vector')[:10]}")
        print(f"result: {result}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
