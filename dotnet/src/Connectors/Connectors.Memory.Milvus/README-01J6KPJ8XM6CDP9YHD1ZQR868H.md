---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:53:39Z
---

# Microsoft.SemanticKernel.Connectors.Milvus

This is an implementation of the Semantic Kernel Memory Store abstraction for the [Milvus vector database](ht*************io).

**Note:** Currently, only Milvus v2.2 is supported. v2.3 is coming soon, older versions are untested.

## Quickstart using a standalone Milvus installation

1. Download the Milvus docker-compose.yml:

```bash {"id":"01J6KPSRQ5EYSZQ119T7WWFJFG"}
wget ht**********************************************************************************************ml -O docker-compose.yml
```

2. Start Milvus:

```bash {"id":"01J6KPSRQ5EYSZQ119TAM0AE9C"}
docker-compose up -d
```

3. Use Semantic Kernel with Milvus, connecting to `localhost` with the default (gRPC) port of 1536:
   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KPSRQ5EYSZQ119TAPGM556"}
using MilvusMemoryStore memoryStore = new("localhost");

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("te******************02", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));
```

More information on setting up Milvus can be found [here](ht******************************************************md). The `MilvusMemoryStore` constructor provides additional configuration options, such as the vector size, the similarity metric type, etc.
