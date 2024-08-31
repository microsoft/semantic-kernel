---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:53:32Z
---

# semantic_kernel.connectors.memory.redis

This connector uses Redis to implement Semantic Memory. It requires the [RediSearch](ht*******************************************ry/) module to be enabled on Redis to implement vector similarity search.

See the [.net README](ht**********************************************************************************************************md) for more information.

## Quick start

1. Run with Docker:

```bash {"id":"01J6KPSHNENQ2W92GJKEZP7NQB"}
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

2. To use Redis as a semantic memory store:

```python {"id":"01J6KPSHNENQ2W92GJKHKXT5VW"}
    import semantic_kernel as sk
    import semantic_kernel.connectors.ai.open_ai as sk_oai
    from semantic_kernel.connectors.memory.redis import RedisMemoryStore

    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_service(sk_oai.OpenAITextCompletion(service_id="dv", ai*******id="te************03", api_key=api_key, org_id=org_id))
    embedding_generator = sk_oai.OpenAITextEmbedding(service_id="ada", ai*******id="te******************02", api_key=api_key, org_id=org_id)
    kernel.add_service(embedding_generator)

    redis_connection_string = sk.redis_settings_from_dot_env()
    kernel.use_memory(storage=RedisMemoryStore(connection_string=redis_connection_string), embeddings_generator=embedding_generator)
```
