# semantic_kernel.connectors.memory.redis

This connector uses Redis to implement Semantic Memory. It requires the [RediSearch](https://redis.io/docs/interact/search-and-query/) module to be enabled on Redis to implement vector similarity search. 

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
    kernel.add_text_completion_service("dv", sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id))
    kernel.add_text_embedding_generation_service("ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id))

    redis_connection_string = sk.redis_settings_from_dot_env()
    kernel.register_memory_store(memory_store=RedisMemoryStore(connection_string=redis_connection_string))
```

