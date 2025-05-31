# Connectors.Memory.SqlServer

This connector uses the SQL Server database engine to implement [Vector Store](https://learn.microsoft.com/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-csharp) capability in Semantic Kernel. 

> [!IMPORTANT]  
> The features needed to use this connector are available in preview in Azure SQL only at the moment. Please take a look at the [Public Preview of Native Vector Support in Azure SQL Database](https://devblogs.microsoft.com/azure-sql/exciting-announcement-public-preview-of-native-vector-support-in-azure-sql-database/) for more information.

Here's an example of how to use the SQL Server Vector Store connector in your Semantic Kernel application:

```csharp
/*
    Vector store schema    
*/
public sealed class BlogPost
{
    [VectorStoreRecordKey]
    public int Id { get; set; }

    [VectorStoreRecordData]
    public string? Title { get; set; }

    [VectorStoreRecordData]
    public string? Url { get; set; }

    [VectorStoreRecordData]
    public string? Content { get; set; }

    [VectorStoreRecordVector(Dimensions: 1536)]
    public ReadOnlyMemory<float> ContentEmbedding { get; set; }
}

/*
 * Build the kernel and configure the embedding provider
 */
var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAITextEmbeddingGeneration(AZURE_OPENAI_EMBEDDING_MODEL, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY);
var kernel = builder.Build();

/*
 * Define vector store
 */
var vectorStore = new SqlServerVectorStore(AZURE_SQL_CONNECTION_STRING);

/*
 * Get a collection instance using vector store
 */
var collection = vectorStore.GetCollection<int, BlogPost>("SemanticKernel_VectorStore_BlogPosts");
await collection.CreateCollectionIfNotExistsAsync();

/*
 * Get blog posts to vectorize
 */
var blogPosts = await GetBlogPosts('https://devblogs.microsoft.com/azure-sql/');

/*
 * Generate embeddings for each glossary item
 */
var tasks = blogPosts.Select(b => Task.Run(async () =>
{    
    b.ContentEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(b.Content);
}));
await Task.WhenAll(tasks);

/*
 * Upsert the data into the vector store
 */
await collection.UpsertBatchAsync(blogPosts);

/*
 * Query the vector store
 */
var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync("How to use vector search in Azure SQL");
var searchResult = await collection.VectorizedSearchAsync(searchVector);
```

You can get a fully working sample using this connector in the following repository:

- [Vector Store sample](https://github.com/Azure-Samples/azure-sql-db-vector-search/tree/main/SemanticKernel/dotnet)


