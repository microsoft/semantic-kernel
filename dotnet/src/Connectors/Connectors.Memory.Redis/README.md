﻿# Microsoft.SemanticKernel.Connectors.Redis

This connector uses Redis to implement Semantic Memory. It requires the [RediSearch](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/) module to be enabled on Redis to implement vector similarity search.

## What is RediSearch?

[RediSearch](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/) is a source-available Redis module that enables querying, secondary indexing, and full-text search for Redis. These features enable multi-field queries, aggregation, exact phrase matching, numeric filtering, geo filtering and vector similarity semantic search on top of text queries.

Ways to get RediSearch:

1. You can create an [Azure Cache for Redis Enterpise instance](https://learn.microsoft.com/azure/azure-cache-for-redis/quickstart-create-redis-enterprise) and [enable RediSearch module](https://learn.microsoft.com/azure/azure-cache-for-redis/cache-redis-modules).

1. Set up the RediSearch on your self-managed Redis, please refer to its [documentation](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/).

1. Use the [Redis Enterprise](https://redis.io/docs/latest/operate/rs/), see [Azure Marketplace](https://azuremarketplace.microsoft.com/en-us/marketplace/apps/garantiadata.redis_enterprise_1sp_public_preview?tab=Overview), [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-e6y7ork67pjwg?sr=0-2&ref_=beagle&applicationId=AWSMPContessa), or [Google Marketplace](https://console.cloud.google.com/marketplace/details/redislabs-public/redis-enterprise?pli=1).

## Quick start

1. Run with Docker:

```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

2. To use Redis as a semantic memory store:
   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp
// ConnectionMultiplexer should be a singleton instance in your application, please consider to dispose of it when your application shuts down.
// See https://stackexchange.github.io/StackExchange.Redis/Basics#basic-usage
ConnectionMultiplexer connectionMultiplexer = await ConnectionMultiplexer.ConnectAsync("localhost:6379");
IDatabase database = connectionMultiplexer.GetDatabase();
RedisMemoryStore memoryStore = new RedisMemoryStore(database, vectorSize: 1536);

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("text-embedding-ada-002", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));
```
