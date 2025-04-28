# Microsoft.SemanticKernel.Connectors.SqlServer

This connector uses the SQL Server database engine to implement Semantic Kernel [vector store](https://learn.microsoft.com/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-csharp).

> [!IMPORTANT]  
> The features needed to use this connector are available in preview in Azure SQL only at the moment. Please take a look at the [Announcing EAP for Vector Support in Azure SQL Database](https://devblogs.microsoft.com/azure-sql/announcing-eap-native-vector-support-in-azure-sql-database/) for more information on how to enable the feature.

## Quick start

Create a new .NET console application:

```bash
dotnet new console --framework net9.0 -n MyVectorStoreApp
```

Add the Semantic Kernel packages needed to create a Chatbot:

```bash
dotnet add package Microsoft.SemanticKernel
dotnet add package Microsoft.Extensions.VectorData.Abstractions --prerelease
```

Add `Microsoft.SemanticKernel.Connectors.SqlServer` to use SQL Server or Azure SQL to store vectors:

```bash
dotnet add package Microsoft.SemanticKernel.Connectors.SqlServer --prerelease
```

Then you can use the following code to create a Chatbot with a memory that uses SQL Server:

```csharp
using System.Text.Json;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Kernel = Microsoft.SemanticKernel.Kernel;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Microsoft.SemanticKernel.Embeddings;

#pragma warning disable SKEXP0001, SKEXP0010, SKEXP0020

// Replace with your Azure OpenAI endpoint
const string azureOpenAIEndpoint = "https://.openai.azure.com/";

// Replace with your Azure OpenAI API key
const string azureOpenAIApiKey = "";

// Replace with your Azure OpenAI embedding deployment name
const string embeddingModelDeploymentName = "text-embedding-3-small";

// Complete with your Azure SQL connection string
const string connectionString = "Data Source=.database.windows.net;Initial Catalog=;Authentication=Active Directory Default;Connection Timeout=30";

// Table where memories will be stored
const string tableName = "skglossary";

// Sample Data
var glossaryEntries = new List<Glossary>()
{
    new()
    {
        Key = 1,
        Term = "API",
        Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
    },
    new()
    {
        Key = 2,
        Term = "Connectors",
        Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
    },
    new()
    {
        Key = 3,
        Term = "RAG",
        Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user's question (prompt)."
    }
};

/*
 * Set up Semantic Kernel
 */

// Build the kernel and configure the embedding provider
var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAITextEmbeddingGeneration(embeddingModelDeploymentName, azureOpenAIEndpoint, azureOpenAIApiKey);
var kernel = builder.Build();

// Define vector store
var vectorStore = new SqlServerVectorStore(connectionString);

// Get a collection instance using vector store
// IMPORTANT: Make sure the use the same data type for key here and for the VectorStoreRecordKey element
var collection = vectorStore.GetCollection<int, Glossary>(tableName);
await collection.CreateCollectionIfNotExistsAsync();

// Get embedding service
var textEmbeddingGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

/*
 * Generate embeddings for each glossary item
 */
Console.WriteLine("Generating embeddings...");

var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
{
    entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
}));

await Task.WhenAll(tasks);

/*
 * Upsert the data into the vector store
 */
Console.WriteLine("Upserting data into vector store...");

await foreach (var key in collection.UpsertBatchAsync(glossaryEntries))
{
    Console.WriteLine(key);
}

/*
 * Upsert the data into the vector store
 */
Console.WriteLine("Return the inserted data...");

var options = new GetRecordOptions() { IncludeVectors = false };

await foreach (var record in collection.GetBatchAsync(keys: [1, 2, 3], options))
{
    Console.WriteLine($"Key: {record.Key}");
    Console.WriteLine($"Term: {record.Term}");
    Console.WriteLine($"Definition: {record.Definition}");
    Console.WriteLine($"Definition Embedding: {JsonSerializer.Serialize(record.DefinitionEmbedding)}");
}

/*
 * Upsert the data into the vector store
 */
Console.WriteLine("Run vector search...");

var searchString = "I want to learn more about Connectors";
var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);

var searchResult = await collection.VectorizedSearchAsync(searchVector);

await foreach (var result in searchResult.Results)
{
    Console.WriteLine($"Search score: {result.Score}");
    Console.WriteLine($"Key: {result.Record.Key}");
    Console.WriteLine($"Term: {result.Record.Term}");
    Console.WriteLine($"Definition: {result.Record.Definition}");
    Console.WriteLine("=========");
}

public sealed class Glossary
{
    [VectorStoreRecordKey]
    public int Key { get; set; }

    [VectorStoreRecordData]
    public string? Term { get; set; }

    [VectorStoreRecordData]
    public string? Definition { get; set; }

    [VectorStoreRecordVector(Dimensions: 1536)]
    public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
}
```
