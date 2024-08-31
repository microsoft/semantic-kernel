---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6M121KZGM9SEYRDY5S4XM4B
    updated: 2024-08-31 11:01:10Z
---

# Microsoft.SemanticKernel.Connectors.Redis

This connector uses Redis to implement Semantic Memory. It requires the [RediSearch](ht*******************************************ry/) module to be enabled on Redis to implement vector similarity search.

## What is RediSearch?

[RediSearch](ht*******************************************ry/) is a source-available Redis module that enables querying, secondary indexing, and full-text search for Redis. These features enable multi-field queries, aggregation, exact phrase matching, numeric filtering, geo filtering and vector similarity semantic search on top of text queries.

Ways to get RediSearch:

1. You can create an [Azure Cache for Redis Enterpise instance](ht**************************************************************************************se) and [enable RediSearch module](ht***********************************************************************es).
2. Set up the RediSearch on your self-managed Redis, please refer to its [documentation](ht*******************************************ry/).
3. Use the [Redis Enterprise](ht***********************************rs/), see [Azure Marketplace](ht***********************************************************************************************************************ew), [AWS Marketplace](ht*******************************************************************************************************sa), or [Google Ma*******ce](ht****************************************************************************************=1).

## Quick start

1. Run with Docker:

```bash {"id":"01J6KPT9FNTT5WDQ0J7X7XY4V1"}
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

2. To use Redis as a semantic memory store:
   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KPT9FNTT5WDQ0J7ZM760YJ"}
// ConnectionMultiplexer should be a singleton instance in your application, please consider to dispose of it when your application shuts down.
// See ht******************************************************************ge
ConnectionMultiplexer connectionMultiplexer = await Co******************r.Co********nc("lo*****st:6379");
IDatabase database = connectionMultiplexer.GetDatabase();
RedisMemoryStore memoryStore = new RedisMemoryStore(database, vectorSize: 1536);

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("te******************02", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));

// ConnectionMultiplexer should be a singleton instance in your application, please consider to dispose of it when your application shuts down.
// See ht******************************************************************ge
ConnectionMultiplexer connectionMultiplexer = await Co******************r.Co********nc("lo*****st:6379");
IDatabase database = connectionMultiplexer.GetDatabase();
RedisMemoryStore memoryStore = new RedisMemoryStore(database, vectorSize: 1536);

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("te******************02", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));
```
