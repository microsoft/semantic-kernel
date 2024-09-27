---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6M121KZGM9SEYRDY5S4XM4B
    updated: 2024-08-31 11:00:58Z
---

# Microsoft.SemanticKernel.Connectors.Kusto

This connector uses [Azure Data Explorer (Kusto)](ht*************************************************er/) to implement Semantic Memory.

## Quick Start

1. Create a cluster and database in Azure Data Explorer (Kusto) - see ht***************************************************************************************ee
2. To use Kusto as a semantic memory store, use the following code:

   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KPNSDA8KM2K36VWNEPCD6P"}
using Kusto.Data;

var connectionString = new KustoConnectionStringBuilder("ht***********************************et").WithAadUserPromptAuthentication();
KustoMemoryStore memoryStore = new(connectionString, "MyDatabase");

var embeddingGenerator = new OpenAITextEmbeddingGenerationService("te******************02", apiKey);

SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(textMemory));
```

## Important Notes

### Cosine Similarity

As of now, cosine similarity is not built-in to Kusto.
A function to calculate cosine similarity is automatically added to the Kusto database during first search operation.
This function (`series_cosine_similarity_fl`) is not removed automatically.
You might want to delete it manually if you stop using the Kusto database as a semantic memory store.
If you want to delete the function, you can do it manually using the Kusto explorer.
The function is called `series_cosine_similarity_fl` and is located in the `Functions` folder of the database.

### Append-Only Store

Kusto is an append-only store. This means that when a fact is updated, the old fact is not deleted.
This isn't a problem for the semantic memory connector, as it always utilizes the most recent fact.
This is made possible by using the [arg_max](ht*********************************************************************************on) aggregation function in conjunction with the [ingestion_time](ht***********************************************************************************on) function.  
However, users manually querying the underlying table should be aware of this behavior.

### Authentication

Please note that the authentication used in the example above is not recommended for production use. You can find more details here: ht************************************************************************************to
