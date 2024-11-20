## AI Service Settings used across SK:

| Provider | Service | Constructor Settings | Environment Variable | Required? | Settings Class |
| --- | --- | --- | --- | --- | --- |
| OpenAI | [OpenAIChatCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_chat_completion.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_CHAT_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No | [OpenAISettings](../../../semantic_kernel/connectors/ai/open_ai/settings/open_ai_settings.py) |
|  | [OpenAITextCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_completion.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_TEXT_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No |  |
|  | [OpenAITextEmbedding](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_embedding.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_EMBEDDING_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No |  |
|  | [OpenAITextToImage](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_to_image.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_TEXT_TO_IMAGE_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No |  |
|  | [OpenAITextToAudio](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_text_to_audio.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_TEXT_TO_AUDIO_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No |  |
|  | [OpenAIAudioToText](../../../semantic_kernel/connectors/ai/open_ai/services/open_ai_audio_to_text.py) | ai_model_id, <br> api_key, <br> org_id | OPENAI_AUDIO_TO_TEXT_MODEL_ID, <br> OPENAI_API_KEY, <br> OPENAI_ORG_ID | Yes, <br> Yes, <br> No |  |
| Azure OpenAI | [AzureChatCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/azure_chat_completion.py) | deployment_name, <br> api_key, <br> endpoint, <br> api_version, <br> base_url | AZURE_OPENAI_CHAT_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT, <br> AZURE_OPENAI_API_VERSION, <br> AZURE_OPENAI_BASE_URL | Yes, <br> No, <br> Yes, <br> Yes, <br> Yes | [AzureOpenAISettings](../../../semantic_kernel/connectors/ai/open_ai/settings/azure_open_ai_settings.py) |
|  | [AzureTextCompletion](../../../semantic_kernel/connectors/ai/open_ai/services/azure_text_completion.py) | deployment_name, <br> api_key, <br> endpoint, <br> api_version, <br> base_url | AZURE_OPENAI_TEXT_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT, <br> AZURE_OPENAI_API_VERSION, <br> AZURE_OPENAI_BASE_URL | Yes, <br> No, <br> Yes, <br> Yes, <br> Yes |  |
|  | [AzureTextEmbedding](../../../semantic_kernel/connectors/ai/open_ai/services/azure_text_embedding.py) | deployment_name, <br> api_key, <br> endpoint, <br> api_version, <br> base_url | AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT, <br> AZURE_OPENAI_API_VERSION, <br> AZURE_OPENAI_BASE_URL | Yes, <br> No, <br> Yes, <br> Yes, <br> Yes |  |
|  | [AzureTextToImage](../../../semantic_kernel/connectors/ai/open_ai/services/azure_text_to_image.py) | deployment_name, <br> api_key, <br> endpoint | AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT | Yes, <br> No, <br> Yes |  |
|  | [AzureTextToAudio](../../../semantic_kernel/connectors/ai/open_ai/services/azure_text_to_audio.py) | deployment_name, <br> api_key, <br> endpoint | AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT | Yes, <br> No, <br> Yes |  |
|  | [AzureAudioToText](../../../semantic_kernel/connectors/ai/open_ai/services/azure_audio_to_text.py) | deployment_name, <br> api_key, <br> endpoint | AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME, <br> AZURE_OPENAI_API_KEY, <br> AZURE_OPENAI_ENDPOINT | Yes, <br> No, <br> Yes |  |
| Azure AI Inference | [AzureAIInferenceChatCompletion](../../../semantic_kernel/connectors/ai/azure_ai_inference/services/azure_ai_inference_chat_completion.py) | ai_model_id, <br> api_key, <br> endpoint | N/A, <br> AZURE_AI_INFERENCE_API_KEY, <br> AZURE_AI_INFERENCE_ENDPOINT | Yes, <br> No, <br> Yes | [AzureAIInferenceSettings](../../../semantic_kernel/connectors/ai/azure_ai_inference/azure_ai_inference_settings.py) |
|  | [AzureAIInferenceTextEmbedding](../../../semantic_kernel/connectors/ai/azure_ai_inference/services/azure_ai_inference_text_embedding.py) | ai_model_id, <br> api_key, <br> endpoint | N/A, <br> AZURE_AI_INFERENCE_API_KEY, <br> AZURE_AI_INFERENCE_ENDPOINT | Yes, <br> No, <br> Yes |  |
| Anthropic | [AnthropicChatCompletion](../../../semantic_kernel/connectors/ai/anthropic/services/anthropic_chat_completion.py) | api_key, <br> ai_model_id | ANTHROPIC_API_KEY, <br> ANTHROPIC_CHAT_MODEL_ID | Yes, <br> Yes | [AnthropicSettings](../../../semantic_kernel/connectors/ai/anthropic/settings/anthropic_settings.py) |
| Bedrock | [BedrockChatCompletion](../../../semantic_kernel/connectors/ai/bedrock/services/bedrock_chat_completion.py) | model_id | BEDROCK_CHAT_MODEL_ID | Yes | [BedrockSettings](../../../semantic_kernel/connectors/ai/bedrock/bedrock_settings.py) |
|  | [BedrockTextCompletion](../../../semantic_kernel/connectors/ai/bedrock/services/bedrock_text_completion.py) | model_id | BEDROCK_TEXT_MODEL_ID | Yes |  |
|  | [BedrockTextEmbedding](../../../semantic_kernel/connectors/ai/bedrock/services/bedrock_text_embedding.py) | model_id | BEDROCK_EMBEDDING_MODEL_ID | Yes |  |
| Google AI | [GoogleAIChatCompletion](../../../semantic_kernel/connectors/ai/google/google_ai/services/google_ai_chat_completion.py) | gemini_model_id, <br> api_key | GOOGLE_AI_GEMINI_MODEL_ID, <br> GOOGLE_AI_API_KEY | Yes, <br> Yes | [GoogleAISettings](../../../semantic_kernel/connectors/ai/google/google_ai/google_ai_settings.py) |
|  | [GoogleAITextCompletion](../../../semantic_kernel/connectors/ai/google/google_ai/services/google_ai_text_completion.py) | gemini_model_id, <br> api_key | GOOGLE_AI_GEMINI_MODEL_ID, <br> GOOGLE_AI_API_KEY | Yes, <br> Yes |  |
|  | [GoogleAITextEmbedding](../../../semantic_kernel/connectors/ai/google/google_ai/services/google_ai_text_embedding.py) | embedding_model_id, <br> api_key | GOOGLE_AI_EMBEDDING_MODEL_ID, <br> GOOGLE_AI_API_KEY | Yes, <br> Yes |  |
| Vertex AI | [VertexAIChatCompletion](../../../semantic_kernel/connectors/ai/google/vertex_ai/services/vertex_ai_chat_completion.py) | project_id, <br> region, <br> gemini_model_id | VERTEX_AI_PROJECT_ID, <br> VERTEX_AI_REGION, <br> VERTEX_AI_GEMINI_MODEL_ID | Yes, <br> No, <br> Yes | [VertexAISettings](../../../semantic_kernel/connectors/ai/google/vertex_ai/vertex_ai_settings.py) |
|  | [VertexAITextCompletion](../../../semantic_kernel/connectors/ai/google/google_ai/services/google_ai_text_completion.py) | project_id, <br> region, <br> gemini_model_id | VERTEX_AI_PROJECT_ID, <br> VERTEX_AI_REGION, <br> VERTEX_AI_GEMINI_MODEL_ID | Yes, <br> No, <br> Yes |  |
|  | [VertexAITextEmbedding](../../../semantic_kernel/connectors/ai/google/google_ai/services/google_ai_text_embedding.py) | project_id, <br> region, <br> embedding_model_id | VERTEX_AI_PROJECT_ID, <br> VERTEX_AI_REGION, <br> VERTEX_AI_EMBEDDING_MODEL_ID | Yes, <br> No, <br> Yes |  |
| HuggingFace | [HuggingFaceTextCompletion](../../../semantic_kernel/connectors/ai/hugging_face/services/hf_text_completion.py) | ai_model_id | N/A | Yes | |
|  | [HuggingFaceTextEmbedding](../../../semantic_kernel/connectors/ai/hugging_face/services/hf_text_embedding.py) | ai_model_id | N/A | Yes | |
| Mistral AI | [MistralAIChatCompletion](../../../semantic_kernel/connectors/ai/mistral_ai/services/mistral_ai_chat_completion.py) | ai_model_id, <br> api_key | MISTRALAI_CHAT_MODEL_ID, <br> MISTRALAI_API_KEY | Yes, <br> Yes | [MistralAISettings](../../../semantic_kernel/connectors/ai/mistral_ai/settings/mistral_ai_settings.py) |
|  | [MistralAITextEmbedding](../../../semantic_kernel/connectors/ai/mistral_ai/services/mistral_ai_text_embedding.py) | ai_model_id, <br> api_key | MISTRALAI_EMBEDDING_MODEL_ID, <br> MISTRALAI_API_KEY | Yes, <br> Yes |  |
| Ollama | [OllamaChatCompletion](../../../semantic_kernel/connectors/ai/ollama/services/ollama_chat_completion.py) | ai_model_id, <br> host | OLLAMA_CHAT_MODEL_ID, <br> OLLAMA_HOST | Yes, <br> No | [OllamaSettings](../../../semantic_kernel/connectors/ai/ollama/ollama_settings.py) |
|  | [OllamaTextCompletion](../../../semantic_kernel/connectors/ai/ollama/services/ollama_text_completion.py) | ai_model_id, <br> host | OLLAMA_TEXT_MODEL_ID, <br> OLLAMA_HOST | Yes, <br> No |  |
|  | [OllamaTextEmbedding](../../../semantic_kernel/connectors/ai/ollama/services/ollama_text_embedding.py) | ai_model_id, <br> host | OLLAMA_EMBEDDING_MODEL_ID, <br> OLLAMA_HOST | Yes, <br> No |  |
| Onnx | [OnnxGenAIChatCompletion](../../../semantic_kernel/connectors/ai/onnx/services/onnx_gen_ai_chat_completion.py) | template, <br> ai_model_path | N/A, <br> ONNX_GEN_AI_CHAT_MODEL_FOLDER | Yes, <br> Yes | [OnnxGenAISettings](../../../semantic_kernel/connectors/ai/onnx/onnx_gen_ai_settings.py) |
|  | [OnnxGenAITextCompletion](../../../semantic_kernel/connectors/ai/onnx/services/onnx_gen_ai_text_completion.py) | ai_model_path | ONNX_GEN_AI_TEXT_MODEL_FOLDER | Yes |  |

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

## Other settings used:

| Service | Class | Constructor Settings | Environment Variable | Required? | Settings Class |
| --- | --- | --- | --- | --- | --- |
Bing | [BingSearch](../../../semantic_kernel/connectors/search_engine/bing_connector.py) |  |  |  | [BingSettings](../../../semantic_kernel/connectors/search_engine/bing_connector_settings.py)
| | | api_key | BING_API_KEY | No
| | | custom_config | BING_CUSTOM_CONFIG | No
Azure Container Apps Sessions | [ACASessionsPlugin](../../../semantic_kernel/core_plugins/sessions_python_tool/sessions_python_plugin.py) |  |  |  | [ACASessionsSettings](../../../semantic_kernel/core_plugins/sessions_python_tool/sessions_python_settings.py)
| | | pool_management_endpoint | ACA_POOL_MANAGEMENT_ENDPOINT | Yes
