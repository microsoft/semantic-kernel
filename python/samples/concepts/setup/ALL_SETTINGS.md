## AI Service Settings used across SK:

| Service | Class | Constructor Settings | Environment Variable | Required? | Settings Class |
| --- | --- | --- | --- | --- | --- |
OpenAI | [OpenAIChatCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_chat_completion.py) |  |  |  | [OpenAISettings](../../../semantic_kernel/connectors/ai/open_ai/settings/open_ai_settings.py)
|  |  |  api_key | OPENAI_API_KEY | Yes
|  |  |  org_id | OPENAI_ORG_ID | No 
|  |  |  ai_model_id | OPENAI_CHAT_MODEL_ID | Yes 
|  | [OpenAITextCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_completion.py)
|  |  |  api_key | OPENAI_API_KEY | Yes
|  |  |  org_id | OPENAI_ORG_ID | No
|  |  |  ai_model_id | OPENAI_TEXT_MODEL_ID | Yes
|  | [OpenAITextEmbedding](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_embedding.py)
|  |  |  api_key | OPENAI_API_KEY | Yes
|  |  |  org_id | OPENAI_ORG_ID | No
|  |  |  ai_model_id | OPENAI_EMBEDDING_MODEL_ID | Yes
Azure OpenAI | [AzureOpenAIChatCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/azure_open_ai_chat_completion.py) |  |  |  | [AzureOpenAISettings](../../../semantic_kernel/connectors/ai/open_ai/settings/azure_open_ai_settings.py)
|  |  |  api_key | AZURE_OPENAI_API_KEY | Yes
|  |  |  endpoint | AZURE_OPENAI_ENDPOINT | Yes
|  |  |  ai_model_id | AZURE_OPENAI_CHAT_MODEL_ID | Yes
|  | [AzureOpenAITextCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/azure_open_ai_text_completion.py)
|  |  |  api_key | AZURE_OPENAI_API_KEY | Yes
|  |  |  endpoint | AZURE_OPENAI_ENDPOINT | Yes
|  |  |  ai_model_id | AZURE_OPENAI_TEXT_MODEL_ID | Yes
|  | [AzureOpenAITextEmbedding](../../../semantic_kernel/connectors/ai/open_ai/services/azure_open_ai_text_embedding.py)
|  |  |  api_key | AZURE_OPENAI_API_KEY | Yes
|  |  |  endpoint | AZURE_OPENAI_ENDPOINT | Yes
|  |  |  ai_model_id | AZURE_OPENAI_EMBEDDING_MODEL_ID | Yes

## Memory Service Settings used across SK:

| Service | Class | Constructor Settings | Environment Variable | Required? | Settings Class |
| --- | --- | --- | --- | --- | --- |
AstraDB | [AstraDBMemoryService](../../../semantic_kernel/connectors/memory/astradb/astradb_memory_store.py) |  |  |  | [AstraDBSettings](../../../semantic_kernel/connectors/memory/astradb/astradb_settings.py)
|  |  |  app_token | ASTRADB_APP_TOKEN | Yes
| | | db_id | ASTRADB_DB_ID | Yes
|  |  |  region | ASTRADB_REGION | Yes
|  |  |  keyspace | ASTRADB_KEYSPACE | Yes
Azure AI Search | [AzureAISearchMemoryService](../../../semantic_kernel/connectors/memory/azure_cognitive_search/azure_cognitive_search_memory_store.py) |  |  |  | [AzureAISearchSettings](../../../semantic_kernel/connectors/memory/azure_cognitive_search/azure_ai_search_settings.py)
|  |  |  api_key | AZURE_AI_SEARCH_API_KEY | No
|  |  |  endpoint | AZURE_AI_SEARCH_ENDPOINT | Yes
|  |  |  index_name | AZURE_AI_SEARCH_INDEX_NAME | No
Azure Cosmos DB | [AzureCosmosDBMemoryService](../../../semantic_kernel/connectors/memory/azure_cosmosdb/azure_cosmos_db_memory_store.py) |  |  |  | [AzureCosmosDBSettings](../../../semantic_kernel/connectors/memory/azure_cosmosdb/azure_cosmosdb_settings.py)
|  |  |  api | AZURE_COSMOS_DB_API | No
|  |  |  connection_string | AZURE_COSMOS_DB_CONNECTION_STRING or AZCOSMOS_CONNSTR | No
Mongo DB Atlas | [MongoDBAtlasMemoryService](../../../semantic_kernel/connectors/memory/mongodb_atlas/mongodb_atlas_memory_store.py) |  |  |  | [MongoDBAtlasSettings](../../../semantic_kernel/connectors/memory/mongodb_atlas/mongodb_atlas_settings.py)
|  |  |  connection_string | MONGODB_ATLAS_CONNECTION_STRING | Yes
|  |  |  database_name | MONGODB_ATLAS_DATABASE_NAME | No
|  |  |  index_name | MONGODB_ATLAS_INDEX_NAME | No
Pinecone | [PineconeMemoryService](../../../semantic_kernel/connectors/memory/pinecone/pinecone_memory_store.py) |  |  |  | [PineconeSettings](../../../semantic_kernel/connectors/memory/pinecone/pinecone_settings.py)
|  |  |  api_key | PINECONE_API_KEY | Yes
Postgres | [PostgresMemoryService](../../../semantic_kernel/connectors/memory/postgres/postgres_memory_store.py) |  |  |  | [PostgresSettings](../../../semantic_kernel/connectors/memory/postgres/postgres_settings.py)
|  |  |  connection_string | POSTGRES_CONNECTION_STRING | Yes
Redis | [RedisMemoryService](../../../semantic_kernel/connectors/memory/redis/redis_memory_store.py) |  |  |  | [RedisSettings](../../../semantic_kernel/connectors/memory/redis/redis_settings.py)
| | | connection_string | REDIS_CONNECTION_STRING | Yes
Weaviate | [WeaviateMemoryService](../../../semantic_kernel/connectors/memory/weaviate/weaviate_memory_store.py) |  |  |  | [WeaviateSettings](../../../semantic_kernel/connectors/memory/weaviate/weaviate_settings.py)
|  |  |  url | WEAVIATE_URL | No
|  |  |  api_key | WEAVIATE_API_KEY | No
| | | use_embed | WEAVIATE_USE_EMBED | No