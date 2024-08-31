---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:53:26Z
---

# Microsoft.SemanticKernel.Connectors.MongoDB

This connector uses [MongoDB Atlas Vector Search](ht*********************************************************ch) to implement Semantic Memory.

## Quick Start

1. Create [Atlas cluster](ht**********************************************ed/)
2. Create a [collection](ht***************************************************ns/)
3. Create [Vector Search Index](ht*************************************************************************ew/) for the collection. The index has to be defined on a field called `embedding`. For example:

```json {"id":"01J6KPS9K898EKX8242YK9Z46Z"}
{
  "type": "vectorSearch",
  "fields": [
    {
      "numDimensions": <number-of-dimensions>,
      "path": "embedding",
      "similarity": "euclidean | cosine | dotProduct",
      "type": "vector"
    }
  ]
}
```

4. Create the MongoDB memory store
   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KPS9K898EKX82432G8NQAE"}
var connectionString = "MONGODB ATLAS CONNECTION STRING"
MongoDBMemoryStore memoryStore = new(connectionString, "MyDatabase");

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("te******************02", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));
```

> Guide to find the connection string: ht***********************************************************ng/

## Important Notes

### Vector search indexes

In this version, vector search index management is outside of `MongoDBMemoryStore` scope.
Creation and maintenance of the indexes have to be done by the user. Please note that deleting a collection
(`memoryStore.DeleteCollectionAsync`) will delete the index as well.
