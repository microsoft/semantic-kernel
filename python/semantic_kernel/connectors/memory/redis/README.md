# semantic_kernel.connectors.memory.redis

This connector uses Redis to implement Semantic Memory. It requires the [RediSearch](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/) module to be enabled on Redis to implement vector similarity search.

See the [.net README](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.Memory.Redis/README.md) for more information.

## Quick start

1. Run with Docker:

```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

2. To use Redis as a semantic memory store:

```python
    import semantic_kernel as sk
    import semantic_kernel.connectors.ai.open_ai as sk_oai
    from semantic_kernel.connectors.memory.redis import RedisMemoryStore

    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_service(sk_oai.OpenAITextCompletion(service_id="dv", ai_model_id="text-davinci-003", api_key=api_key, org_id=org_id))
    embedding_generator = sk_oai.OpenAITextEmbedding(service_id="ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id)
    kernel.add_service(embedding_generator)

    redis_connection_string = sk.redis_settings_from_dot_env()
    kernel.use_memory(storage=RedisMemoryStore(connection_string=redis_connection_string), embeddings_generator=embedding_generator)
```
