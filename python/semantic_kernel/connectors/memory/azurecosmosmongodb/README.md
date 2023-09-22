# semantic_kernel.connectors.memory.azure_cosmosdb_mongodb

This connector uses Azure CosmosDB MongoDB Vector Store to implement Semantic Memory.

See the [official documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search) for more information.

## Quick start

1. Run with Docker:

```bash
docker run -p 27017:27017 -d --name=cosmosdb-emulator mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:mongodb
```

2. To use Azure CosmosDB MongoDB Vector Store as a semantic memory store:

```python
    import semantic_kernel as sk
    import semantic_kernel.connectors.ai.open_ai as sk_oai
    from semantic_kernel.connectors.memory.azurecosmosmongodb import AzureCosmosDbMongoDBMemoryStore

    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service("dv", sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id))
    kernel.add_text_embedding_generation_service("ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id))

    connection_string = sk.azure_cosmos_mongodb_settings_from_dot_env()
    kernel.register_memory_store(memory_store= AzureCosmosDBMongoDBMemoryStore(
        connection_string=connection_string,
        vector_size=536,
        database_name="test_db",
        embedding_key="Embedding",
    ))
```
