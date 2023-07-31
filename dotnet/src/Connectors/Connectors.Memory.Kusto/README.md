# Microsoft.SemanticKernel.Connectors.Memory.Kuato

This connector uses Kusto (Azure Data Explorer)[https://learn.microsoft.com/en-us/azure/data-explorer/] to implement Semantic Memory.

## Quick start

1. Create a cluster and database in Kusto (Azure Data Explorer) - see https://learn.microsoft.com/en-us/azure/data-explorer/create-cluster-and-database?tabs=free

2. To use Kusto as a semantic memory store:

```csharp
var connectionString = new KustoConnectionStringBuilder("https://mycluster.kusto.windows.net").WithAadUserPromptAuthentication();
KustoMemoryStore memoryStore = new(connectionString, "MyDatabase");

IKernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextCompletionService(modelId: TestConfiguration.OpenAI.ModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithOpenAITextEmbeddingGenerationService(modelId: TestConfiguration.OpenAI.EmbeddingModelId,apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithMemoryStorage(memoryStore)
    .Build();
```

## Important notes

### Coisine similarity
At this time, coisine similiarity is not baked in into Kusto. It is add to the database hosting the collections when the first collection is created.  
This is done by creating a function in the database. 
This function is not deleted when the last collection is deleted. This is done to avoid the cost of creating the function each time a collection is created. 
If you want to delete the function, you can do it manually using the Kusto explorer. The function is called `series_cosine_similarity_fl` and is located in the `Functions` folder of the database.

### Append Only Store
Kusto is an append only store. This means that when a fact is updated, the old fact is not deleted.
This is not a problem for the semantic memory connector as it will always use the latest fact. 
This is achieved by using the (arg_max)[https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/arg-max-aggfunction] aggregation function together with the (ingestion_time)[https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/ingestiontimefunction] function.
It should have little implications, however, in case the user will query the underlying table manually, they should be aware of this behavior.  
