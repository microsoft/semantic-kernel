# Microsoft.SemanticKernel.Connectors.Memory.Kusto

This connector uses (Azure Data Explorer (Kusto))[https://learn.microsoft.com/en-us/azure/data-explorer/] to implement Semantic Memory.

## Quick Start

1. Create a cluster and database in Azure Data Explorer (Kusto) - see https://learn.microsoft.com/en-us/azure/data-explorer/create-cluster-and-database?tabs=free

2. To use Kusto as a semantic memory store, use the following code:

```csharp
using Kusto.Data;

var connectionString = new KustoConnectionStringBuilder("https://kvc123.eastus.kusto.windows.net").WithAadUserPromptAuthentication();
KustoMemoryStore memoryStore = new(connectionString, "MyDatabase");

IKernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextCompletionService(modelId: TestConfiguration.OpenAI.ModelId, apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithOpenAITextEmbeddingGenerationService(modelId: TestConfiguration.OpenAI.EmbeddingModelId,apiKey: TestConfiguration.OpenAI.ApiKey)
    .WithMemoryStorage(memoryStore)
    .Build();
```

## Important Notes

### Cosine Similarity
As of now, cosine similiarity is not built-in to Kusto. 
A function to calculate cosine similarity is automatically added to the Kusto database when the first collection is created. 
This function (`series_cosine_similarity_fl`) is not removed. 
You might want to delete it manually if you stop using the Kusto database as a semantic memory store. 
If you want to delete the function, you can do it manually using the Kusto explorer. 
The function is called `series_cosine_similarity_fl` and is located in the `Functions` folder of the database. 

### Append-Only Store
Kusto is an append-only store. This means that when a fact is updated, the old fact is not deleted. 
This isn't a problem for the semantic memory connector, as it always utilizes the most recent fact. 
This is made possible by using the (arg_max)[https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/arg-max-aggfunction] aggregation function in conjunction with the (ingestion_time)[https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/ingestiontimefunction] function.  
However, users manually querying the underlying table should be aware of this behavior.

### Authentication
Please note that the authentication used in the example above is not recommended for production use. You can find more details here: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/api/connection-strings/kusto
