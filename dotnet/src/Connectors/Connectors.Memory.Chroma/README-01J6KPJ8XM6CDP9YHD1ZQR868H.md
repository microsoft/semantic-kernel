---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:51:58Z
---

# Microsoft.SemanticKernel.Connectors.Chroma

This assembly contains implementation of Semantic Kernel Memory Store using [Chroma](ht**********************om/), open-source embedding database.

**Note:** Chroma connector is verified using Chroma version **0.4.10**. Any higher versions may introduce incompatibility.

## Quickstart using local Chroma server

1. Clone Chroma:

```bash {"id":"01J6KPPMQEJFRBZ02BHD12JZMZ"}
git clone ht*************************************it
cd chroma
```

2. Run local Chroma server with Docker within Chroma repository root:

```bash {"id":"01J6KPPMQEJFRBZ02BHFH091E5"}
docker-compose up -d --build
```

3. Use Semantic Kernel with Chroma, using server local endpoint `ht*****************00`:

   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KPPMQEJFRBZ02BHGEW2J8E"}
const string endpoint = "ht*****************00";

var memoryWithChroma = new MemoryBuilder()
    .WithChromaMemoryStore(endpoint)
    .WithLoggerFactory(loggerFactory)
    .WithOpenAITextEmbeddingGeneration("te******************02", apiKey)
    .Build();

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(memoryWithChroma));
```
