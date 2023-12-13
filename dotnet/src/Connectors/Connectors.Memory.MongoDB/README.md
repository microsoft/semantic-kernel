# Microsoft.SemanticKernel.Connectors.Memory.MongoDB

This connector uses [MongoDB Atlas Vector Search](https://www.mongodb.com/products/platform/atlas-vector-search) to implement Semantic Memory.

## Quick Start

1. Create [Atlas cluster](https://www.mongodb.com/docs/atlas/getting-started/)

2. Create a [collection](https://www.mongodb.com/docs/atlas/atlas-ui/collections/)

3. Create [Vector Search Index](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/) for the collection. The index has to be defined on a field called `embedding`. For example:

```
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

```csharp
var connectionString = "MONGODB ATLAS CONNECTION STRING"
MongoDBMemoryStore memoryStore = new(connectionString, "MyDatabase");

Kernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextGenerationService(modelId: TestConfiguration.OpenAI.ModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithOpenAITextEmbeddingGenerationService(modelId: TestConfiguration.OpenAI.EmbeddingModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithMemoryStorage(memoryStore)
    .Build();
```

> Guide to find the connection string: https://www.mongodb.com/docs/manual/reference/connection-string/

## Important Notes

### Vector search indexes

In this version, vector search index management is outside of `MongoDBMemoryStore` scope.
Creation and maintenance of the indexes have to be done by the user. Please note that deleting a collection
(`memoryStore.DeleteCollectionAsync`) will delete the index as well.
