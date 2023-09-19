# Microsoft.SemanticKernel.Connectors.Memory.MongoDB

This connector uses [MongoDB Atlas Vector Search](https://www.mongodb.com/products/platform/atlas-vector-search) to implement Semantic Memory.

## Quick Start

1. Create [Atlas cluster](https://www.mongodb.com/docs/atlas/getting-started/)

2. Create a collection

3. Create [Vector Search Index](https://www.mongodb.com/docs/atlas/atlas-search/field-types/knn-vector/) for the collection.
The index has to be defined on a field called ```embedding```. For example:
```
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimension": 1024,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

4. Create the MongoDB memory store
```csharp
var connectionString = "MONGODB ATLAS CONNECTION STRING"
MongoDBMemoryStore memoryStore = new(connectionString, "MyDatabase");

IKernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextCompletionService(modelId: TestConfiguration.OpenAI.ModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithOpenAITextEmbeddingGenerationService(modelId: TestConfiguration.OpenAI.EmbeddingModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithMemoryStorage(memoryStore)
    .Build();
```

## Important Notes

### Vector search indexes
In this version, vector search index management is outside of ```MongoDBMemoryStore``` scope.
Creation and maintenance of the indexes have to be done by the user. Please note that deleting a collection
(```memoryStore.DeleteCollectionAsync```) will delete the index as well.
